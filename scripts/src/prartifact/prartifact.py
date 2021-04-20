import re
import os
import sys
import argparse

import requests

# TODO(baijum): Move this code under chartsubmission.chart module
def get_modified_charts(number):
    url = f'https://api.github.com/repos/openshift-helm-charts/repo/pulls/{number}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(url, headers=headers)
    pattern = re.compile(r"charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/.*")
    count = 0
    for f in r.json():
        m = pattern.match(f["filename"])
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version

    return "", "", "", ""


def save_metadata(directory, vendor_label, chart, number):
    with open(os.path.join(directory, "vendor"), "w") as fd:
        fd.write(vendor_label)

    with open(os.path.join(directory, "chart"), "w") as fd:
        fd.write(chart)

    with open(os.path.join(directory, "NR"), "w") as fd:
        fd.write(number)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", dest="directory", type=str, required=True,
                                        help="current working directory")
    parser.add_argument("-n", "--pr-number", dest="number", type=str, required=True,
                                        help="current pull request number")
    args = parser.parse_args()
    os.mkdir(args.directory)
    category, organization, chart, version = get_modified_charts(args.number)
    save_metadata(args.directory, organization, chart, args.number)

if __name__ == "__main__":
    main()
