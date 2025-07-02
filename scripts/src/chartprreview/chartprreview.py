import argparse
import hashlib
import os
import os.path
import re
import subprocess
import sys

import requests
import semantic_version
import semver
import yaml
from environs import Env

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

sys.path.append("../")
from pullrequest import prartifact
from reporegex import matchers
from report import report_info, verifier_report
from signedchart import signedchart
from tools import gitutils


def write_error_log(directory, *msg):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, "errors"), "w") as fd:
        for line in msg:
            print(line)
            fd.write(line)
            fd.write("\n")


def get_vendor_type(directory):
    vendor_type = os.environ.get("VENDOR_TYPE")
    if not vendor_type or vendor_type not in {"partner", "redhat", "community"}:
        msg = "[ERROR] Chart files need to be under one of charts/partners, charts/redhat, or charts/community"
        write_error_log(directory, msg)
        sys.exit(1)
    return vendor_type


def get_modified_charts(directory, api_url):
    """Get the category, organization, chart name, and new version corresponding to
    the chart being added.

    Args:
        directory (str): Local directory in which to write the error logs
        api_url (str): URL of the GitHub PR

    Returns:
        (str, str, str, str): category, organization, chart, and version (e.g. partner,
                              hashicorp, vault, 1.4.0)
    """
    print("[INFO] Get modified charts. %s" % directory)
    files = prartifact.get_modified_files(api_url)
    pattern = re.compile(
        matchers.submission_path_matcher(strict_categories=False) + r"/.*"
    )
    for file_path in files:
        m = pattern.match(file_path)
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version

    msg = "[ERROR] One or more files included in the pull request are not part of the chart"
    write_error_log(directory, msg)
    sys.exit(1)


def verify_user(directory, username, category, organization, chart):
    """Check that the user that submitted the PR is in the OWNERS file for this chart.

    Args:
        directory (str): Local directory in which to write the error logs
        username (str): Github username that submitted the PR.
        category (str): Type of profile (community, partners, or redhat)
        organization (str): Name of the organization (ex: hashicorp)
        chart (str): Name of the chart (ex: vault)
    """
    print(
        "[INFO] Verify user. %s, %s, %s, %s" % (username, category, organization, chart)
    )
    owners_path = os.path.join("charts", category, organization, chart, "OWNERS")
    if not os.path.exists(owners_path):
        msg = f"[ERROR] {owners_path} file does not exist."
        write_error_log(directory, msg)
        sys.exit(1)

    data = open(owners_path).read()
    out = yaml.load(data, Loader=Loader)
    if username not in [x["githubUsername"] for x in out["users"]]:
        msg = f"[ERROR] {username} is not allowed to submit the chart on behalf of {organization}"
        write_error_log(directory, msg)
        sys.exit(1)


def check_owners_file_against_directory_structure(
    directory, category, organization, chart
):
    """Check that the content of the OWNERS file correspond to the directory structure
    the chart is under.

    Following assertion must be true:
    - the chart.name key must correspond to the name of the chart directory
    - the vendor.label key must correspond to the organization directory

    Args:
        directory (str): Local directory in which to write the error logs
        category (str): Type of profile (community, partners, or redhat)
        organization (str): Name of the organization (ex: hashicorp)
        chart (str): Name of the chart (ex: vault)
    """
    print(
        "[INFO] Check owners file against directory structure. %s, %s, %s"
        % (category, organization, chart)
    )
    data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
    out = yaml.load(data, Loader=Loader)
    vendor_label = out["vendor"]["label"]
    chart_name = out["chart"]["name"]
    error_exit = False
    msgs = []
    if organization != vendor_label:
        error_exit = True
        msgs.append(
            f"[ERROR] vendor/label in OWNERS file ({vendor_label}) doesn't match the directory structure (charts/{category}/{organization}/{chart})"
        )
    if chart != chart_name:
        msgs.append(
            f"[ERROR] chart/name in OWNERS file ({chart_name}) doesn't match the directory structure (charts/{category}/{organization}/{chart})"
        )
        error_exit = True
    if error_exit:
        write_error_log(directory, *msgs)
        sys.exit(1)


