import argparse
import os
import re
import sys

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from tools import gitutils

sys.path.append("../")
from pullrequest import prartifact


def check_if_ci_only_is_modified(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1

    files = prartifact.get_modified_files(api_url)
    workflow_files = [
        re.compile(r".github/(workflows|actions)/.*"),
        re.compile(r"scripts/.*"),
        re.compile(r"tests/.*"),
    ]
    test_files = [
        re.compile(r"tests/functional/behave_features/.*.feature"),
    ]
    skip_build_files = [
        re.compile(r"release/release_info.json"),
        re.compile(r"README.md"),
        re.compile(r"docs/([\w-]+)\.md"),
    ]

    print(f"[INFO] The following files were modified in this PR: {files}")

    workflow_found = False
    others_found = False
    tests_included = False

    for filename in files:
        if any([pattern.match(filename) for pattern in workflow_files]):
            print(f"[DEBUG] Modified file {filename} is a workflow file.")
            workflow_found = True
            # Tests are considered workflow files AND test files to inform other actions
            # so we detect both separately.
            if any([pattern.match(filename) for pattern in test_files]):
                print(f"[DEBUG] Modified file {filename} is also a test file.")
                tests_included = True
        elif any([pattern.match(filename) for pattern in skip_build_files]):
            print(f"[DEBUG] Modified file {filename} is a skippable file.")
            others_found = True
        else:
            print(
                f"[DEBUG] Modified file {filename} did not match any file paths of interest. Ignoring."
            )
            continue

    if others_found and not workflow_found:
        gitutils.add_output("do-not-build", "true")
    elif tests_included:
        print("[INFO] set full_tests_in_pr to true")
        gitutils.add_output("full_tests_in_pr", "true")

    return workflow_found


def verify_user(username):
    print(f"[INFO] Verify user. {username}")
    owners_path = "OWNERS"
    if not os.path.exists(owners_path):
        print(f"[ERROR] {owners_path} file does not exist.")
    else:
        data = open(owners_path).read()
        out = yaml.load(data, Loader=Loader)
        if username in out["approvers"]:
            print(f"[INFO] {username} authorized")
            return True
        else:
            print(f"[ERROR] {username} cannot run tests")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--api-url",
        dest="api_url",
        type=str,
        required=False,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-n",
        "--verify-user",
        dest="username",
        type=str,
        required=True,
        help="check if the user can run tests",
    )
    args = parser.parse_args()
    if not args.api_url:
        if verify_user(args.username):
            print("[INFO] User authorized for manual invocation - run tests.")
            gitutils.add_output("run-tests", "true")
        else:
            print(
                "[INFO] User not authorized for manual invocation - do not run tests."
            )
            gitutils.add_output("workflow-only-but-not-authorized", "true")
    elif check_if_ci_only_is_modified(args.api_url):
        if verify_user(args.username):
            print(
                "[INFO] PR is workflow changes only and user is authorized - run tests."
            )
            gitutils.add_output("run-tests", "true")
        else:
            print(
                "[INFO] PR is workflow changes only but user is not authorized - do not run tests."
            )
            gitutils.add_output("workflow-only-but-not-authorized", "true")
    else:
        print("[INFO] Non workflow changes were found - do not run tests")


if __name__ == "__main__":
    main()
