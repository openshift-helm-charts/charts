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

import argparse
import json
import os
import re
import sys

import semver
from reporegex import matchers

from release import release_info, releaser

sys.path.append("../")
from owners import checkuser
from pullrequest import prartifact
from tools import gitutils

VERSION_FILE = "release/release_info.json"
CHARTS_PR_BASE_REPO = gitutils.CHARTS_REPO
CHARTS_PR_HEAD_REPO = gitutils.CHARTS_REPO
DEV_PR_BASE_REPO = gitutils.DEVELOPMENT_REPO
DEV_PR_HEAD_REPO = gitutils.DEVELOPMENT_REPO
STAGE_PR_BASE_REPO = gitutils.STAGE_REPO
STAGE_PR_HEAD_REPO = gitutils.STAGE_REPO
DEFAULT_BOT_NAME = "openshift-helm-charts-bot"
ERROR_IF_MATCH_NOT_FOUND = False
ERROR_IF_MATCH_FOUND = True


def check_file_in_pr(api_url, pattern, error_value):
    print("[INFO] check if PR for matching files")
    files = prartifact.get_modified_files(api_url)

    for file_path in files:
        match = pattern.match(file_path)
        if not match and not error_value:
            print(f"[INFO] stop non match found  : {file_path}")
            return False
        elif match and error_value:
            print(f"[INFO] stop match found  : {file_path}")
            return False

    return True


def check_if_only_charts_are_included(api_url):
    print("[INFO] check if only chart files are included")
    chart_pattern = re.compile(
        matchers.submission_path_matcher(include_version_matcher=False) + r"./*"
    )
    return check_file_in_pr(api_url, chart_pattern, ERROR_IF_MATCH_NOT_FOUND)


def check_if_no_charts_are_included(api_url):
    print("[INFO] check if no chart files are included")
    chart_pattern = re.compile(
        matchers.submission_path_matcher(include_version_matcher=False) + r"./*"
    )
    return check_file_in_pr(api_url, chart_pattern, ERROR_IF_MATCH_FOUND)


def check_if_only_version_file_is_modified(api_url):
    print("[INFO] check if only version file is modified")
    pattern_versionfile = re.compile(r"release/release_info.json")
    return check_file_in_pr(api_url, pattern_versionfile, ERROR_IF_MATCH_NOT_FOUND)


def check_if_dev_release_branch(sender, pr_branch, pr_body, api_url, pr_head_repo):
    print("[INFO] check if PR is release branch on dev")

    if sender != os.environ.get("BOT_NAME") and sender != DEFAULT_BOT_NAME:
        print(f"Sender indicates PR is not part of a release: {sender}")
        return False

    if not checkuser.verify_user(sender):
        print(f"Sender is not authorized to create a release PR : {sender}")
        return False

    if not pr_branch.startswith(releaser.DEV_PR_BRANCH_NAME_PREFIX):
        print(f"PR branch indicates PR is not part of a release: {pr_branch}")
        return False

    version = pr_branch.removeprefix(releaser.DEV_PR_BRANCH_NAME_PREFIX)
    if not semver.VersionInfo.is_valid(version):
        print(
            f"Release part ({version}) of branch name {pr_branch} is not a valid semantic version."
        )
        return False

    if not pr_head_repo.endswith(DEV_PR_HEAD_REPO):
        print(
            f"PR does not have the expected origin. Got: {pr_head_repo}, expected: {DEV_PR_HEAD_REPO}"
        )
        return False

    if not pr_body.startswith(releaser.DEV_PR_BRANCH_BODY_PREFIX):
        print(f"PR title indicates PR is not part of a release: {pr_body}")
        return False

    return check_if_only_charts_are_included(api_url)


