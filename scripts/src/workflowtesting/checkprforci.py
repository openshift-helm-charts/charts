import re
import argparse
import os
import requests
import json
import yaml
import sys

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def check_if_ci_only_is_modified(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1

    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}

    workflow_files = [re.compile(r".github/workflows/.*"),re.compile(r"scripts/.*"),re.compile(r"tests/.*")]
    test_files = [re.compile(r"tests/functional/step_defs/.*_test_.*"),re.compile(r"tests/functional/behave_features/.*.feature")]
    skip_build_files = [re.compile(r"release/release_info.json"),re.compile(r"README.md"),re.compile(r"docs/([\w-]+)\.md")]
    page_number = 1
    max_page_size,page_size = 100,100

    workflow_found = False
    others_found = False
    tests_included = False

    while (page_size == max_page_size):

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        r = requests.get(files_api_query,headers=headers)
        files = r.json()
        page_size = len(files)
        page_number += 1

        for f in files:
            filename = f["filename"]
            if any([pattern.match(filename) for pattern in workflow_files]):
                workflow_found = True
                if any([pattern.match(filename) for pattern in test_files]):
                    tests_included = True
            elif any([pattern.match(filename) for pattern in skip_build_files]):
                others_found = True
            else:
                return False

    if others_found and not workflow_found:
        print("::set-output name=do-not-build::true")
    elif tests_included:
        print(f"[INFO] set full_tests_in_pr to true")
        print("::set-output name=full_tests_in_pr::true")

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
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=False,
                                        help="API URL for the pull request")
    parser.add_argument("-n", "--verify-user", dest="username", type=str, required=True,
                        help="check if the user can run tests")
    args = parser.parse_args()
    if not args.api_url:
        if verify_user(args.username):
            print(f"[INFO] User authorized for manual invocation - run tests.")
            print(f"::set-output name=run-tests::true")
        else:
            print(f"[INFO] User not authorized for manual invocation - do not run tests.")
            print(f"::set-output name=workflow-only-but-not-authorized::true")
    elif check_if_ci_only_is_modified(args.api_url):
        if verify_user(args.username):
            print(f"[INFO] PR is workflow changes only and user is authorized - run tests.")
            print(f"::set-output name=run-tests::true")
        else:
            print(f"[INFO] PR is workflow changes only but user is not authorized - do not run tests.")
            print(f"::set-output name=workflow-only-but-not-authorized::true")
    else:
        print(f"[INFO] Non workflow changes were found - do not run tests")


if __name__ == "__main__":
    main()
