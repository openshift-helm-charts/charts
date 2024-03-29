#!/usr/bin/env python3

"""A quick way to check if a given user is an approver in the repository's OWNERS file.

Accepts only a single value (the username)

Returns 0 if the user is found in the OWNERS file in the approver section.
Returns 1 if the user is NOT found in the OWNERS file.
Any other non-zero is considered a failed execution (contextually, something broke)
"""

import os
import sys

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

OWNERS_FILE = "OWNERS"


def is_approver(username: str) -> bool:
    """Returns true if username is in the OWNERS file

    Raises an Exception in cases where the content from the OWNERS file
    does not match our expectations.
    """

    with open(OWNERS_FILE, "r") as f:
        data = f.read()
        out = yaml.load(data, Loader=Loader)

    if "approvers" not in out:
        raise Exception('OWNERS file did not have the required "approvers" key')

    approvers = out.get("approvers")
    if not isinstance(approvers, list):
        raise Exception('The "approvers" key was not a list, and a list is expected')

    if username in out.get("approvers"):
        return True

    return False


def main():
    if len(sys.argv) != 2:
        print(
            "[Error] This script accepts only a single string as an argument, representing the user to check."
        )
        return 10

    user = sys.argv[1]

    print(f"[Info] Checking OWNERS file at path {os.path.abspath(OWNERS_FILE)}")
    if not os.path.exists(OWNERS_FILE):
        print(f"{OWNERS_FILE} file does not exist.")
        return 20

    try:
        if is_approver(user):
            print(f'[Info] User "{user}" is an approver.')
            return 0
    except Exception as e:
        print(f"[Error] Could not extract expected values from OWNERS file: {e}.")
        return 30

    print(f'[Info] User "{user}" is NOT an approver.')
    return 1


if __name__ == "__main__":
    sys.exit(main())
