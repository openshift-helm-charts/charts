import re
import os
import sys
import argparse
import subprocess
import json
import hashlib
import tempfile

import semver
import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

sys.path.append('../')
from report import report_info

def write_error_log(directory, *msg):
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

def get_labels(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(api_url, headers=headers)
    return r.json()["labels"]

def get_modified_charts(directory, api_url):
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(files_api_url, headers=headers)
    pattern = re.compile(r"charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.-]+)/.*")
    for f in r.json():
        m = pattern.match(f["filename"])
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version

    msg = "[ERROR] One or more files included in the pull request are not part of the chart"
    write_error_log(directory, msg)
    sys.exit(1)

def verify_user(directory, username, category, organization, chart):
    owners_path = os.path.join("charts", category, organization, chart, "OWNERS")
    if not os.path.exists(owners_path):
        msg = f"[ERROR] {owners_path} file does not exist."
        write_error_log(directory, msg)
        sys.exit(1)

    data = open(owners_path).read()
    out = yaml.load(data, Loader=Loader)
    if username not in [x['githubUsername'] for x in out['users']]:
        msg = f"[ERROR] {username} is not allowed to submit the chart on behalf of {organization}"
        write_error_log(directory, msg)
        sys.exit(1)

def check_owners_file_against_directory_structure(directory,username, category, organization, chart):
    data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
    out = yaml.load(data, Loader=Loader)
    vendor_label = out["vendor"]["label"]
    chart_name = out["chart"]["name"]
    error_exit = False
    msgs = []
    if organization != vendor_label:
        error_exit = True
        msgs.append(f"[ERROR] vendor/label in OWNERS file ({vendor_label}) doesn't match the directory structure (charts/{category}/{organization}/{chart})")
    if chart != chart_name:
        msgs.append(f"[ERROR] chart/name in OWNERS file ({chart_name}) doesn't match the directory structure (charts/{category}/{organization}/{chart})")
        error_exit = True
    if error_exit:
        write_error_log(directory, *msgs)
        sys.exit(1)

def verify_signature(directory, category, organization, chart, version):
    data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
    out = yaml.load(data, Loader=Loader)
    publickey = out.get('publicPgpKey')
    if not publickey:
        return
    with open("public.key", "w") as fd:
        fd.write(publickey)
    out = subprocess.run(["gpg", "--import", "public.key"], capture_output=True)
    print("[INFO]", out.stdout.decode("utf-8"))
    print("[WARNING]", out.stderr.decode("utf-8"))
    report = os.path.join("charts", category, organization, chart, version, "report.yaml")
    sign = os.path.join("charts", category, organization, chart, version, "report.yaml.asc")
    out = subprocess.run(["gpg", "--verify", sign, report], capture_output=True)
    print("[INFO]", out.stdout.decode("utf-8"))
    print("[WARNING]", out.stderr.decode("utf-8"))

def match_checksum(directory, category, organization, chart, version):
    submitted_report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    submitted_digests = report_info.getReportDigests(submitted_report_path)
    submitted_digest = submitted_digests["chart"]

    generated_report_path = "report.yaml"
    generated_digests = report_info.getReportDigests(generated_report_path)
    generated_digest = generated_digests]["chart"]

    if  submitted_digest != generated_digest:
        msg = f"[ERROR] Digest is not matching: {submitted_digest}, {generated_digest}"
        write_error_log(directory, msg)
        sys.exit(1)

def check_url(directory, report_path):
    chart_url = report_info.getReportChartUrl(report_path)

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

def match_name_and_version(directory, category, organization, chart, version):
    submitted_report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    if os.path.exists(submitted_report_path):
        submitted_report_chart = report_info.getReportChart(submitted_report_path)
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

        if os.path.exists("report.yaml"):
            report_chart = report_info.getReportChart(report_path)
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
        report_chart = report_info.getReportChart(report_path)
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

def check_report_success(directory, api_url, report_path, version):
    data = open(report_path).read()
    print("[INFO] Full report: ")
    print(data)
    quoted_data = data.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
    print(f"::set-output name=report_content::{quoted_data}")

    chart = report_info.getReportChart(report_path)
    report_version = chart["version"]
    if report_version != version:
        msg = f"[ERROR] Chart Version '{report_version}' doesn't match the version in the directory path: '{version}'"
        write_error_log(directory, msg)
        sys.exit(1)

    annotations = report_info.getAnnotations(report_path)

    required_annotations = {"charts.openshift.io/lastCertifiedTimestamp",
                            "charts.openshift.io/certifiedOpenShiftVersions",
                            "charts.openshift.io/digest"}

    available_annotations = set(annotations.keys())

    missing_annotations = required_annotations - available_annotations
    for annotation in missing_annotations:
        msg = f"[ERROR] Missing annotation in chart/report: {annotation}"
        write_error_log(directory, msg)
        sys.exit(1)

    vendor_type = get_vendor_type(directory)
    report = report_info.getReportResults(report_path,vendor_type,"")

    labels = get_labels(api_url)
    label_names = [l["name"] for l in labels]

    failed = report["failed"]
    passed = report["passed"]
    if failed > 0:
        msgs = []
        msgs.append("[ERROR] Chart verifier report includes failures:")
        msgs.append(f"- Number of checks passed: {passed}")
        msgs.append(f"- Number of checks failed: {failed}")
        msgs.append(f"- Error message(s):")
        for m in report["message"]:
            msgs.append(f"  - {m}")
        write_error_log(directory, *msgs)
        if vendor_type == "redhat":
            print(f"::set-output name=redhat_to_community::True")
        if vendor_type != "redhat" and "force-publish" not in label_names:
            sys.exit(1)
    if vendor_type == "community" and "force-publish" not in label_names:
        # requires manual review and approval
        msg = "[INFO] Community charts require manual review and approval from maintainers"
        write_error_log(directory, msg)
        sys.exit(1)

    if "charts.openshift.io/certifiedOpenShiftVersions" in annotations:
        full_version = annotations["charts.openshift.io/certifiedOpenShiftVersions"]
        if not semver.VersionInfo.isvalid(full_version):
            msg = f"[ERROR] OpenShift version not conforming to SemVer spec: {full_version}"
            write_error_log(directory, msg)
            sys.exit(1)


