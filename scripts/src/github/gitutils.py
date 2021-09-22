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


import os
import json
import requests
from git import Repo
from git.exc import GitCommandError

GITHUB_BASE_URL = 'https://api.github.com'
CHARTS_REPO = f"{os.environ.get('REPOSITORY_ORGANIZATION')}/charts"
DEVELOPMENT_REPO = f"{os.environ.get('REPOSITORY_ORGANIZATION')}/development"

# GitHub actions bot email for git email
GITHUB_ACTIONS_BOT_EMAIL = '41898282+github-actions[bot]@users.noreply.github.com'

def set_git_username_email(repo, username, email):
    """
    Parameters:
    repo (git.Repo): git.Repo instance of the local directory
    username (str): git username to set
    email (str): git email to set
    """
    repo.config_writer().set_value("user", "name", username).release()
    repo.config_writer().set_value("user", "email", email).release()


def github_api_post(endpoint, bot_token, headers={}, json={}):
    r = requests.post(f'{GITHUB_BASE_URL}/{endpoint}',
                      headers=headers, json=json)
    return r

def github_api_get(endpoint, bot_token, headers={}):
    r = requests.get(f'{GITHUB_BASE_URL}/{endpoint}', headers=headers)
    return r

def github_api(method, endpoint, bot_token, headers={}, data={}, json={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    if method == 'get':
        return github_api_get(endpoint, bot_token, headers=headers)
    elif method == 'post':
        return github_api_post(endpoint, bot_token, headers=headers, json=json)
    else:
        raise ValueError(
            f"Github API method {method} not implemented in helper function")

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


def create_charts_pr(version):

    repo = Repo(os.getcwd())

    bot_name, bot_token = get_bot_name_and_token()
    set_git_username_email(repo,bot_name,GITHUB_ACTIONS_BOT_EMAIL)

    branch_name = f"Release-{version}"
    repo.create_head(branch_name)
    print(f"checkout branch {branch_name}")
    repo.git.checkout(branch_name)

    if add_changes(repo,[]):

        print(f"commit changes with message: {branch_name}")
        repo.index.commit(branch_name)

        print(f"push the branch to {CHARTS_REPO}")
        repo.git.push(f'https://x-access-token:{bot_token}@github.com/{CHARTS_REPO}',
                   f'HEAD:refs/heads/{branch_name}','-f')

        print("make the pull request")
        data = {'head': branch_name, 'base': 'main',
                'title': branch_name, 'body': f'Workflow and script updates from development repository {branch_name}'}

        r = github_api(
            'post', f'repos/{CHARTS_REPO}/pulls', bot_token, json=data)

        j = json.loads(r.text)
        print(f"pull request info: {j['number']}")
    else:
        print(f"no changes required for {CHARTS_REPO}")



def commit_development_updates(version,skip_files):

    repo = Repo(os.getcwd())

    print("checkout main")
    repo.git.checkout("main")

    if add_changes(repo,skip_files):

        print(f"commit changes with message: Version-{version} Update charts from chart repository")
        repo.index.commit(f"Version-{version} Update charts from chart repository")

        print(f"push the branch to {DEVELOPMENT_REPO}")
        bot_name, bot_token = get_bot_name_and_token()

        repo.git.push(f'https://x-access-token:{bot_token}@github.com/{DEVELOPMENT_REPO}',
                  f'HEAD:refs/heads/main', '-f')
    else:
        print(f"no changes required for {DEVELOPMENT_REPO}")


def add_changes(repo,skip_files):

    if len(skip_files) == 0:
        print(f"Add all changes")
        repo.git.add(all=True)
    else:
        changed = [ item.a_path for item in repo.index.diff(None) ]
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