def verify_signature(category, organization, chart, version):
    """Verify that the PGP signature (report.yaml.asc) can decrypt report.yaml

    Args:
        category (str): Type of profile (community, partners, or redhat)
        organization (str): Name of the organization (ex: hashicorp)
        chart (str): Name of the chart (ex: vault)
        version (str): The version of the chart (ex: 1.4.0)
    """
    print("[INFO] Verify signature. %s, %s, %s" % (organization, chart, version))
    sign = os.path.join(
        "charts", category, organization, chart, version, "report.yaml.asc"
    )
    if os.path.exists(sign):
        data = open(
            os.path.join("charts", category, organization, chart, "OWNERS")
        ).read()
        out = yaml.load(data, Loader=Loader)
        publickey = out.get("publicPgpKey")
        if not publickey:
            return
        with open("public.key", "w") as fd:
            fd.write(publickey)
        out = subprocess.run(["gpg", "--import", "public.key"], capture_output=True)
        print("[INFO]", out.stdout.decode("utf-8"))
        print("[WARNING]", out.stderr.decode("utf-8"))
        report = os.path.join(
            "charts", category, organization, chart, version, "report.yaml"
        )
        out = subprocess.run(["gpg", "--verify", sign, report], capture_output=True)
        print("[INFO]", out.stdout.decode("utf-8"))
        print("[WARNING]", out.stderr.decode("utf-8"))
    else:
        print(f"[INFO] Signed report not found: {sign}.")


def match_checksum(
    directory, generated_report_info_path, category, organization, chart, version
):
    """Check that the provided report and the generated report have the same chart
    digest

    Args:
        directory (str): Local directory in which to write the error logs
        generated_report_info_path (str): Path to the processed JSON report generated
                                          in the pipeline
        category (str): Type of profile (community, partners, or redhat)
        organization (str): Name of the organization (ex: hashicorp)
        chart (str): Name of the chart (ex: vault)
        version (str): The version of the chart (ex: 1.4.0)
    """
    print("[INFO] Check digests match. %s, %s, %s" % (organization, chart, version))
    submitted_report_path = os.path.join(
        "charts", category, organization, chart, version, "report.yaml"
    )
    submitted_digests = report_info.get_report_digests(
        report_path=submitted_report_path
    )
    submitted_digest = submitted_digests["chart"]

    generated_digests = report_info.get_report_digests(
        report_info_path=generated_report_info_path
    )
    generated_digest = generated_digests["chart"]

    if submitted_digest != generated_digest:
        msg = f"[ERROR] Digest is not matching: {submitted_digest}, {generated_digest}"
        write_error_log(directory, msg)
        sys.exit(1)


def check_url(directory, report_path):
    """Check that the chart URL provided in report.yaml is valid and that the chart
    digest matches the one provided in report.yaml

    Args:
        directory (str): Local directory in which to write the error logs
        report_path (str): Path to report.yaml
    """
    print("[INFO] Check chart_url is a valid url. %s" % report_path)
    chart_url = report_info.get_report_chart_url(report_path=report_path)

    try:
        r = requests.head(chart_url)
    except requests.exceptions.InvalidSchema as err:
        msgs = []
        msgs.append(f"Invalid schema: {chart_url}")
        msgs.append(str(err))
        write_error_log(directory, *msgs)
        sys.exit(1)
    except requests.exceptions.InvalidURL as err:
        msgs = []
        msgs.append(f"Invalid URL: {chart_url}")
        msgs.append(str(err))
        write_error_log(directory, *msgs)
        sys.exit(1)
    except requests.exceptions.MissingSchema as err:
        msgs = []
        msgs.append(f"Missing schema in URL: {chart_url}")
        msgs.append(str(err))
        write_error_log(directory, *msgs)
        sys.exit(1)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        msgs = []
        msgs.append("[WARNING] URL is not accessible: {chart_url} ")
        msgs.append(str(err))
        write_error_log(directory, *msgs)

    verify_package_digest(chart_url, report_path)


