import re
import os
import sys
import argparse

import requests

AUTOMERGE = "automerge"

def ensure_automerge_label_does_not_exist(api_url):
    # api_url https://api.github.com/repos/<organization-name>/<repository-name>/pulls/1
    headers = {'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(api_url, headers=headers)
    for label in r.json()["labels"]:
        if label["name"] == AUTOMERGE:
            print("[ERROR] Pull request not merged")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                                        help="API URL for the pull request")
    args = parser.parse_args()
    ensure_automerge_label_does_not_exist(args.api_url)
