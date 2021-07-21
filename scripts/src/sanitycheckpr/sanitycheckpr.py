import re
import os
import sys
import argparse

import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


ALLOW_CI_CHANGES = "allow/ci-changes"
TYPE_MATCH_EXPRESSION = "(partners|redhat|community)"

def ensure_only_chart_is_modified(api_url, repository, branch):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(api_url, headers=headers)
    for label in r.json()["labels"]:
        if label["name"] == ALLOW_CI_CHANGES:
            return
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(files_api_url, headers=headers)
    pattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/([\w\.-]+)/.*")
    reportpattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/([\w\.-]+)/report.yaml")
    page_number = 1
    max_page_size,page_size = 100,100

    while page_size == max_page_size:

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        print(f"Query files : {files_api_query}")
        r = requests.get(files_api_query,headers=headers)
        files = r.json()
        page_size = len(files)
        page_number += 1

        match_found = False
        for f in files:
            filename = f["filename"]
            match = pattern.match(filename)
            if not match:
                msg = f"[ERROR] PR should only modify chart related files: {filename}"
                print(msg)
                print(f"::set-output name=sanity-error-message::{msg}")
                sys.exit(1)
            else:
                if reportpattern.match(filename):
                    print("[INFO] Report found")
                    print("::set-output name=report-exists::true")
                if not match_found:
                    pattern_match = match
                    match_found = True
                elif pattern_match.groups() != match.groups():
                    msg = f"[ERROR] PR must only include one chart"
                    print(msg)
                    print(f"::set-output name=sanity-error-message::{msg}")
                    sys.exit(1)


    if match_found:
        category, organization, chart, version = pattern_match.groups()
        print(f"::set-output name=category::{'partner' if category == 'partners' else category}")
        print("Downloading index.yaml", category, organization, chart, version)
        r = requests.get(f'https://raw.githubusercontent.com/{repository}/{branch}/index.yaml')
        if r.status_code == 200:
            data = yaml.load(r.text, Loader=Loader)
        else:
            data = {"apiVersion": "v1",
                "entries": {}}

        crtentries = []
        entry_name = f"{organization}-{chart}"
        d = data["entries"].get(entry_name, [])
        print(f"::set-output name=chart-entry-name::{entry_name}")
        for v in d:
            if v["version"] == version:
                msg = f"[ERROR] Helm chart release already exists in the index.yaml: {version}"
                print(msg)
                print(f"::set-output name=sanity-error-message::{msg}")
                sys.exit(1)

        tag_name = f"{organization}-{chart}-{version}"
        print(f"::set-output name=chart-name-with-version::{tag_name}")
        tag_api = f"https://api.github.com/repos/{repository}/git/ref/tags/{tag_name}"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        print(f"[INFO] checking tag: {tag_api}")
        r = requests.head(tag_api, headers=headers)
        if r.status_code == 200:
            msg = f"[ERROR] Helm chart release already exists in the GitHub Release/Tag: {tag_name}"
            print(msg)
            print(f"::set-output name=sanity-error-message::{msg}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--index-branch", dest="branch", type=str, required=True,
                                        help="index branch")
    parser.add_argument("-r", "--repository", dest="repository", type=str, required=True,
                                        help="Git Repository")
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    args = parser.parse_args()
    branch = args.branch.split("/")[-1]
    ensure_only_chart_is_modified(args.api_url, args.repository, branch)


if __name__ == "__main__":
    main()
