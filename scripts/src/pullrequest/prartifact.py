import os
import sys
import requests

pr_files = []
pr_labels = []
xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"


def get_modified_files(api_url):
    """Populates and returns the list of files modified by this the PR

    Args:
        api_url (str): URL of the GitHub PR

    Returns:
        list[str]: List of modified files
    """
    if not pr_files:
        page_number = 1
        max_page_size, page_size = 100, 100
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        files_api_url = f"{api_url}/files"

        while page_size == max_page_size:
            files_api_query = f"{files_api_url}?per_page={page_size}&page={page_number}"
            print(f"[INFO] Query files : {files_api_query}")
            r = requests.get(files_api_query, headers=headers)
            files = r.json()
            page_size = len(files)
            page_number += 1

            if xRateLimit in r.headers:
                print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
            if xRateRemain in r.headers:
                print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

            if "message" in files:
                print(f'[ERROR] getting pr files: {files["message"]}')
                sys.exit(1)
            else:
                for file in files:
                    if "filename" in file:
                        pr_files.append(file["filename"])

    return pr_files


def get_labels(api_url):
    if not pr_labels:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        r = requests.get(api_url, headers=headers)
        pr_data = r.json()

        if xRateLimit in r.headers:
            print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
        if xRateRemain in r.headers:
            print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

        if "message" in pr_data:
            print(f'[ERROR] getting pr files: {pr_data["message"]}')
            sys.exit(1)
        if "labels" in pr_data:
            for label in pr_data["labels"]:
                pr_labels.append(label["name"])

    return pr_labels
