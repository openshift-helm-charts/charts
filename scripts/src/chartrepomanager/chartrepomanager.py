import argparse
import shutil
import os
import sys
import re
import subprocess
import tempfile
from datetime import datetime, timezone
import hashlib
import urllib.parse

import semver
import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

sys.path.append('../')
from report import report_info

def get_modified_charts(api_url):
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(files_api_url, headers=headers)
    pattern = re.compile(r"charts/(\w+)/([\w-]+)/([\w-]+)/([\w\.]+)/.*")
    for f in r.json():
        m = pattern.match(f["filename"])
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version

    print("No modified files found.")
    sys.exit(0)

def get_current_commit_sha():
    cwd = os.getcwd()
    os.chdir("..")
    subprocess.run(["git", "pull", "--all", "--force"], capture_output=True)
    commit = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], capture_output=True)
    print(commit.stdout.decode("utf-8"))
    print(commit.stderr.decode("utf-8"))
    commit_hash = commit.stdout.strip()
    print("Current commit sha:", commit_hash)
    os.chdir(cwd)
    return commit_hash

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
    report_content = urllib.parse.unquote(os.environ.get("REPORT_CONTENT"))
    print("[INFO] Report content:")
    print(report_content)
    report_path = os.path.join(cwd, "report.yaml")
    with open(report_path, "w") as fd:
        fd.write(report_content)
    return report_path

def prepare_chart_source_for_release(category, organization, chart, version):
    print("[INFO] prepare chart source for release. %s, %s, %s, %s" % (category, organization, chart, version))
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
    print("[INFO] prepare chart tarball for release. %s, %s, %s, %s" % (category, organization, chart, version))
    chart_file_name = f"{chart}-{version}.tgz"
    new_chart_file_name = f"{organization}-{chart}-{version}.tgz"
    path = os.path.join("charts", category, organization, chart, version, chart_file_name)
    try:
        os.remove(os.path.join(".cr-release-packages", new_chart_file_name))
    except FileNotFoundError:
        pass
    shutil.copy(path, f".cr-release-packages/{new_chart_file_name}")
    shutil.copy(path, chart_file_name)

def push_chart_release(repository, organization, commit_hash):
    print("[INFO]push chart release. %s, %s, %s " % (repository, organization, commit_hash))
    org, repo = repository.split("/")
    token = os.environ.get("GITHUB_TOKEN")
    print("[INFO] Upload chart using the chart-releaser")
    release_name_template = f"{organization}-"+"{{ .Name }}-{{ .Version }}"
    if os.environ.get('TRIGGERED_BY_TEST') == 'true':
        pr_number = os.environ.get("PR_NUMBER")
        release_name_template += f'-test-pr{pr_number}'
    out = subprocess.run(["cr", "upload", "-c", commit_hash, "-o", org, "-r", repo, "--release-name-template", release_name_template, "-t", token], capture_output=True)
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
    print("[INFO] create index from chart. %s, %s, %s, %s, %s" % (category, organization, chart, version, chart_url))
    path = os.path.join("charts", category, organization, chart, version)
    chart_file_name = f"{chart}-{version}.tgz"
    out = subprocess.run(["helm", "show", "chart", os.path.join(".cr-release-packages", chart_file_name)], capture_output=True)
    p = out.stdout.decode("utf-8")
    print(p)
    print(out.stderr.decode("utf-8"))
    crt = yaml.load(p, Loader=Loader)
    return crt

def create_index_from_report(category, report_path):
    print("[INFO] create index from report. %s, %s" % (category, report_path))

    annotations = report_info.get_report_annotations(report_path)

    print("category:", category)
    redhat_to_community = bool(os.environ.get("REDHAT_TO_COMMUNITY"))
    if category == "partners":
        annotations["charts.openshift.io/providerType"] = "partner"
    elif category == "redhat" and redhat_to_community:
        annotations["charts.openshift.io/providerType"] = "community"
    else:
        annotations["charts.openshift.io/providerType"] = category

    chart_url = report_info.get_report_chart_url(report_path)
    chart_entry = report_info.get_report_chart(report_path)
    if "annotations" in chart_entry:
        annotations = chart_entry["annotations"] | annotations

    chart_entry["annotations"] = annotations


    digests = report_info.get_report_digests(report_path)
    if "package" in digests:
        chart_entry["digest"] = digests["package"]

    return chart_entry, chart_url


