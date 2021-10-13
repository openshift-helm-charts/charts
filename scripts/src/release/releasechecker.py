"""
Used by a github action
1. To determine if the contents of pull request contain only the file which contains the charts release.
2. To determine if the release has been updated.

parameters:
    --api-url : API URL for the pull request.
    --version : version to compare with the current version

results:
    if --api-url is specified, output variables are set:
        PR_version : The chart verifier version read from the version file from the PR.
        PR_release_image : The name of the image to be used for the release.
        PR_release_info : Information about the release content.
        PR_includes_release : Set to true if the PR contains the version file.
        PR_release_body : Body of text to be used to describe the release.
    if --version only is specified, output variables are set:
        updated : set to true if the version specified is later than the version in the version file
                  from the main branch.
    if neither parameters are specified, output variables are set:
        PR_version : The chart verifier version read from the version file from main branch.
        PR_release_image : The name of the image from the version file from main branch.
"""


import re
import os
import argparse
import json
import requests
import semver
import sys
from release import release_info
from release import releaser

sys.path.append('../')
from owners import checkuser
from github import gitutils

VERSION_FILE = "release/release_info.json"
TYPE_MATCH_EXPRESSION = "(partners|redhat|community)"
CHARTS_PR_BASE_REPO = gitutils.CHARTS_REPO
CHARTS_PR_HEAD_REPO = gitutils.DEVELOPMENT_REPO
DEV_PR_BASE_REPO = gitutils.DEVELOPMENT_REPO
DEV_PR_HEAD_REPO = gitutils.DEVELOPMENT_REPO



def check_if_only_charts_are_included(api_url):

    print("[INFO] check if PR includes only chart files")
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    chart_pattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/.*")
    page_number = 1
    max_page_size,page_size = 100,100
    file_count = 0

    while page_size == max_page_size:

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        print(f"Query files : {files_api_query}")
        pr_files = requests.get(files_api_query,headers=headers)
        files = pr_files.json()
        page_size = len(files)
        file_count += page_size
        page_number += 1

        for f in files:
            file_path = f["filename"]
            match = chart_pattern.match(file_path)
            if not match:
                print(f"[INFO non chart file found: {file_path}")
                return False

    return True

def check_if_no_charts_are_included(api_url):

    print("[INFO] check if PR contains any chart files")
    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    chart_pattern = re.compile(r"charts/"+TYPE_MATCH_EXPRESSION+"/([\w-]+)/([\w-]+)/.*")
    page_number = 1
    max_page_size,page_size = 100,100
    file_count = 0

    while page_size == max_page_size:

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        print(f"Query files : {files_api_query}")
        pr_files = requests.get(files_api_query,headers=headers)
        files = pr_files.json()
        page_size = len(files)
        file_count += page_size
        page_number += 1

        for f in files:
            file_path = f["filename"]
            match = chart_pattern.match(file_path)
            if match:
                print(f"[INFO chart file found: {file_path}")
                return False

    return True

