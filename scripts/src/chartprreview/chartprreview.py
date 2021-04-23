import re
import os
import sys
import argparse
import subprocess
import json

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
    pattern = re.compile(r"charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/.*")
    count = 0
    for f in r.json():
        m = pattern.match(f["filename"])
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version

    return "", "", "", ""


def verify_user(username, category, organization, chart):
    data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
    out = yaml.load(data, Loader=Loader)
    if username not in [x['githubUsername'] for x in out['users']]:
        print("User doesn't exist in list of owners:", username)
        sys.exit(1)

def check_owners_file_against_directory_structure(username, category, organization, chart):
    data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
    out = yaml.load(data, Loader=Loader)
    vendor_label = out["vendor"]["label"]
    chart_name = out["chart"]["name"]
    error_exit = False
    if organization != vendor_label:
        error_exit = True
        print("vendor/label in OWNERS file doesn't match the directory structure.")
    if chart != chart_name:
        print("chart/name in OWNERS file doesn't match the directory structure.")
        error_exit = True
    if error_exit:
        sys.exit(1)

def verify_signature(category, organization, chart, version):
    data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
    out = yaml.load(data, Loader=Loader)
    publickey = out['publicPgpKey']
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
    print("Full report: ")
    print(data)
    try:
        out = yaml.load(data, Loader=Loader)
    except yaml.scanner.ScannerError as err:
        print("YAML error: {0}".format(err))
        sys.exit(1)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        sys.exit(1)

    out = subprocess.run(["scripts/src/chartprreview/verify-report.sh", "results", report_path], capture_output=True)
    r = out.stdout.decode("utf-8")
    print(r)
    report = json.loads(r)
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error analysing the report:", err)
        sys.exit(1)

    failed = report["failed"]
    passed = report["passed"]
    if failed > 0:
        print("Report has failed.")
        print(f"Number of checks passed: {passed}\nNUmber of checks failed: {failed}")
        print("Error message:")
        for m in report["message"]:
            print(m)
        sys.exit(1)

def generate_and_verify_report(category, organization, chart, version):
    src = os.path.join("charts", category, organization, chart, version, "src")
    out = subprocess.run(["helm", "package", src], capture_output=True)
    stdout = out.stdout.decode("utf-8")
    print(stdout)
    print(out.stderr.decode("utf-8"))
    dn = os.path.dirname(stdout.split(":")[1].strip())
    fn = os.path.basename(stdout.split(":")[1].strip())
    out = subprocess.run(["docker", "run", "-v", dn+":/charts:z", "--rm", "quay.io/redhat-certification/chart-verifier:latest", "verify", os.path.join("/charts", fn)], capture_output=True)
    stdout = out.stdout.decode("utf-8")
    stderr = out.stderr.decode("utf-8")
    report_path = os.path.join(dn, "report.yaml")
    fd = open(report_path, "w")
    fd.write(stderr)
    fd.close()

    data = open(report_path).read()
    return report_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--verify-user", dest="username", type=str, required=True,
                                        help="check if the user can update the chart")
    parser.add_argument("-n", "--pr-number", dest="number", type=str, required=True,
                                        help="current pull request number")
    args = parser.parse_args()
    category, organization, chart, version = get_modified_charts(args.number)
    verify_user(args.username, category, organization, chart)
    check_owners_file_against_directory_structure(args.username, category, organization, chart)
    report = os.path.join("charts", category, organization, chart, version, "report.yaml")
    if os.path.exists(report):
        print("Report exists: ", report)
        report_path = verify_signature(category, organization, chart, version)
    else:
        print("Report does not exist: ", report)
        report_path = generate_and_verify_report(category, organization, chart, version)

    check_report_success(report_path)