def set_package_digest(chart_entry):
    print("[INFO] set package digests.")

    url = chart_entry["urls"][0]
    head = requests.head(url, allow_redirects=True)
    target_digest = ""
    if head.status_code == 200:
        response = requests.get(url, allow_redirects=True)
        target_digest = hashlib.sha256(response.content).hexdigest()

    pkg_digest = ""
    if "digest" in chart_entry:
        pkg_digest = chart_entry["digest"]
    
    if target_digest:
        if not pkg_digest:
            # Digest was computed but not passed
            chart_entry["digest"] = target_digest
        elif pkg_digest != target_digest:
            # Digest was passed and computed but differ
            raise Exception("Found an integrity issue. SHA256 digest passed does not match SHA256 digest computed.")
    elif not pkg_digest:
        # Digest was not passed and could not be computed
        raise Exception("Was unable to compute SHA256 digest, please ensure chart url points to a chart package.")



def update_index_and_push(indexdir, repository, branch, category, organization, chart, version, chart_url, chart_entry, pr_number):
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
    entry_name = os.environ.get("CHART_ENTRY_NAME")
    if not entry_name:
        print("[ERROR] Internal error: missing chart entry name")
        sys.exit(1)
    d = data["entries"].get(entry_name, [])
    for v in d:
        if v["version"] == version:
            continue
        crtentries.append(v)

    chart_entry["urls"] = [chart_url]
    set_package_digest(chart_entry)
    chart_entry["annotations"]["charts.openshift.io/submissionTimestamp"] = now
    crtentries.append(chart_entry)
    data["entries"][entry_name] = crtentries

    print("[INFO] Add and commit changes to git")
    out = yaml.dump(data, Dumper=Dumper)
    print("index.yaml content:\n", out)
    with open(os.path.join(indexdir, "index.yaml"), "w") as fd:
        fd.write(out)
    old_cwd = os.getcwd()
    os.chdir(indexdir)
    out = subprocess.run(["git", "status"], cwd=indexdir, capture_output=True)
    print("Git status:")
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    out = subprocess.run(["git", "add", os.path.join(indexdir, "index.yaml")], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error adding index.yaml to git staging area", "index directory", indexdir, "branch", branch)
    out = subprocess.run(["git", "status"], cwd=indexdir, capture_output=True)
    print("Git status:")
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    out = subprocess.run(["git", "commit",  "-m", f"{organization}-{chart}-{version} index.yaml (#{pr_number})"], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error committing index.yaml", "index directory", indexdir, "branch", branch, "error:", err)
    r = requests.head(f'https://raw.githubusercontent.com/{repository}/{branch}/index.yaml')
    etag = r.headers.get('etag')
    if original_etag and etag and (original_etag != etag):
        print("index.html not updated. ETag mismatch.", "original ETag", original_etag, "new ETag", etag, "index directory", indexdir, "branch", branch)
        sys.exit(1)
    out = subprocess.run(["git", "status"], cwd=indexdir, capture_output=True)
    print("Git status:")
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    out = subprocess.run(["git", "push", f"https://x-access-token:{token}@github.com/{repository}", f"HEAD:refs/heads/{branch}", "-f"], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    if out.returncode:
        print("index.html not updated. Push failed.", "index directory", indexdir, "branch", branch)
        sys.exit(1)
    os.chdir(old_cwd)


def update_chart_annotation(category, organization, chart_file_name, chart, report_path):
    print("[INFO] Update chart annotation. %s, %s, %s, %s" % (category, organization, chart_file_name, chart))
    dr = tempfile.mkdtemp(prefix="annotations-")

    annotations = report_info.get_report_annotations(report_path)

    print("category:", category)
    redhat_to_community = bool(os.environ.get("REDHAT_TO_COMMUNITY"))
    if category == "partners":
        annotations["charts.openshift.io/providerType"] = "partner"
    elif category == "redhat" and redhat_to_community:
        annotations["charts.openshift.io/providerType"] = "community"
    else:
        annotations["charts.openshift.io/providerType"] = category

    if "charts.openshift.io/provider" not in annotations:
        data = open(os.path.join("charts", category, organization, chart, "OWNERS")).read()
        out = yaml.load(data, Loader=Loader)
        vendor_name = out["vendor"]["name"]
        annotations["charts.openshift.io/provider"] = vendor_name

    if "charts.openshift.io/certifiedOpenShiftVersions" in annotations:
        full_version = annotations["charts.openshift.io/certifiedOpenShiftVersions"]
        if full_version == "N/A":
            annotations["charts.openshift.io/certifiedOpenShiftVersions"] = "N/A"
        else:
            ver = semver.VersionInfo.parse(full_version)
            annotations["charts.openshift.io/certifiedOpenShiftVersions"] = f"{ver.major}.{ver.minor}"

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
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    parser.add_argument("-n", "--pr-number", dest="pr_number", type=str, required=True,
                                        help="current pull request number")
    args = parser.parse_args()
    branch = args.branch.split("/")[-1]
    category, organization, chart, version = get_modified_charts(args.api_url)
    chart_source_exists, chart_tarball_exists = check_chart_source_or_tarball_exists(category, organization, chart, version)

    print("[INFO] Creating Git worktree for index branch")
    indexdir = create_worktree_for_index(branch)

    print("[INFO] Report Content : ", os.environ.get("REPORT_CONTENT"))
    if chart_source_exists or chart_tarball_exists:
        if chart_source_exists:
            prepare_chart_source_for_release(category, organization, chart, version)
        if chart_tarball_exists:
            prepare_chart_tarball_for_release(category, organization, chart, version)

        commit_hash = get_current_commit_sha()
        print("[INFO] Publish chart release to GitHub")
        push_chart_release(args.repository, organization, commit_hash)

        print("[INFO] Check if report exist as part of the commit")
        report_exists, report_path = check_report_exists(category, organization, chart, version)
        chart_file_name = f"{chart}-{version}.tgz"
        if report_exists:
            shutil.copy(report_path, "report.yaml")
        else:
            tag = os.environ.get("CHART_NAME_WITH_VERSION")
            if not tag:
                print("[ERROR] Internal error: missing chart name with version (tag)")
                sys.exit(1)
            print(f"::set-output name=tag::{tag}")
            print("[INFO] Genereate report")
            report_path = generate_report(chart_file_name)

        print("[INFO] Updating chart annotation")
        update_chart_annotation(category, organization, chart_file_name, chart, report_path)
        chart_url = f"https://github.com/{args.repository}/releases/download/{organization}-{chart}-{version}/{organization}-{chart}-{version}.tgz"
        if os.environ.get('TRIGGERED_BY_TEST') == 'true':
            pr_number = os.environ.get("PR_NUMBER")
            chart_url = f"https://github.com/{args.repository}/releases/download/{organization}-{chart}-{version}-test-pr{pr_number}/{organization}-{chart}-{version}.tgz"
        print("[INFO] Helm package was released at %s" % chart_url)
        print("[INFO] Creating index from chart")
        chart_entry = create_index_from_chart(indexdir, args.repository, branch, category, organization, chart, version, chart_url)
    else:
        report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
        print("[INFO] Creating index from report")
        chart_entry, chart_url = create_index_from_report(category, report_path)

    update_index_and_push(indexdir, args.repository, branch, category, organization, chart, version, chart_url, chart_entry, args.pr_number)