def check_if_only_version_file_is_modified(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/<pr_number>

    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    pattern_versionfile = re.compile(r"release/release_info.json")
    page_number = 1
    max_page_size,page_size = 100,100

    version_file_found = False
    while (page_size == max_page_size):

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        r = requests.get(files_api_query,headers=headers)
        files = r.json()
        page_size = len(files)
        page_number += 1

        for f in files:
            filename = f["filename"]
            if pattern_versionfile.match(filename):
                version_file_found = True
            else:
                return False

    return version_file_found

def check_if_dev_release_branch(sender,pr_branch,pr_body,api_url,pr_head_repo):

    print("[INFO] check if PR is release branch on dev")

    if not sender==os.environ.get("BOT_NAME"):
        print(f"Sender indicates PR is not part of a release: {sender}")
        return False

    if not pr_branch.startswith(releaser.DEV_PR_BRANCH_NAME_PREFIX):
        print(f"PR branch indicates PR is not part of a release: {pr_branch}")
        return False

    version = pr_branch.removeprefix(releaser.DEV_PR_BRANCH_NAME_PREFIX)
    if not semver.VersionInfo.isvalid(version):
        print(f"Release part ({version}) of branch name {pr_branch} is not a valid semantic version.")
        return False

    if not pr_head_repo.endswith(DEV_PR_HEAD_REPO):
        print(f"PR does not have the expected origin. Got: {pr_head_repo}, expected: {DEV_PR_HEAD_REPO}")
        return False

    if not pr_body.startswith(releaser.DEV_PR_BRANCH_BODY_PREFIX):
        print(f"PR title indicates PR is not part of a release: {pr_body}")
        return False

    return check_if_only_charts_are_included(api_url)

def check_if_charts_release_branch(sender,pr_branch,pr_body,api_url,pr_head_repo):

    print("[INFO] check if PR is release branch on charts")

    if not sender==os.environ.get("BOT_NAME"):
        print(f"Sender indicates PR is not part of a release: {sender}")
        return False

    if not pr_branch.startswith(releaser.CHARTS_PR_BRANCH_NAME_PREFIX):
        print(f"PR branch indicates PR is not part of a release: {pr_branch}")
        return False

    version = pr_branch.removeprefix(releaser.CHARTS_PR_BRANCH_NAME_PREFIX)
    if not semver.VersionInfo.isvalid(version):
        print(f"Release part ({version}) of branch name {pr_branch} is not a valid semantic version.")
        return False

    if not pr_head_repo.endswith(CHARTS_PR_HEAD_REPO):
        print(f"PR does not have the expected origin. Got: {pr_head_repo}, expected: {CHARTS_PR_HEAD_REPO}")
        return False

    if not pr_body.startswith(releaser.CHARTS_PR_BRANCH_BODY_PREFIX):
        print(f"PR title indicates PR is not part of a release: {pr_body}")
        return False

    return check_if_no_charts_are_included(api_url)


def make_release_body(version, release_info):
    body = f"Charts workflow version {version} <br><br>"
    body += "This version includes:<br>"
    for info in release_info:
        body += f"- {info}<br>"

    print(f"[INFO] Release body: {body}")
    print(f"::set-output name=PR_release_body::{body}")

def get_version_info():
    data = {}
    with open(VERSION_FILE) as json_file:
        data = json.load(json_file)
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--api-url", dest="api_url", type=str, required=False,
                        help="API URL for the pull request")
    parser.add_argument("-v", "--version", dest="version", type=str, required=False,
                        help="Version to compare")
    parser.add_argument("-s", "--sender", dest="sender", type=str, required=False,
                        help="sender of the PR")
    parser.add_argument("-b", "--pr_branch", dest="pr_branch", type=str, required=False,
                        help="PR branch name")
    parser.add_argument("-t", "--pr_body", dest="pr_body", type=str, required=False,
                        help="PR title")
    parser.add_argument("-r", "--pr_base_repo", dest="pr_base_repo", type=str, required=False,
                        help="PR target repo")
    parser.add_argument("-z", "--pr_head_repo", dest="pr_head_repo", type=str, required=False,
                        help="PR source repo")

    args = parser.parse_args()

    print("[INFO] release checker inputs:")
    print(f"[INFO] arg api-url : {args.api_url}")
    print(f"[INFO] arg version : {args.version}")
    print(f"[INFO] arg sender : {args.sender}")
    print(f"[INFO] arg pr_branch : {args.pr_branch}")
    print(f"[INFO] arg pr_body : {args.pr_body}")
    print(f"[INFO] arg pr base repo :  {args.pr_base_repo}")
    print(f"[INFO] arg pr head repo :  {args.pr_head_repo}")

    if args.pr_branch:
        if args.pr_base_repo.endswith(DEV_PR_BASE_REPO):
            if check_if_dev_release_branch(args.sender,args.pr_branch,args.pr_body,args.api_url,args.pr_head_repo):
                print('[INFO] Dev release pull request found')
                print(f'::set-output name=dev_release_branch::true')
                version = args.pr_branch.removeprefix(releaser.DEV_PR_BRANCH_NAME_PREFIX)
                print(f'::set-output name=PR_version::{version}')
                print(f"::set-output name=PR_release_body::{args.pr_body}")
        elif args.pr_base_repo.endswith(CHARTS_PR_BASE_REPO):
            if check_if_charts_release_branch(args.sender,args.pr_branch,args.pr_body,args.api_url,args.pr_head_repo):
                print('[INFO] Dev release pull request found')
                print(f'::set-output name=charts_release_branch::true')
    elif args.api_url:
        ## should be on PR branch
        if args.pr_base_repo.endswith(DEV_PR_BASE_REPO):
            version_only = check_if_only_version_file_is_modified(args.api_url)
            user_authorized = checkuser.verify_user(args.sender)
            if version_only and user_authorized:
                organization = args.pr_base_repo.removesuffix(DEV_PR_BASE_REPO)
                print(f'::set-output name=charts_repo::{organization}{CHARTS_PR_BASE_REPO}')
                version = release_info.get_version("./")
                version_info = release_info.get_info("./")
                print(f'[INFO] Release found in PR files : {version}.')
                print(f'::set-output name=PR_version::{version}')
                print(f'::set-output name=PR_release_info::{version_info}')
                print(f'::set-output name=PR_includes_release_only::true')
                make_release_body(version,version_info)
            elif version_only and not user_authorized:
                print(f'[ERROR] sender not authorized : {args.sender}.')
                print(f'::set-output name=sender_not_authorized::true')
            else:
                print('[INFO] Not a release PR')
        else:
            print(f'[INFO] Not a release PR, target is not : {DEV_PR_BASE_REPO}.')
    else:
        version = release_info.get_version("./")
        if args.version:
            # should be on main branch
            if semver.compare(args.version,version) > 0 :
                print(f'[INFO] Release {args.version} found in PR files is newer than: {version}.')
                print(f'::set-output name=release_updated::true')
            else:
                print(f'[ERROR] Release found in PR files is not new  : {args.version}.')
        else:
            print(f'[ERROR] no valid parameter set to release checker.')

