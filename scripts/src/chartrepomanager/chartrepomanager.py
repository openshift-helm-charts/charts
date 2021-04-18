import argparse
import shutil
import os
import sys
import re
import subprocess
import datetime
import tempfile
from datetime import datetime, timezone

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
    count = 0
    for line in files.stdout.decode("utf-8").split('\n'):
        m = pattern.match(line)
        if m:
            category, organization, chart, version = m.groups()
            return category, organization, chart, version
    print("No modified files out.")
    sys.exit(0)

def prepare_chart_for_release(category, organization, chart, version):
    path = os.path.join("charts", category, organization, chart, version, "src")
    out = subprocess.run(["helm", "package", path], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    p = out.stdout.decode("utf-8").strip().split(":")[1].strip()
    chartname = os.path.basename(p)
    try:
        os.remove(os.path.join(os.path.dirname(p), ".cr-release-packages", chartname))
    except FileNotFoundError:
        pass
    shutil.move(p, ".cr-release-packages")
    return chartname

def push_chart_release():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        out = subprocess.run(["cr", "upload", "-o", "openshift-helm-charts", "-r", "repo", "-t", token], capture_output=True)
        print(out.stdout.decode("utf-8"))
        print(out.stderr.decode("utf-8"))

def create_worktree_for_index():
    dr = tempfile.mkdtemp(prefix="crm-")
    out = subprocess.run(["git", "worktree", "add", "--detach", dr, "origin/gh-pages"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    return dr

def create_index(indexdir, branch, chartname, category, organization, chart, version):
    path = os.path.join("charts", category, organization, chart, version)
    token = os.environ.get("GITHUB_TOKEN")
    r = requests.get('https://github.com/openshift-helm-charts/charts/raw/gh-pages/index.yaml')
    if r.status_code == 200:
        data = yaml.load(r.text, Loader=Loader)
    else:
        data = {"apiVersion": "v1",
            "generated": datetime.now(timezone.utc).astimezone().isoformat(),
            "entries": {}}
    if os.path.exists(os.path.join(path, "src")):
        out = subprocess.run(["helm", "show", "chart", os.path.join(path, "src")], capture_output=True)
        p = out.stdout.decode("utf-8")
        print(p)
        print(out.stderr.decode("utf-8"))
        crt = yaml.load(p, Loader=Loader)

    crtentries = []
    for v in data["entries"].get(chart, []):
        if v["version"] == version:
            continue
        crtentries.append(v)

    crtentries.append(crt)
    data["entries"][chart] = crtentries

    out = yaml.dump(data, Dumper=Dumper)
    with open(os.path.join(indexdir, "index.yaml"), "w") as fd:
        fd.write(out)
    out = subprocess.run(["git", "add", os.path.join(indexdir, "index.yaml")], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    out = subprocess.run(["git", "commit", indexdir, "-m", "Update index.html"], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))
    out = subprocess.run(["git", "push", f"https://x-access-token:{token}@github.com/openshift-helm-charts/repo", "HEAD:refs/heads/"+branch, "-f"], cwd=indexdir, capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

def update_chart_annotation(chartname):
    out = subprocess.run(["tar", "zxvf", os.path.join(".cr-release-packages", chartname)], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--index-branch", dest="branch", type=str, required=True,
                                        help="index branch")
    args = parser.parse_args()

    category, organization, chart, version = get_modified_charts()
    chartname = prepare_chart_for_release(category, organization, chart, version )
    #push_chart_release()
    #update_chart_annotation(chartname)
    indexdir = create_worktree_for_index()
    create_index(indexdir, args.branch, chartname, category, organization, chart, version)