def match_name_and_version(
    directory, category, organization, chart, version, generated_report_path
):
    """Check that the chart name and version in the provided report.yaml and in the
    report generated in the pipeline match the underlying directory structure.

    Args:
        directory (str): Local directory in which to write the error logs
        category (str): Type of profile (community, partners, or redhat)
        organization (str): Name of the organization (ex: hashicorp)
        chart (str): Name of the chart (ex: vault)
        version (str): The version of the chart (ex: 1.4.0)
        generated_report_path (str): Path to the report generated in the pipeline
    """
    print(
        "[INFO] Check chart has same name and version as directory structure. %s, %s, %s"
        % (organization, chart, version)
    )
    submitted_report_path = os.path.join(
        "charts", category, organization, chart, version, "report.yaml"
    )
    if os.path.exists(submitted_report_path):
        submitted_report_chart = report_info.get_report_chart(
            report_path=submitted_report_path
        )
        submitted_report_chart_name = submitted_report_chart["name"]
        submitted_report_chart_version = submitted_report_chart["version"]

        if submitted_report_chart_name != chart:
            msg = f"[ERROR] Chart name ({submitted_report_chart_name}) doesn't match the directory structure (charts/{category}/{organization}/{chart}/{version})"
            write_error_log(directory, msg)
            sys.exit(1)

        if submitted_report_chart_version != version:
            msg = f"[ERROR] Chart version ({submitted_report_chart_version}) doesn't match the directory structure (charts/{category}/{organization}/{chart}/{version})"
            write_error_log(directory, msg)
            sys.exit(1)

        if os.path.exists(generated_report_path):
            report_chart = report_info.get_report_chart(
                report_path=generated_report_path
            )
            report_chart_name = report_chart["name"]
            report_chart_version = report_chart["version"]

            if submitted_report_chart_name != report_chart_name:
                msg = f"[ERROR] Chart name in the chart is not matching against the value in the report: {submitted_report_chart_name} vs {report_chart_name}"
                write_error_log(directory, msg)
                sys.exit(1)

            if submitted_report_chart_version != report_chart_version:
                msg = f"[ERROR] Chart version in the chart is not matching against the value in the report: {submitted_report_chart_version} vs. {report_chart_version}"
                write_error_log(directory, msg)
                sys.exit(1)
    else:
        print(f"[INFO] No report submitted, get data from : {generated_report_path}")
        report_chart = report_info.get_report_chart(report_path=generated_report_path)
        report_chart_name = report_chart["name"]
        report_chart_version = report_chart["version"]

        if report_chart_name != chart:
            msg = f"[ERROR] Chart name ({report_chart_name}) doesn't match the directory structure (charts/{category}/{organization}/{chart}/{version})"
            write_error_log(directory, msg)
            sys.exit(1)

        if report_chart_version != version:
            msg = f"[ERROR] Chart version ({report_chart_version}) doesn't match the directory structure (charts/{category}/{organization}/{chart}/{version})"
            write_error_log(directory, msg)
            sys.exit(1)


