import re
import os
import sys
import argparse
import shutil
import pathlib

import requests

sys.path.append('../')
from checkprcontent import checkpr

# TODO(baijum): Move this code under chartsubmission.chart module
def get_modified_charts(api_url):
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(files_api_url, headers=headers)
    pattern,_ = checkpr.get_file_match_compiled_patterns()
    for f in r.json():
        m = pattern.match(f["filename"])
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version

    return "", "", "", ""

def get_modified_files(api_url):
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(files_api_url, headers=headers)
    pr_files = []
    print(f"[INFO] file info in PR {r.json()}")
    for f in r.json():
        if "filename" in f:
            pr_files.append(f["filename"])
    return pr_files

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
    parser.add_argument("-d", "--directory", dest="directory", type=str, required=False,
                                        help="artifact directory for archival")
    parser.add_argument("-n", "--pr-number", dest="number", type=str, required=False,
                                        help="current pull request number")
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    parser.add_argument("-f","--get-files", dest="get_files", default=False,action='store_true' )

    args = parser.parse_args()
    if args.get_files:
        pr_files = get_modified_files(args.api_url)
        print(f"[INFO] files in pr: {pr_files}")
        print(f"::set-output name=pr_files::{pr_files}")
    else:
        os.makedirs(args.directory, exist_ok=True)
        category, organization, chart, version = get_modified_charts(args.api_url)
        save_metadata(args.directory, organization, chart, args.number)

if __name__ == "__main__":
    main()
