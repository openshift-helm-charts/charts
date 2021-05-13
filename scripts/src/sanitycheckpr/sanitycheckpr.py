import re
import os
import sys
import argparse

import requests

ALLOW_CI_CHANGES = "allow/ci-changes"

def ensure_only_chart_is_modified(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(api_url, headers=headers)
    for label in r.json()["labels"]:
        if label["name"] == ALLOW_CI_CHANGES:
            return
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(files_api_url, headers=headers)
    pattern = re.compile(r"charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/.*")
    reportpattern = re.compile(r"charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/report.yaml")
    count = 0
    for f in r.json():
        if not pattern.match(f["filename"]):
            print("PR should only modify chart related files")
            sys.exit(1)
        elif reportpattern.match(f["filename"]):
            print("[INFO] Report found")
            print("::set-output name=report-exists::true")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    args = parser.parse_args()
    ensure_only_chart_is_modified(args.api_url)


if __name__ == "__main__":
    main()