def check_report_success(directory, api_url, report_path, report_info_path, version):
    """Check the content of report.yaml

    * Check that the version in the report matches with the directory structure.
    * Check that the vendor type in the report matches with the directory structure.
    * Check the presence of the required annotations.
    * Check that the report doesn't contains failed checks.
    * Check that the testedOpenShiftVersion and certifiedOpenShiftVersions labels
      contain SemVer compatible versions.

    Also adds the content of report.yaml to the GITHUB_OUTPUT.

    Args:
        directory (str): Local directory in which to write the error logs
        api_url (str): URL of the GitHub PR
        report_path (str): Path to report.yaml
        report_info_path (str): Path to processed JSON report
        version (str): The version of the chart (ex: 1.4.0)
    """
    print("[INFO] Check report success. %s" % report_path)
    data = open(report_path).read()
    print("[INFO] Full report: ")
    print(data)
    quoted_data = data.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
    gitutils.add_output("report_content", quoted_data)

    chart = report_info.get_report_chart(
        report_path=report_path, report_info_path=report_info_path
    )
    report_version = chart["version"]
    if report_version != version:
        msg = f"[ERROR] Chart Version '{report_version}' doesn't match the version in the directory path: '{version}'"
        write_error_log(directory, msg)
        sys.exit(1)

    report_metadata = report_info.get_report_metadata(
        report_path=report_path, report_info_path=report_info_path
    )
    profile_version = report_metadata["profileVersion"]
    vendor_type = get_vendor_type(directory)
    report_vendor_type = report_metadata["vendorType"]

    if report_vendor_type != vendor_type:
        msg = f"[ERROR] Report profile type '{report_vendor_type}' doesn't match the vendor type in the directory path: '{vendor_type}'"
        write_error_log(directory, msg)
        sys.exit(1)

    print(f"[INFO] Profile version:  {profile_version}")
    annotations = report_info.get_report_annotations(
        report_path=report_path, report_info_path=report_info_path
    )

    required_annotations = {
        "charts.openshift.io/lastCertifiedTimestamp",
        "charts.openshift.io/testedOpenShiftVersion",
        "charts.openshift.io/supportedOpenShiftVersions",
        "charts.openshift.io/digest",
    }

    if profile_version == "v1.0":
        required_annotations = {
            "charts.openshift.io/lastCertifiedTimestamp",
            "charts.openshift.io/certifiedOpenShiftVersions",
            "charts.openshift.io/digest",
        }

    available_annotations = set(annotations.keys())

    missing_annotations = required_annotations - available_annotations
    for annotation in missing_annotations:
        msg = f"[ERROR] Missing annotation in chart/report: {annotation}"
        write_error_log(directory, msg)
        sys.exit(1)

    report = report_info.get_report_results(
        report_path=report_path,
        report_info_path=report_info_path,
        profile_type=vendor_type,
    )

    label_names = prartifact.get_labels(api_url)

    failed = report["failed"]
    passed = report["passed"]
    failures_in_report = failed > 0
    if failures_in_report:
        msgs = []
        msgs.append("[ERROR] Chart verifier report includes failures:")
        msgs.append(f"- Number of checks passed: {passed}")
        msgs.append(f"- Number of checks failed: {failed}")
        msgs.append("- Error message(s):")
        for m in report["message"]:
            msgs.append(f"  - {m}")
        write_error_log(directory, *msgs)
        if vendor_type == "redhat":
            gitutils.add_output("redhat_to_community", "True")
        if vendor_type != "redhat" and "force-publish" not in label_names:
            if vendor_type == "community":
                # requires manual review and approval
                gitutils.add_output("community_manual_review_required", "True")
            sys.exit(1)

    if vendor_type == "community" and "force-publish" not in label_names:
        # requires manual review and approval
        print("[INFO] Community submission requires manual approval.")
        gitutils.add_output("community_manual_review_required", "True")
        sys.exit(1)

    if failures_in_report or vendor_type == "community":
        return

    if "charts.openshift.io/testedOpenShiftVersion" in annotations:
        full_version = annotations["charts.openshift.io/testedOpenShiftVersion"]
        try:
            semantic_version.Version.coerce(full_version)
        except ValueError:
            msg = f"[ERROR] tested OpenShift version not conforming to SemVer spec: {full_version}"
            write_error_log(directory, msg)
            sys.exit(1)

    if "charts.openshift.io/certifiedOpenShiftVersions" in annotations:
        full_version = annotations["charts.openshift.io/certifiedOpenShiftVersions"]
        if not semver.VersionInfo.is_valid(full_version):
            msg = f"[ERROR] certified OpenShift version not conforming to SemVer spec: {full_version}"
            write_error_log(directory, msg)
            sys.exit(1)


