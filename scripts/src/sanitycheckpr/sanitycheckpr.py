import re
import os
import sys
import argparse

import requests

ALLOW_CI_CHANGES = "allow/ci-changes"

def ensure_only_chart_is_modified(number):
    url = f'https://api.github.com/repos/openshift-helm-charts/repo/pulls/{number}'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(url, headers=headers)
    for label in r.json()["labels"]:
        if label["name"] == ALLOW_CI_CHANGES:
            return
    url = f'https://api.github.com/repos/openshift-helm-charts/repo/pulls/{number}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(url, headers=headers)
    pattern = re.compile(r"charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/.*")
    count = 0
    for f in r.json():
        if not pattern.match(f["filename"]):
            print("PR should only modify chart related files")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--pr-number", dest="number", type=str, required=True,
                                        help="current pull request number")
    args = parser.parse_args()
    ensure_only_chart_is_modified(args.number)


if __name__ == "__main__":
    main()
