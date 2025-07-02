"""
This script will help to list, create or update secrets of a repository

Prerequsites:

1. Before running this script, you have to set the GITHUB_TOKEN environment variable with as below:
export GITHUB_TOKEN=<Github_token_value>

Note: Github Token you are using needs to have correct authorization to list/create/update the secrets

2. Install the "pynacl" module using : pip install pynacl==1.5.0

Example Usage:

1. To list the secret names of openshift-helm-charts/sandbox repository
  python push_secrets.py -r openshift-helm-charts/sandbox -l

2. To create or update the CLUSTER_TOKEN of openshift-helm-charts/sandbox repository
  python push_secrets.py -r openshift-helm-charts/sandbox -s CLUSTER_TOKEN -v <cluster_token_value>

"""

import argparse
import json
import logging
import os
import sys
from base64 import b64encode

import requests
from nacl import encoding, public

sys.path.append("../")
from pullrequest import prartifact

token = os.environ.get("BOT_TOKEN")
headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {token}",
}

logging.basicConfig(level=logging.INFO)


def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def get_repo_public_key(repo):
    """Get the public key id and key of a github repository"""
    response = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=headers,
    )
    if response.status_code != 200:
        logging.error(
            f"unexpected response getting repo public key : {response.status_code} : {response.reason}"
        )
        sys.exit(1)
    response_json = response.json()

    if prartifact.xRateLimit in response.headers:
        print(
            f"[DEBUG] {prartifact.xRateLimit} : {response.headers[prartifact.xRateLimit]}"
        )
    if prartifact.xRateRemain in response.headers:
        print(
            f"[DEBUG] {prartifact.xRateRemain}  : {response.headers[prartifact.xRateRemain]}"
        )

    if "message" in response_json:
        print(f'[ERROR] getting public key: {response_json["message"]}')
        sys.exit(1)

    return response_json["key_id"], response_json["key"]


def get_repo_secrets(repo):
    """Get the list of secret names of a github repository"""
    secret_names = []
    response = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets", headers=headers
    )
    if response.status_code != 200:
        logging.error(
            f"[ERROR] unexpected response getting repo secrets : {response.status_code} : {response.reason}"
        )
        sys.exit(1)
    response_json = response.json()
    if "message" in response_json:
        print(f'[ERROR] getting repo secrets: {response_json["message"]}')
        sys.exit(1)
    for i in range(response_json["total_count"]):
        secret_names.append(response_json["secrets"][i]["name"])
    return secret_names


def create_or_update_repo_secrets(repo, secret_name, key_id, encrypted_value):
    """Create or update a github repository secret"""
    response = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}",
        json={"key_id": key_id, "encrypted_value": encrypted_value},
        headers=headers,
    )
    if response.status_code != 201 and response.status_code != 204:
        logging.error(
            f"unexpected response during put request : {response.status_code} : {response.reason}"
        )
        sys.exit(1)
    try:
        response_json = response.json()
        if "message" in response_json:
            print(f'[ERROR] updating repo secret: {response_json["message"]}')
            sys.exit(1)
    except json.decoder.JSONDecodeError:
        pass

    logging.info(f"Secret {secret_name} create or update successful")


def main():
    parser = argparse.ArgumentParser(
        description="Script to list, create or update secrets of a repository"
    )
    parser.add_argument(
        "-r",
        "--repo",
        dest="repo",
        type=str,
        required=True,
        help="Github repo name in {org}/{repo_name} format",
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="list",
        action="store_true",
        required=False,
        help="List the secret names",
    )
    parser.add_argument(
        "-s", "--secret", dest="secret", type=str, required=False, help="Secret name"
    )
    parser.add_argument(
        "-v",
        "--value",
        dest="value",
        type=str,
        required=False,
        help="Secret value to set",
    )
    args = parser.parse_args()

    if args.list:
        secrets = get_repo_secrets(args.repo)
        logging.info(f"Github Secret Names: {secrets}")
    elif args.secret and args.value:
        secret_name = args.secret
        secret_value = args.value
        logging.info(f"Setting SECRET: {secret_name}")
        key_id, public_key = get_repo_public_key(args.repo)
        encrypted_value = encrypt(public_key, secret_value)
        create_or_update_repo_secrets(args.repo, secret_name, key_id, encrypted_value)
    else:
        logging.error("Wrong argument combination")


if __name__ == "__main__":
    main()