def verify_package_digest(url, report):
    print("[INFO] check package digest.")

    response = requests.get(url, allow_redirects=True)
    if response.status_code == 200:
        target_digest = hashlib.sha256(response.content).hexdigest()

    found, report_data = verifier_report.get_report_data(report)
    if found:
        pkg_digest = verifier_report.get_package_digest(report_data)

    if target_digest:
        if pkg_digest and pkg_digest != target_digest:
            # Digest was passed and computed but differ
            raise Exception(
                "Found an integrity issue. SHA256 digest passed does not match SHA256 digest computed."
            )
    elif not pkg_digest:
        # Digest was not passed and could not be computed
        raise Exception(
            "Was unable to compute SHA256 digest, please ensure chart url points to a chart package."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        dest="directory",
        type=str,
        required=True,
        help="artifact directory for archival",
    )
    parser.add_argument(
        "-n",
        "--verify-user",
        dest="username",
        type=str,
        required=True,
        help="check if the user can update the chart",
    )
    parser.add_argument(
        "-u",
        "--api-url",
        dest="api_url",
        type=str,
        required=True,
        help="API URL for the pull request",
    )
    args = parser.parse_args()

    category, organization, chart, version = get_modified_charts(
        args.directory, args.api_url
    )
    verify_user(args.directory, args.username, category, organization, chart)
    check_owners_file_against_directory_structure(
        args.directory, category, organization, chart
    )

    report_generated = os.environ.get("REPORT_GENERATED")
    generated_report_path = os.environ.get("GENERATED_REPORT_PATH")
    generated_report_info_path = os.environ.get("REPORT_SUMMARY_PATH")
    env = Env()
    web_catalog_only = env.bool("WEB_CATALOG_ONLY", False)

    submitted_report_path = os.path.join(
        "charts", category, organization, chart, version, "report.yaml"
    )
    if os.path.exists(submitted_report_path):
        ocp_version_range = os.environ.get("OCP_VERSION_RANGE")
        report_valid, message = verifier_report.validate(
            submitted_report_path, ocp_version_range
        )
        if not report_valid:
            msg = f"Submitted report is not valid: {message}"
            print(f"[ERROR] {msg}")
            write_error_log(args.directory, msg)
            sys.exit(1)

        print("[INFO] Submitted report passed validity check!")
        owners_file = os.path.join("charts", category, organization, chart, "OWNERS")
        pgp_key_in_owners = signedchart.get_pgp_key_from_owners(owners_file)
        if pgp_key_in_owners:
            if signedchart.check_report_for_signed_chart(submitted_report_path):
                if not signedchart.check_pgp_public_key(
                    pgp_key_in_owners, submitted_report_path
                ):
                    msg = "PGP key in OWNERS file does not match with key digest in report."
                    print(f"[ERROR] {msg}")
                    write_error_log(args.directory, msg)
                    sys.exit(1)
                else:
                    print(
                        "[INFO] PGP key in OWNERS file matches with key digest in report."
                    )

        print("[INFO] Report exists: ", submitted_report_path)
        verify_signature(category, organization, chart, version)
        report_path = submitted_report_path
        report_info_path = ""
        if report_generated and report_generated == "True":
            match_checksum(
                args.directory,
                generated_report_info_path,
                category,
                organization,
                chart,
                version,
            )
        elif not web_catalog_only:
            check_url(args.directory, report_path)
    else:
        print("[INFO] Report does not exist: ", submitted_report_path)
        report_path = generated_report_path
        report_info_path = generated_report_info_path

    print(f"[INFO]: report path: {report_path}")
    print(f"[INFO]: generated report path: {generated_report_path}")
    print(f"[INFO]: generated report info: {generated_report_info_path}")

    match_name_and_version(
        args.directory, category, organization, chart, version, generated_report_path
    )
    check_report_success(
        args.directory, args.api_url, report_path, report_info_path, version
    )
