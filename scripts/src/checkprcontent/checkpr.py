import argparse
import json
import os
import re
import sys

import requests
import semver
import yaml
from reporegex import matchers

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

sys.path.append("../")
from owners import owners_file
from pullrequest import prartifact
from report import verifier_report
from tools import gitutils

ALLOW_CI_CHANGES = "allow/ci-changes"


def check_web_catalog_only(report_in_pr, num_files_in_pr, report_file_match):
    print(f"[INFO] report in PR {report_in_pr}")
    print(f"[INFO] num files in PR {num_files_in_pr}")

    category, organization, chart, version = report_file_match.groups()

    print(f"read owners file : {category}/{organization}/{chart}")
    found_owners, owner_data = owners_file.get_owner_data(category, organization, chart)

    if found_owners:
        owner_web_catalog_only = owners_file.get_web_catalog_only(owner_data)
        print(
            f"[INFO] webCatalogOnly/providerDelivery from OWNERS : {owner_web_catalog_only}"
        )
    else:
        msg = "[ERROR] OWNERS file was not found."
        print(msg)
        gitutils.add_output("owners-error-message", msg)
        sys.exit(1)

    if report_in_pr:
        report_file_path = os.path.join(
            "pr-branch", "charts", category, organization, chart, version, "report.yaml"
        )
        print(f"read report file : {report_file_path}")
        found_report, report_data = verifier_report.get_report_data(report_file_path)

        if found_report:
            report_web_catalog_only = verifier_report.get_web_catalog_only(report_data)
            print(
                f"[INFO] webCatalogOnly/providerDelivery from report : {report_web_catalog_only}"
            )
        else:
            msg = f"[ERROR] Failed tp open report: {report_file_path}."
            print(msg)
            gitutils.add_output("pr-content-error-message", msg)
            sys.exit(1)

    web_catalog_only = False
    if report_in_pr and num_files_in_pr > 1:
        if report_web_catalog_only or owner_web_catalog_only:
            msg = "[ERROR] The web catalog distribution method requires the pull request to be report only."
            print(msg)
            gitutils.add_output("pr-content-error-message", msg)
            sys.exit(1)
    elif report_in_pr:
        if report_web_catalog_only and owner_web_catalog_only:
            if verifier_report.get_package_digest(report_data):
                web_catalog_only = True
            else:
                msg = "[ERROR] The web catalog distribution method requires a package digest in the report."
                print(msg)
                gitutils.add_output("pr-content-error-message", msg)
                sys.exit(1)
        elif report_web_catalog_only:
            msg = "[ERROR] Report indicates web catalog only but the distribution method set for the chart is not web catalog only."
            print(msg)
            gitutils.add_output("pr-content-error-message", msg)
            sys.exit(1)
        elif owner_web_catalog_only:
            msg = "[ERROR] The web catalog distribution method is set for the chart but is not set in the report."
            print(msg)
            gitutils.add_output("pr-content-error-message", msg)
            sys.exit(1)

    if web_catalog_only:
        print("[INFO] webCatalogOnly/providerDelivery is a go")
        gitutils.add_output("web_catalog_only", "True")
    else:
        gitutils.add_output("web_catalog_only", "False")
        print("[INFO] webCatalogOnly/providerDelivery is a no-go")


def get_file_match_compiled_patterns():
    """Return a tuple of patterns, where the first can be used to match any file in a chart PR
    and the second can be used to match a valid report file within a chart PR. The patterns
    match based on the relative path of a file to the base repository

    Both patterns capture chart type, chart vendor, chart name and chart version from the file path..

    Examples of valid file paths are:

    charts/partners/hashicorp/vault/0.20.0/<file>
    charts/partners/hashicorp/vault/0.20.0//report.yaml
    """

    base = matchers.submission_path_matcher()

    pattern = re.compile(base + r"/.*")
    reportpattern = re.compile(base + r"/report.yaml")
    tarballpattern = re.compile(base + r"/(.*\.tgz)")
    return pattern, reportpattern, tarballpattern


