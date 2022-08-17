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

sys.path.append('../')
from owners import owners_file
from report import verifier_report

ALLOW_CI_CHANGES = "allow/ci-changes"
TYPE_MATCH_EXPRESSION = "(partners|redhat|community)"

def check_provider_delivery(report_in_pr,num_files_in_pr,report_file_match):

    print(f"[INFO] report in PR {report_in_pr}")
    print(f"[INFO] num files in PR {num_files_in_pr}")
    
    category, organization, chart, version = report_file_match.groups()

    print(f"read owners file : {category}/{organization}/{chart}" )
    found_owners,owner_data = owners_file.get_owner_data(category, organization, chart)

    if found_owners:
        owner_provider_delivery = owners_file.get_provider_delivery(owner_data)
        print(f"[INFO] providerDelivery from OWNERS : {owner_provider_delivery}")
    else:
        msg = "[ERROR] OWNERS file was not found."
        print(msg)
        print(f"::set-output name=owners-error-message::{msg}")
        sys.exit(1)

    if report_in_pr:
        report_file_path = os.path.join("pr-branch","charts", category, organization, chart, version, "report.yaml")
        print(f"read report file : {report_file_path}" )
        found_report,report_data = verifier_report.get_report_data(report_file_path)

        if found_report:
            report_provider_delivery = verifier_report.get_provider_delivery(report_data)
            print(f"[INFO] providerDelivery from report : {report_provider_delivery}")
        else:
            msg = f"[ERROR] Failed tp open report: {report_file_path}."
            print(msg)
            print(f"::set-output name=pr-content-error-message::{msg}")
            sys.exit(1)

    provider_delivery = False
    if report_in_pr and num_files_in_pr > 1:
        if report_provider_delivery or owner_provider_delivery:
            msg = f"[ERROR] OWNERS file and/or report indicate provider controlled delivery but pull request is not report only."
            print(msg)
            print(f"::set-output name=pr-content-error-message::{msg}")
            sys.exit(1)
    elif report_in_pr:
        if report_provider_delivery and owner_provider_delivery:
            if verifier_report.get_package_digest(report_data):
                provider_delivery = True
            else:
                msg = f"[ERROR] Provider delivery control requires a package digest in the report."
                print(msg)
                print(f"::set-output name=pr-content-error-message::{msg}")
                sys.exit(1)
        elif report_provider_delivery:
            msg = f"[ERROR] Report indicates provider controlled delivery but OWNERS file does not."
            print(msg)
            print(f"::set-output name=pr-content-error-message::{msg}")
            sys.exit(1)
        elif owner_provider_delivery:
            msg = f"[ERROR] OWNERS file indicates provider controlled delivery but report does not."
            print(msg)
            print(f"::set-output name=pr-content-error-message::{msg}")
            sys.exit(1)

    if provider_delivery:
        print(f"[INFO] providerDelivery is a go")
        print(f"::set-output name=providerDelivery::True")
    else:
        print(f"::set-output name=providerDelivery::False")
        print(f"[INFO] providerDelivery is a no-go")

def get_file_match_compiled_patterns():
    """Return a tuple of patterns, where the first can be used to match any file in a chart PR 
    and the second can be used to match a valid report file within a chart PR. The patterns
    match based on the relative path of a file to the base repository
    
    Both patterns capture chart type, chart vendor, chart name and chart version from the file path..
    
    Examples of valid file paths are:
    
    charts/partners/hashicorp/vault/0.20.0/<file>
    charts/partners/hashicorp/vault/0.20.0//report.yaml
    """

    pattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/([\w\.-]+)/.*")
    reportpattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/([\w\.-]+)/report.yaml")

    return pattern,reportpattern


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
    pattern,reportpattern = get_file_match_compiled_patterns()
    page_number = 1
    max_page_size,page_size = 100,100
    matches_found = 0
    report_found = False
    none_chart_files = {}
    file_count = 0

    while page_size == max_page_size:

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        print(f"Query files : {files_api_query}")
        r = requests.get(files_api_query,headers=headers)
        files = r.json()
        page_size = len(files)
        file_count += page_size
        page_number += 1

        for f in files:
            file_path = f["filename"]
            match = pattern.match(file_path)
            if not match:
                file_name = os.path.basename(file_path)
                none_chart_files[file_name] = file_path
            else:
                matches_found += 1
                if reportpattern.match(file_path):
                    print("[INFO] Report found")
                    print("::set-output name=report-exists::true")
                    report_found = True
                if matches_found == 1:
                    pattern_match = match
                elif pattern_match.groups() != match.groups():
                    msg = "[ERROR] A PR must contain only one chart. Current PR includes files for multiple charts."
                    print(msg)
                    print(f"::set-output name=pr-content-error-message::{msg}")
                    exit(1)
    
    if none_chart_files:
        if file_count > 1 or "OWNERS" not in none_chart_files: #OWNERS not present or preset but not the only file
            example_file = list(none_chart_files.values())[0]
            msg = f"[ERROR] PR includes one or more files not related to charts, e.g., {example_file}"
            print(msg)
            print(f"::set-output name=pr-content-error-message::{msg}")

        if "OWNERS" in none_chart_files:
            file_path = none_chart_files["OWNERS"]
            path_parts = file_path.split("/")
            category = path_parts[1] # Second after charts
            if category == "partners":
                msg = "[ERROR] OWNERS file should never be set directly by partners. See certification docs."
                print(msg)
                print(f"::set-output name=owners-error-message::{msg}")
            elif matches_found>0: # There is a mix of chart and non-chart files including OWNERS
                msg = "[ERROR] Send OWNERS file by itself in a separate PR."
                print(msg)
                print(f"::set-output name=owners-error-message::{msg}")
            elif file_count == 1: # OWNERS file is the only file in PR
                msg = "[INFO] OWNERS file changes require manual review by maintainers."
                print(msg)
                print(f"::set-output name=owners-error-message::{msg}") 
                
        sys.exit(1)

    check_provider_delivery(report_found,matches_found,pattern_match)

    if matches_found>0:
        category, organization, chart, version = pattern_match.groups()
        print(f"::set-output name=category::{'partner' if category == 'partners' else category}")
        print(f"::set-output name=organization::{organization}")
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
                print(f"::set-output name=pr-content-error-message::{msg}")
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
            print(f"::set-output name=pr-content-error-message::{msg}")
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
