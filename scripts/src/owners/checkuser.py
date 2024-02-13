"""
Used by a github action to determine if the owner of a PR is permitted to change the files
associated with publishing a release of the development workflows.

parameters:
    --api-url : API URL for the pull request
    --user : user to be checked for authority to modify release files in a PR

results:
    exit code 1 if pull request contains restricted files and user is not authorized to modify them.
"""

import argparse
import os
import re
import sys

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

sys.path.append("../")
from pullrequest import prartifact

OWNERS_FILE = "OWNERS"
VERSION_FILE = "release/release_info.json"
THIS_FILE = "scripts/src/owners/checkuser.py"


def verify_user(username):
    print(f"[INFO] Verify user. {username}")
    if not os.path.exists(OWNERS_FILE):
        print(f"[ERROR] {OWNERS_FILE} file does not exist.")
    else:
        data = open(OWNERS_FILE).read()
        out = yaml.load(data, Loader=Loader)
        if username in out["approvers"]:
            print(f"[INFO] {username} authorized")
            return True
        else:
            print(f"[ERROR] {username} not auhtorized")
    return False


def check_for_restricted_file(api_url):
    files = prartifact.get_modified_files(api_url)
    pattern_owners = re.compile(OWNERS_FILE)
    pattern_versionfile = re.compile(VERSION_FILE)
    pattern_thisfile = re.compile(THIS_FILE)

    for filename in files:
        if (
            pattern_versionfile.match(filename)
            or pattern_owners.match(filename)
            or pattern_thisfile.match(filename)
        ):
            print(f"[INFO] restricted file found: {filename}")
            return True

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--api-url",
        dest="api_url",
        type=str,
        required=True,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-u",
        "--user",
        dest="username",
        type=str,
        required=True,
        help="user to be checked for authority to modify release files in a PR",
    )
    args = parser.parse_args()

    if check_for_restricted_file(args.api_url):
        if verify_user(args.username):
            print(f"[INFO] {args.username} is authorized to modify all files in the PR")
        else:
            print(
                f"[INFO] {args.username} is not authorized to modify all files in the PR"
            )
            sys.exit(1)
    else:
        print("[INFO] no restricted files found in the PR")
