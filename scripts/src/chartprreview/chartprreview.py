import re
import os
import sys
import argparse
import subprocess
import json
import hashlib
import tempfile

import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def get_modified_charts(api_url):
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(files_api_url, headers=headers)
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
    publickey = out.get('publicPgpKey')
    if not publickey:
        return
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

def match_checksum(category, organization, chart, version):
    submitted_report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    submitted_report = yaml.load(open(submitted_report_path), Loader=Loader)
    submitted_digest = submitted_report["metadata"]["tool"]["digest"]

    generated_report_path = "report.yaml"
    generated_report = yaml.load(open(generated_report_path), Loader=Loader)
    generated_digest = generated_report["metadata"]["tool"]["digest"]

    if  submitted_digest != generated_digest:
        print("Digest is not matching:", submitted_digest, generated_digest)
        sys.exit(1)

def check_url(report_path):
    report = yaml.load(open(report_path), Loader=Loader)
    chart_url = report["metadata"]["tool"]['chart-uri']

    try:
        requests.head(chart_url)
    except requests.exceptions.InvalidSchema as err:
        print("Invalid schema:", chart_url)
        print(err)
        sys.exit(1)
    except requests.exceptions.InvalidURL as err:
        print("Invalid URL:", chart_url)
        print(err)
        sys.exit(1)
    except requests.exceptions.MissingSchema as err:
        print("Missing schema in URL:", chart_url)
        print(err)
        sys.exit(1)

def match_name_and_version(category, organization, chart, version):
    submitted_report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    if os.path.exists(submitted_report_path):
        submitted_report = yaml.load(open(submitted_report_path), Loader=Loader)
        submitted_report_chart_name = submitted_report["metadata"]["chart"]["name"]
        submitted_report_chart_version = submitted_report["metadata"]["chart"]["version"]

        if submitted_report_chart_name != chart:
            print("Chart name is not matching against the value in the directory structure:", submitted_report_chart_name, "vs.", chart)
            sys.exit(1)

        if submitted_report_chart_version != version:
            print("Chart version is not matching against the value in the directory structure:", submitted_report_chart_version, "vs.", version)
            sys.exit(1)

        if os.path.exists("report.yaml"):
            report = yaml.load(open("report.yaml"), Loader=Loader)
            report_chart_name = report["metadata"]["chart"]["name"]
            report_chart_version = report["metadata"]["chart"]["version"]

            if submitted_report_chart_name != report_chart_name:
                print("Chart name is not matching against the value in the submitted report:", submitted_report_chart_name, "vs.", report_chart_name)
                sys.exit(1)

            if submitted_report_chart_version != report_chart_version:
                print("Chart version is not matching against the value in the submitted report:", submitted_report_chart_version, "vs.", report_chart_version)
                sys.exit(1)
    else:
        report = yaml.load(open(report_path), Loader=Loader)
        report_chart_name = report["metadata"]["chart"]["name"]
        report_chart_version = report["metadata"]["chart"]["version"]

        if report_chart_name != chart:
            print("Chart name is not matching against the value in the directory structure:", report_chart_name, "vs.", chart)
            sys.exit(1)

        if report_chart_version != version:
            print("Chart version is not matching against the value in the directory structure:", report_chart_version, "vs.", version)
            sys.exit(1)

def check_report_success(report_path, version):
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

    report_version = out["metadata"]["chart"]["version"]
    if report_version != version:
        print(f"Chart Version '{report_version}' doesn't match the version in the directory path: '{version}'")
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

def generate_verify_report(category, organization, chart, version):
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
        print("Both chart source and tar ball should not exist.")
        sys.exit(1)
    if not os.path.exists(report_path):
        if not src_exists and not tar_exists:
            print("Either chart source or tar ball should exist.")
            sys.exit(1)
    if src_exists:
        if os.path.exists(report_path):
            out = subprocess.run(["docker", "run", "-v", src+":/charts:z", "--rm", "quay.io/redhat-certification/chart-verifier:latest", "verify", "-e", "has-readme", "/charts"], capture_output=True)
        else:
            out = subprocess.run(["docker", "run", "-v", src+":/charts:z", "--rm", "quay.io/redhat-certification/chart-verifier:latest", "verify", "/charts"], capture_output=True)
    elif tar_exists:
        dn = os.path.join(os.getcwd(), "charts", category, organization, chart, version)
        if os.path.exists(report_path):
            out = subprocess.run(["docker", "run", "-v", dn+":/charts:z", "--rm", "quay.io/redhat-certification/chart-verifier:latest", "verify", "-e", "has-readme", f"/charts/{chart}-{version}.tgz"], capture_output=True)
        else:
            out = subprocess.run(["docker", "run", "-v", dn+":/charts:z", "--rm", "quay.io/redhat-certification/chart-verifier:latest", "verify", f"/charts/{chart}-{version}.tgz"], capture_output=True)
    else:
        return

    stderr = out.stderr.decode("utf-8")
    report_path = "report.yaml"
    print("report:", stderr)
    with open(report_path, "w") as fd:
        fd.write(stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--verify-user", dest="username", type=str, required=True,
                                        help="check if the user can update the chart")
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    args = parser.parse_args()
    category, organization, chart, version = get_modified_charts(args.api_url)
    verify_user(args.username, category, organization, chart)
    check_owners_file_against_directory_structure(args.username, category, organization, chart)
    submitted_report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    generate_verify_report(category, organization, chart, version)
    if os.path.exists(submitted_report_path):
        print("Report exists: ", submitted_report_path)
        verify_signature(category, organization, chart, version)
        report_path = submitted_report_path
        if os.path.exists("report.yaml"):
            match_checksum(category, organization, chart, version)
        else:
            check_url(report_path)
    else:
        print("Report does not exist: ", submitted_report_path)
        report_path = "report.yaml"

    match_name_and_version(category, organization, chart, version)
    check_report_success(report_path, version)
