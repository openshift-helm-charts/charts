import argparse
import shutil
import os
import sys
import re
import subprocess
import datetime
import tempfile
from datetime import datetime, timezone
import json

import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def get_modified_charts():
    commit = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], capture_output=True)
    print(commit.stdout.decode("utf-8"))
    print(commit.stderr.decode("utf-8"))
    commit_hash = commit.stdout.strip()
    files = subprocess.run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash], capture_output=True)
    print(files.stdout.decode("utf-8"))
    print(files.stderr.decode("utf-8"))
    pattern = re.compile("charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/.*")
    for line in files.stdout.decode("utf-8").split('\n'):
        m = pattern.match(line)
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version
    print("No modified files found.")
    sys.exit(0)

def check_chart_source_or_tarball_exists(category, organization, chart, version):
    src = os.path.join("charts", category, organization, chart, version, "src")
    if os.path.exists(src):
        return True, False

    tarball = os.path.join("charts", category, organization, chart, version, f"{chart}-{version}.tgz")
    if os.path.exists(tarball):
        return False, True

    return False, False

def check_report_exists(category, organization, chart, version):
    report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    return os.path.exists(report_path), report_path

def generate_report(chart_file_name):
    cwd = os.getcwd()
    out = subprocess.run(["docker", "run", "-v", cwd+":/charts:z", "--rm", "quay.io/redhat-certification/chart-verifier:latest", "verify", os.path.join("/charts", chart_file_name)], capture_output=True)
    stderr = out.stderr.decode("utf-8")
    report_path = os.path.join(cwd, "report.yaml")
    with open(report_path, "w") as fd:
        fd.write(stderr)
    return report_path

