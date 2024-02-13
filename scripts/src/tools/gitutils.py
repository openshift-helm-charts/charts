"""
Used within github actions to perform github tasks, specifically as part of the charts auto release process
defined in .github/workflow/release.yml

Requires the environment to contain:
BOT_TOKEN : valid Oauth token for a bot with permission to update development and chart repositories
BOT_NAME : valid owner of the BOT_TOKEN

main functions :
- create_charts_pr - creates a PR to the charts repo based on changes made in the repository
- commit_development_change - directly commits changes to the main branch of the devlopment repository
"""

import json
import os
import sys

import requests
from git import Repo

GITHUB_BASE_URL = "https://api.github.com"
CHARTS_REPO = "/charts"
DEVELOPMENT_REPO = "/development"
STAGE_REPO = "/stage"

PR_CREATED = "PR_CREATED"
PR_NOT_NEEDED = "PR_NOT_NEEDED"
PR_FAILED = "PR_FAILED"

# GitHub actions bot email for git email
GITHUB_ACTIONS_BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"


def set_git_username_email(repo, username, email):
    """
    Parameters:
    repo (git.Repo): git.Repo instance of the local directory
    username (str): git username to set
    email (str): git email to set
    """
    repo.config_writer().set_value("user", "name", username).release()
    repo.config_writer().set_value("user", "email", email).release()


def github_api_post(endpoint, headers, json):
    r = requests.post(f"{GITHUB_BASE_URL}/{endpoint}", headers=headers, json=json)

    try:
        response_json = r.json()

        if "message" in response_json:
            print(f'[ERROR] from post request: {response_json["message"]}')
            sys.exit(1)
    except json.JSONDecodeError:
        pass

    return r


def github_api_get(endpoint, headers):
    r = requests.get(f"{GITHUB_BASE_URL}/{endpoint}", headers=headers)
    response_json = r.json()
    if "message" in response_json:
        print(f'[ERROR] get request: {response_json["message"]}')
        sys.exit(1)

    return r


def github_api(method, endpoint, bot_token, json={}):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {bot_token}",
    }
    if method == "get":
        return github_api_get(endpoint, headers)
    elif method == "post":
        return github_api_post(endpoint, headers, json)
    else:
        raise ValueError(
            f"Github API method {method} not implemented in helper function"
        )


def get_bot_name_and_token():
    bot_name = os.environ.get("BOT_NAME")
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_name and not bot_token:
        raise Exception("BOT_TOKEN environment variable not defined")
    elif not bot_name:
        raise Exception("BOT_TOKEN set but BOT_NAME not specified")
    elif not bot_token:
        raise Exception("BOT_NAME set but BOT_TOKEN not specified")
    else:
        print(f"found bot name ({bot_name}) and token.")
    return bot_name, bot_token


def create_pr(branch_name, skip_files, repository, message, target_branch):
    repo = Repo(os.getcwd())

    bot_name, bot_token = get_bot_name_and_token()
    set_git_username_email(repo, bot_name, GITHUB_ACTIONS_BOT_EMAIL)

    repo.create_head(branch_name)
    print(f"checkout branch {branch_name}")
    repo.git.checkout(branch_name)

    if add_changes(repo, skip_files):
        print(f"commit changes with message: {branch_name}")
        repo.index.commit(branch_name)

        print(f"push the branch {branch_name} to {repository}")
        repo.git.push(
            f"https://x-access-token:{bot_token}@github.com/{repository}",
            f"HEAD:refs/heads/{branch_name}",
            "-f",
        )

        print(f"make the pull request to {target_branch}")
        data = {
            "head": branch_name,
            "base": f"{target_branch}",
            "title": branch_name,
            "body": f"{message}",
        }

        r = github_api("post", f"repos/{repository}/pulls", bot_token, json=data)

        j = json.loads(r.text)
        if "number" in j:
            print(f"pull request info: {j['number']}")
            return PR_CREATED
        else:
            print(
                f"Unexpected response from PR. status code: {r.status_code}, text: {j}"
            )
            return PR_FAILED

    else:
        print(f"no changes required for {repository}")
        return PR_NOT_NEEDED


def add_changes(repo, skip_files):
    if len(skip_files) == 0:
        changed = [item.a_path for item in repo.index.diff(None)]
        for change in changed:
            print(f"Changed file: {change}")
        for add in repo.untracked_files:
            print(f"Added file: {add}")
        print("Add all changes")
        repo.git.add(all=True)
    else:
        changed = [item.a_path for item in repo.index.diff(None)]
        for change in changed:
            if change in skip_files:
                print(f"Skip changed file: {change}")
            else:
                print(f"Add changed file: {change}")
                repo.git.add(change)

        for add in repo.untracked_files:
            if add in skip_files:
                print(f"Skip added file: {add}")
            else:
                print(f"Add added file: {add}")
                repo.git.add(add)

    return len(repo.index.diff("HEAD")) > 0


def add_output(name, value):
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        print(f"{name}={value}", file=fh)