def generate_verify_report(directory, category, organization, chart, version):
    src = os.path.join(os.getcwd(), "charts", category, organization, chart, version, "src")
    report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    src_exists = False
    tar_exists = False
    if os.path.exists(src):
        src_exists = True
    tar = os.path.join("charts", category, organization, chart, version, f"{chart}-{version}.tgz")
    if os.path.exists(tar):
        tar_exists = True
    if src_exists and tar_exists:
        msg = "[ERROR] Both chart source directory and tarball should not exist"
        write_error_log(directory, msg)
        sys.exit(1)
    if not os.path.exists(report_path):
        if not src_exists and not tar_exists:
            msg = "[ERROR] One of these must be modified: report, chart source, or tarball"
            write_error_log(directory, msg)
            sys.exit(1)
    kubeconfig = os.environ.get("KUBECONFIG")
    if not kubeconfig:
        msg = "[ERROR] missing 'KUBECONFIG' environment variable"
        write_error_log(directory, msg)
        sys.exit(1)
    vendor_type = get_vendor_type(directory)
    if src_exists:
        if os.path.exists(report_path):
            out = subprocess.run(["docker", "run", "-v", src+":/charts:z", "-v", kubeconfig+":/kubeconfig", "-e", "KUBECONFIG=/kubeconfig", "--rm",
                                 os.environ.get("VERIFIER_IMAGE"), "verify", "--set", f"profile.vendortype={vendor_type}", "-e", "has-readme", "/charts"], capture_output=True)
        else:
            out = subprocess.run(["docker", "run", "-v", src+":/charts:z", "-v", kubeconfig+":/kubeconfig", "-e", "KUBECONFIG=/kubeconfig", "--rm",
                                 os.environ.get("VERIFIER_IMAGE"), "verify", "--set", f"profile.vendortype={vendor_type}", "/charts"], capture_output=True)
    elif tar_exists:
        dn = os.path.join(os.getcwd(), "charts", category,
                          organization, chart, version)
        if os.path.exists(report_path):
            out = subprocess.run(["docker", "run", "-v", dn+":/charts:z", "-v", kubeconfig+":/kubeconfig", "-e", "KUBECONFIG=/kubeconfig", "--rm", os.environ.get("VERIFIER_IMAGE"),
                                 "verify", "--set", f"profile.vendortype={vendor_type}", "-e", "has-readme", f"/charts/{chart}-{version}.tgz"], capture_output=True)
        else:
            out = subprocess.run(["docker", "run", "-v", dn+":/charts:z", "-v", kubeconfig+":/kubeconfig", "-e", "KUBECONFIG=/kubeconfig", "--rm",
                                 os.environ.get("VERIFIER_IMAGE"), "verify", "--set", f"profile.vendortype={vendor_type}", f"/charts/{chart}-{version}.tgz"], capture_output=True)
    else:
        return

    stderr = out.stderr.decode("utf-8")
    report_path = "report.yaml"
    print("[INFO] report:\n", stderr)
    with open(report_path, "w") as fd:
        fd.write(stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", dest="directory", type=str, required=True,
                                        help="artifact directory for archival")
    parser.add_argument("-n", "--verify-user", dest="username", type=str, required=True,
                                        help="check if the user can update the chart")
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    args = parser.parse_args()
    os.makedirs(args.directory, exist_ok=True)
    category, organization, chart, version = get_modified_charts(args.directory, args.api_url)
    verify_user(args.directory, args.username, category, organization, chart)
    check_owners_file_against_directory_structure(args.directory, args.username, category, organization, chart)
    submitted_report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    generate_verify_report(args.directory, category, organization, chart, version)
    if os.path.exists(submitted_report_path):
        print("[INFO] Report exists: ", submitted_report_path)
        verify_signature(args.directory, category, organization, chart, version)
        report_path = submitted_report_path
        if os.path.exists("report.yaml"):
            match_checksum(args.directory, category, organization, chart, version)
        else:
            check_url(args.directory, report_path)
    else:
        print("[INFO] Report does not exist: ", submitted_report_path)
        report_path = "report.yaml"

    match_name_and_version(args.directory, category, organization, chart, version)
    check_report_success(args.directory, args.api_url, report_path, version)