def ensure_only_chart_is_modified(api_url, repository, branch):
    label_names = prartifact.get_labels(api_url)
    for label_name in label_names:
        if label_name == ALLOW_CI_CHANGES:
            return

    files = prartifact.get_modified_files(api_url)
    pattern, reportpattern, tarballpattern = get_file_match_compiled_patterns()
    matches_found = 0
    report_found = False
    none_chart_files = {}

    for file_path in files:
        match = pattern.match(file_path)
        if not match:
            file_name = os.path.basename(file_path)
            none_chart_files[file_name] = file_path
        else:
            matches_found += 1
            if reportpattern.match(file_path):
                print(f"[INFO] Report found: {file_path}")
                gitutils.add_output("report-exists", "true")
                report_found = True
            else:
                tar_match = tarballpattern.match(file_path)
                if tar_match:
                    print(f"[INFO] tarball found: {file_path}")
                    _, _, chart_name, chart_version, tar_name = tar_match.groups()
                    expected_tar_name = f"{chart_name}-{chart_version}.tgz"
                    if tar_name != expected_tar_name:
                        msg = f"[ERROR] the tgz file is named incorrectly. Expected: {expected_tar_name}. Got: {tar_name}"
                        print(msg)
                        gitutils.add_output("pr-content-error-message", msg)
                        exit(1)

            if matches_found == 1:
                pattern_match = match
            elif pattern_match.groups() != match.groups():
                msg = "[ERROR] A PR must contain only one chart. Current PR includes files for multiple charts."
                print(msg)
                gitutils.add_output("pr-content-error-message", msg)
                exit(1)

    if none_chart_files:
        if (
            len(files) > 1 or "OWNERS" not in none_chart_files
        ):  # OWNERS not present or preset but not the only file
            example_file = list(none_chart_files.values())[0]
            msg = f"[ERROR] PR includes one or more files not related to charts, e.g., {example_file}"
            print(msg)
            gitutils.add_output("pr-content-error-message", msg)

        if "OWNERS" in none_chart_files:
            file_path = none_chart_files["OWNERS"]
            path_parts = file_path.split("/")
            category = path_parts[1]  # Second after charts
            if category == "partners":
                msg = "[ERROR] OWNERS file should never be set directly by partners. See certification docs."
                print(msg)
                gitutils.add_output("owners-error-message", msg)
            elif (
                matches_found > 0
            ):  # There is a mix of chart and non-chart files including OWNERS
                msg = "[ERROR] Send OWNERS file by itself in a separate PR."
                print(msg)
                gitutils.add_output("owners-error-message", msg)
            elif len(files) == 1:  # OWNERS file is the only file in PR
                msg = "[INFO] OWNERS file changes require manual review by maintainers."
                print(msg)
                gitutils.add_output("owners-error-message", msg)

        sys.exit(1)

    check_web_catalog_only(report_found, matches_found, pattern_match)

    if matches_found > 0:
        category, organization, chart, version = pattern_match.groups()
        gitutils.add_output(
            "category", f"{'partner' if category == 'partners' else category}"
        )
        gitutils.add_output("organization", organization)
        gitutils.add_output("chart-name", chart)

        if not semver.VersionInfo.is_valid(version):
            msg = (
                f"[ERROR] Helm chart version is not a valid semantic version: {version}"
            )
            print(msg)
            gitutils.add_output("pr-content-error-message", msg)
            sys.exit(1)

        # Red Hat charts must carry the Red Hat prefix.
        if organization == "redhat":
            if not chart.startswith("redhat-"):
                msg = f"[ERROR] Charts provided by Red Hat must have their name begin with the redhat- prefix. I.e. redhat-{chart}"
                gitutils.add_output("pr-content-error-message", msg)
                sys.exit(1)

        # Non Red Hat charts must not carry the Red Hat prefix.
        if organization != "redhat" and chart.startswith("redhat-"):
            msg = f"[ERROR] The redhat- prefix is reserved for charts provided by Red Hat. Your chart: {chart}"
            gitutils.add_output("pr-content-error-message", msg)
            sys.exit(1)

        # Check the index.yaml for the existence of this chart at this version.
        print("Downloading index.yaml", category, organization, chart, version)
        r = requests.get(
            f"https://raw.githubusercontent.com/{repository}/{branch}/index.yaml"
        )

        if r.status_code == 200:
            data = yaml.load(r.text, Loader=Loader)
        else:
            data = {"apiVersion": "v1", "entries": {}}

        entry_name = chart
        d = data["entries"].get(entry_name, [])
        gitutils.add_output("chart-entry-name", entry_name)
        for v in d:
            if v["version"] == version:
                msg = f"[ERROR] Helm chart release already exists in the index.yaml: {version}"
                print(msg)
                gitutils.add_output("pr-content-error-message", msg)
                sys.exit(1)

        tag_name = f"{organization}-{chart}-{version}"
        gitutils.add_output("release_tag", tag_name)
        tag_api = f"https://api.github.com/repos/{repository}/git/ref/tags/{tag_name}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        print(f"[INFO] checking tag: {tag_api}")
        r = requests.head(tag_api, headers=headers)
        if r.status_code == 200:
            msg = f"[ERROR] Helm chart release already exists in the GitHub Release/Tag: {tag_name}"
            print(msg)
            gitutils.add_output("pr-content-error-message", msg)
            sys.exit(1)
        try:
            if prartifact.xRateLimit in r.headers:
                print(
                    f"[DEBUG] {prartifact.xRateLimit} : {r.headers[prartifact.xRateLimit]}"
                )
            if prartifact.xRateRemain in r.headers:
                print(
                    f"[DEBUG] {prartifact.xRateRemain}  : {r.headers[prartifact.xRateRemain]}"
                )

            response_content = r.json()
            if "message" in response_content:
                print(
                    f'[ERROR] getting index file content: {response_content["message"]}'
                )
                sys.exit(1)
        except json.decoder.JSONDecodeError:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b",
        "--index-branch",
        dest="branch",
        type=str,
        required=True,
        help="index branch",
    )
    parser.add_argument(
        "-r",
        "--repository",
        dest="repository",
        type=str,
        required=True,
        help="Git Repository",
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
    branch = args.branch.split("/")[-1]
    ensure_only_chart_is_modified(args.api_url, args.repository, branch)


if __name__ == "__main__":
    main()
