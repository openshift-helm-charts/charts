import re
import argparse
import os
import requests
import json
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def check_if_ci_only_is_modified(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1

    files_api_url = f'{api_url}/files'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    pattern_workflow = re.compile(r".github/workflows/.*")
    pattern_script = re.compile(r"scripts/.*")
    pattern_test = re.compile(r"tests/.*")
    page_number = 1
    max_page_size,page_size = 100,100

    workflow_found = False
    other_found = False
    test_config_path = ""

    while (page_size == max_page_size) & (not other_found):

        files_api_query = f'{files_api_url}?per_page={page_size}&page={page_number}'
        r = requests.get(files_api_query,headers=headers)
        files = r.json()
        page_size = len(files)
        page_number += 1


        for f in files:
            filename = f["filename"]
            if pattern_workflow.match(filename):
                workflow_found = True
            elif pattern_script.match(filename):
                workflow_found = True
            elif pattern_test.match(filename):
                workflow_found = True
            else:
                other_found = True
                break

    if other_found:
        return False

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
            print(f"[INFO] {username} verified")
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
    if verify_user(args.username):
        if not args.api_url or check_if_ci_only_is_modified(args.api_url):
            print(f"[INFO] PR is only workflow changes - run tests")
            print(f"::set-output name=run-tests::true")

if __name__ == "__main__":
    main()
