import re
import os
import sys
import argparse
import subprocess

import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def get_modified_charts(number):
    url = f'https://api.github.com/repos/openshift-helm-charts/repo/pulls/{number}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(url, headers=headers)
    pattern = re.compile("charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/.*")
    count = 0
    for f in r.json():
        m = pattern.match(f["filename"])
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version

    return "", "", "", ""


def verify_user(username, category, organization, chart, version):
    data = open(os.path.join("charts", category, organization, chart, "owner.yaml")).read()
    out = yaml.load(data, Loader=Loader)
    if username not in out['usernames']:
        print("User doesn't exist in list of owners:", username)
        sys.exit(1)

def verify_report(category, organization, chart, version):
    data = open(os.path.join("charts", category, organization, chart, "owner.yaml")).read()
    out = yaml.load(data, Loader=Loader)
    publickey = out['public-key']
    with open("public.key", "w") as fd:
        fd.write(publickey)
    out = subprocess.run(["gpg", "--import", "public.key"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    report = os.path.join("charts", category, organization, chart, version, "report.yaml")
    sign = os.path.join("charts", category, organization, chart, version, "report.yaml.asc")
    out = subprocess.run(["gpg", "--verify", sign, report], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    return report

def check_report_success(report_path):
    data = open(report_path).read()
    out = yaml.load(data, Loader=Loader)
    if not out['ok']:
        print("Report is not successful")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--verify-user", dest="username", type=str, required=True,
                                        help="check if the user can update the chart")
    parser.add_argument("-n", "--pr-number", dest="number", type=str, required=True,
                                        help="current pull request number")
    args = parser.parse_args()
    category, organization, chart, version = get_modified_charts(args.number)
    verify_user(args.username, category, organization, chart, version)
    report_path = verify_report(category, organization, chart, version)
    check_report_success(report_path)