def check_if_charts_release_branch(sender, pr_branch, pr_body, api_url, pr_head_repo):
    print("[INFO] check if PR is release branch on charts")

    if sender != os.environ.get("BOT_NAME") and sender != DEFAULT_BOT_NAME:
        print(f"Sender indicates PR is not part of a release: {sender}")
        return False

    if not checkuser.verify_user(sender):
        print(f"Sender is not authorized to create a release PR : {sender}")
        return False

    if not pr_branch.startswith(releaser.CHARTS_PR_BRANCH_NAME_PREFIX):
        print(f"PR branch indicates PR is not part of a release: {pr_branch}")
        return False

    version = pr_branch.removeprefix(releaser.CHARTS_PR_BRANCH_NAME_PREFIX)
    if not semver.VersionInfo.is_valid(version):
        print(
            f"Release part ({version}) of branch name {pr_branch} is not a valid semantic version."
        )
        return False

    if not pr_head_repo.endswith(CHARTS_PR_HEAD_REPO) and not pr_head_repo.endswith(
        STAGE_PR_HEAD_REPO
    ):
        print(
            f"PR does not have the expected origin. Got: {pr_head_repo}, expected: {CHARTS_PR_HEAD_REPO}"
        )
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
    gitutils.add_output("PR_release_body", body)


def get_version_info():
    data = {}
    with open(VERSION_FILE) as json_file:
        data = json.load(json_file)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--api-url",
        dest="api_url",
        type=str,
        required=False,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        type=str,
        required=False,
        help="Version to compare",
    )
    parser.add_argument(
        "-s",
        "--sender",
        dest="sender",
        type=str,
        required=False,
        help="sender of the PR",
    )
    parser.add_argument(
        "-b",
        "--pr_branch",
        dest="pr_branch",
        type=str,
        required=False,
        help="PR branch name",
    )
    parser.add_argument(
        "-t", "--pr_body", dest="pr_body", type=str, required=False, help="PR title"
    )
    parser.add_argument(
        "-r",
        "--pr_base_repo",
        dest="pr_base_repo",
        type=str,
        required=False,
        help="PR target repo",
    )
    parser.add_argument(
        "-z",
        "--pr_head_repo",
        dest="pr_head_repo",
        type=str,
        required=False,
        help="PR source repo",
    )

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
            if check_if_dev_release_branch(
                args.sender,
                args.pr_branch,
                args.pr_body,
                args.api_url,
                args.pr_head_repo,
            ):
                print("[INFO] Dev release pull request found")
                gitutils.add_output("dev_release_branch", "true")
                version = args.pr_branch.removeprefix(
                    releaser.DEV_PR_BRANCH_NAME_PREFIX
                )
                gitutils.add_output("PR_version", version)
                gitutils.add_output("PR_release_body", args.pr_body)
        elif args.pr_base_repo.endswith(
            CHARTS_PR_BASE_REPO
        ) or args.pr_base_repo.endswith(STAGE_PR_BASE_REPO):
            if check_if_charts_release_branch(
                args.sender,
                args.pr_branch,
                args.pr_body,
                args.api_url,
                args.pr_head_repo,
            ):
                print("[INFO] Workflow release pull request found")
                gitutils.add_output("charts_release_branch", "true")

    elif args.api_url:
        # should be on PR branch
        if args.pr_base_repo.endswith(DEV_PR_BASE_REPO):
            version_only = check_if_only_version_file_is_modified(args.api_url)
            user_authorized = checkuser.verify_user(args.sender)
            if version_only and user_authorized:
                organization = args.pr_base_repo.removesuffix(DEV_PR_BASE_REPO)
                gitutils.add_output(
                    "charts_repo", f"{organization}{CHARTS_PR_BASE_REPO}"
                )
                gitutils.add_output("stage_repo", f"{organization}{STAGE_PR_BASE_REPO}")
                version = release_info.get_version("./")
                version_info = release_info.get_info("./")
                print(f"[INFO] Release found in PR files : {version}.")
                gitutils.add_output("PR_version", version)
                gitutils.add_output("PR_release_info", version_info)
                gitutils.add_output("PR_includes_release_only", "true")
                make_release_body(version, version_info)
            elif version_only and not user_authorized:
                print(f"[ERROR] sender not authorized : {args.sender}.")
                gitutils.add_output("sender_not_authorized", "true")
            else:
                print("[INFO] Not a release PR")
        else:
            print(f"[INFO] Not a release PR, target is not : {DEV_PR_BASE_REPO}.")
    else:
        version = release_info.get_version("./")
        if args.version:
            # should be on main branch
            if semver.compare(args.version, version) > 0:
                print(
                    f"[INFO] Release {args.version} found in PR files is newer than: {version}."
                )
                gitutils.add_output("release_updated", "true")
            else:
                print(
                    f"[ERROR] Release found in PR files is not new  : {args.version}."
                )
        else:
            print("[ERROR] no valid parameter set to release checker.")