def prepare_chart_source_for_release(category, organization, chart, version):
    path = os.path.join("charts", category, organization, chart, version, "src")
    out = subprocess.run(["helm", "package", path], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    chart_file_name = f"{chart}-{version}.tgz"
    new_chart_file_name = f"{organization}-{chart}-{version}.tgz"
    try:
        os.remove(os.path.join(".cr-release-packages", new_chart_file_name))
    except FileNotFoundError:
        pass
    shutil.copy(f"{chart}-{version}.tgz" , f".cr-release-packages/{new_chart_file_name}")

def prepare_chart_tarball_for_release(category, organization, chart, version):
    chart_file_name = f"{chart}-{version}.tgz"
    new_chart_file_name = f"{organization}-{chart}-{version}.tgz"
    path = os.path.join("charts", category, organization, chart, version, chart_file_name)
    try:
        os.remove(os.path.join(".cr-release-packages", new_chart_file_name))
    except FileNotFoundError:
        pass
    shutil.copy(path, f".cr-release-packages/{new_chart_file_name}")
    shutil.copy(path, chart_file_name)

def push_chart_release(repository, organization, branch):
    org, repo = repository.split("/")
    token = os.environ.get("GITHUB_TOKEN")
    print("[INFO] Upload chart using the chart-releaser")
    out = subprocess.run(["cr", "upload", "-o", org, "-r", repo, "--release-name-template", f"{organization}-"+"{{ .Name }}-{{ .Version }}", "-t", token], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

def create_worktree_for_index(branch):
    dr = tempfile.mkdtemp(prefix="crm-")
    upstream = os.environ["GITHUB_SERVER_URL"] + "/" + os.environ["GITHUB_REPOSITORY"]
    out = subprocess.run(["git", "remote", "add", "upstream", upstream], capture_output=True)
    print(out.stdout.decode("utf-8"))
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Adding upstream remote failed:", err, "branch", branch, "upstream", upstream)
    out = subprocess.run(["git", "fetch", "upstream"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Fetching upstream remote failed:", err, "branch", branch, "upstream", upstream)
    out = subprocess.run(["git", "worktree", "add", "--detach", dr, f"upstream/{branch}"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Creating worktree failed:", err, "branch", branch, "directory", dr)
    return dr

def create_index_from_chart(indexdir, repository, branch, category, organization, chart, version, chart_url):
    path = os.path.join("charts", category, organization, chart, version)
    chart_file_name = f"{chart}-{version}.tgz"
    out = subprocess.run(["helm", "show", "chart", os.path.join(".cr-release-packages", chart_file_name)], capture_output=True)
    p = out.stdout.decode("utf-8")
    print(p)
    print(out.stderr.decode("utf-8"))
    crt = yaml.load(p, Loader=Loader)
    return crt

def create_index_from_report(category, report_path):
    out = subprocess.run(["scripts/src/chartprreview/verify-report.sh", "annotations", report_path], capture_output=True)
    r = out.stdout.decode("utf-8")
    print("annotation",r)
    annotations = json.loads(r)
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error extracting annotations from the report:", err)
        sys.exit(1)

    print("category:", category)
    if category == "partners":
        annotations["helm-chart.openshift.io/providerType"] = "partner"
    else:
        annotations["helm-chart.openshift.io/providerType"] = category

    report = yaml.load(open(report_path), Loader=Loader)
    chart_url = report["metadata"]["tool"]['chart-uri']
    chart_entry = report["metadata"]["chart"]
    chart_entry["annotations"] = chart_entry["annotations"] | annotations
    return chart_entry, chart_url

def update_index_and_push(indexdir, repository, branch, category, organization, chart, version, chart_url, chart_entry):
    token = os.environ.get("GITHUB_TOKEN")
    print("Downloading index.yaml")
    r = requests.get(f'https://raw.githubusercontent.com/{repository}/{branch}/index.yaml')
    original_etag = r.headers.get('etag')
    now = datetime.now(timezone.utc).astimezone().isoformat()
    if r.status_code == 200:
        data = yaml.load(r.text, Loader=Loader)
        data["generated"] = now
    else:
        data = {"apiVersion": "v1",
            "generated": now,
            "entries": {}}

    print("[INFO] Updating the chart entry with new version")
    crtentries = []
    entry_name = f"{organization}-{chart}"
    d = data["entries"].get(entry_name, [])
    for v in d:
        if v["version"] == version:
            continue
        crtentries.append(v)

    chart_entry["urls"] = [chart_url]
    chart_entry["annotations"]["helm-chart.openshift.io/submissionTimestamp"] = now
    crtentries.append(chart_entry)
    data["entries"][entry_name] = crtentries

    print("[INFO] Add and commit changes to git")
    out = yaml.dump(data, Dumper=Dumper)
    with open(os.path.join(indexdir, "index.yaml"), "w") as fd:
        fd.write(out)
    out = subprocess.run(["git", "add", os.path.join(indexdir, "index.yaml")], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error adding index.yaml to git staging area", "index directory", indexdir, "branch", branch)
    out = subprocess.run(["git", "commit", indexdir, "-m", "Update index.html"], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error committing index.yaml", "index directory", indexdir, "branch", branch)
    r = requests.head(f'https://raw.githubusercontent.com/{repository}/{branch}/index.yaml')
    etag = r.headers.get('etag')
    if original_etag and etag and (original_etag != etag):
        print("index.html not updated. ETag mismatch.", "original ETag", original_etag, "new ETag", etag, "index directory", indexdir, "branch", branch)
        sys.exit(1)
    out = subprocess.run(["git", "push", f"https://x-access-token:{token}@github.com/{repository}", f"HEAD:refs/heads/{branch}", "-f"], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    if out.returncode:
        print("index.html not updated. Push failed.", "index directory", indexdir, "branch", branch)
        sys.exit(1)


def update_chart_annotation(category, organization, chart_file_name, chart, report_path):
    dr = tempfile.mkdtemp(prefix="annotations-")
    out = subprocess.run(["scripts/src/chartprreview/verify-report.sh", "annotations", report_path], capture_output=True)
    r = out.stdout.decode("utf-8")
    print("annotation",r)
    annotations = json.loads(r)
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error extracting annotations from the report:", err)
        sys.exit(1)

    print("category:", category)
    if category == "partners":
        annotations["helm-chart.openshift.io/providerType"] = "partner"
    else:
        annotations["helm-chart.openshift.io/providerType"] = category

    if "helm-chart.openshift.io/provider" not in annotations:
        data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
        out = yaml.load(data, Loader=Loader)
        vendor_name = out["vendor"]["name"]
        annotations["helm-chart.openshift.io/provider"] = vendor_name

    out = subprocess.run(["tar", "zxvf", os.path.join(".cr-release-packages", f"{organization}-{chart_file_name}"), "-C", dr], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    fd = open(os.path.join(dr, chart, "Chart.yaml"))
    data = yaml.load(fd, Loader=Loader)
    data["annotations"] = annotations
    out = yaml.dump(data, Dumper=Dumper)
    with open(os.path.join(dr, chart, "Chart.yaml"), "w") as fd:
        fd.write(out)

    out = subprocess.run(["helm", "package", os.path.join(dr, chart)], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    try:
        os.remove(os.path.join(".cr-release-packages", chart_file_name))
    except FileNotFoundError:
        pass

    shutil.move(chart_file_name, ".cr-release-packages")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--index-branch", dest="branch", type=str, required=True,
                                        help="index branch")
    parser.add_argument("-r", "--repository", dest="repository", type=str, required=True,
                                        help="Git Repository")
    args = parser.parse_args()
    branch = args.branch.split("/")[-1]
    category, organization, chart, version = get_modified_charts()
    chart_source_exists, chart_tarball_exists = check_chart_source_or_tarball_exists(category, organization, chart, version)

    print("[INFO] Creating Git worktree for index branch")
    indexdir = create_worktree_for_index(branch)

    if chart_source_exists or chart_tarball_exists:
        if chart_source_exists:
            prepare_chart_source_for_release(category, organization, chart, version)
        if chart_tarball_exists:
            prepare_chart_tarball_for_release(category, organization, chart, version)

        print("[INFO] Publish chart release to GitHub")
        push_chart_release(args.repository, organization, branch)

        print("[INFO] Check if report exist as part of the commit")
        report_exists, report_path = check_report_exists(category, organization, chart, version)
        chart_file_name = f"{chart}-{version}.tgz"
        if report_exists:
            shutil.copy(report_path, "report.yaml")
        else:
            print(f"::set-output name=tag::{organization}-{chart}-{version}")
            print("[INFO] Genereate report")
            report_path = generate_report(chart_file_name)

        print("[INFO] Updating chart annotation")
        update_chart_annotation(category, organization, chart_file_name, chart, report_path)
        chart_url = f"https://github.com/{args.repository}/releases/download/{organization}-{chart}-{version}/{organization}-{chart}-{version}.tgz"

        print("[INFO] Creating index from chart")
        chart_entry = create_index_from_chart(indexdir, args.repository, branch, category, organization, chart, version, chart_url)
    else:
        report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
        print("[INFO] Creating index from report")
        chart_entry, chart_url = create_index_from_report(category, report_path)

    update_index_and_push(indexdir, args.repository, branch, category, organization, chart, version, chart_url, chart_entry)
