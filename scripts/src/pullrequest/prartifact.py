import argparse
import os
import pathlib
import shutil
import sys

import requests

sys.path.append("../")
from checkprcontent import checkpr
from tools import gitutils

pr_files = []
pr_labels = []
xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"


# TODO(baijum): Move this code under chartsubmission.chart module
def get_modified_charts(api_url):
    files = get_modified_files(api_url)
    pattern, _, _ = checkpr.get_file_match_compiled_patterns()
    for file in files:
        match = pattern.match(file)
        if match:
            category, organization, chart, version = match.groups()
            return category, organization, chart, version

    return "", "", "", ""


def get_modified_files(api_url):
    """Populates and returns the list of files modified by this the PR

    Args:
        api_url (str): URL of the GitHub PR

    Returns:
        list[str]: List of modified files
    """
    if not pr_files:
        page_number = 1
        max_page_size, page_size = 100, 100
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        files_api_url = f"{api_url}/files"

        while page_size == max_page_size:
            files_api_query = f"{files_api_url}?per_page={page_size}&page={page_number}"
            print(f"[INFO] Query files : {files_api_query}")
            r = requests.get(files_api_query, headers=headers)
            files = r.json()
            page_size = len(files)
            page_number += 1

            if xRateLimit in r.headers:
                print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
            if xRateRemain in r.headers:
                print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

            if "message" in files:
                print(f'[ERROR] getting pr files: {files["message"]}')
                sys.exit(1)
            else:
                for file in files:
                    if "filename" in file:
                        pr_files.append(file["filename"])

    return pr_files


def get_labels(api_url):
    if not pr_labels:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        r = requests.get(api_url, headers=headers)
        pr_data = r.json()

        if xRateLimit in r.headers:
            print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
        if xRateRemain in r.headers:
            print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

        if "message" in pr_data:
            print(f'[ERROR] getting pr files: {pr_data["message"]}')
            sys.exit(1)
        if "labels" in pr_data:
            for label in pr_data["labels"]:
                pr_labels.append(label["name"])

    return pr_labels


def save_metadata(directory, vendor_label, chart, number):
    with open(os.path.join(directory, "vendor"), "w") as fd:
        print(f"add {directory}/vendor as {vendor_label}")
        fd.write(vendor_label)

    with open(os.path.join(directory, "chart"), "w") as fd:
        print(f"add {directory}/chart as {chart}")
        fd.write(chart)

    with open(os.path.join(directory, "NR"), "w") as fd:
        fd.write(number)

    if os.path.exists("report.yaml"):
        shutil.copy("report.yaml", directory)
    else:
        pathlib.Path(os.path.join(directory, "report.yaml")).touch()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        dest="directory",
        type=str,
        required=False,
        help="artifact directory for archival",
    )
    parser.add_argument(
        "-n",
        "--pr-number",
        dest="number",
        type=str,
        required=False,
        help="current pull request number",
    )
    parser.add_argument(
        "-u",
        "--api-url",
        dest="api_url",
        type=str,
        required=True,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-f", "--get-files", dest="get_files", default=False, action="store_true"
    )

    args = parser.parse_args()
    if args.get_files:
        pr_files = get_modified_files(args.api_url)
        print(f"[INFO] files in pr: {pr_files}")
        gitutils.add_output("pr_files", pr_files)
    else:
        os.makedirs(args.directory, exist_ok=True)
        category, organization, chart, version = get_modified_charts(args.api_url)
        save_metadata(args.directory, organization, chart, args.number)


if __name__ == "__main__":
    main()
