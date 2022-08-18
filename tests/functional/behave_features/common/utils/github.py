# -*- coding: utf-8 -*-
"""Utility class for setting up and manipulating GitHub operations."""

import json
import requests
from retrying import retry

from common.utils.setttings import *

@retry(stop_max_delay=30_000, wait_fixed=1000)
def get_run_id(secrets, pr_number=None):

    pr = get_pr(secrets, pr_number)
    r = github_api(
        'get', f'repos/{secrets.test_repo}/actions/runs', secrets.bot_token)
    runs = json.loads(r.text)

    for run in runs['workflow_runs']:
        if run['head_sha'] == pr['head']['sha'] and run['name'] == CERTIFICATION_CI_NAME:
            return run['id']
    else:
        raise Exception("Workflow for the submitted PR did not run.")


@retry(stop_max_delay=60_000*40, wait_fixed=2000)
def get_run_result(secrets, run_id):
    r = github_api(
        'get', f'repos/{secrets.test_repo}/actions/runs/{run_id}', secrets.bot_token)
    run = json.loads(r.text)

    if run['conclusion'] is None:
        raise Exception(f"Workflow {run_id} is still running, PR: {secrets.pr_number} ")

    return run['conclusion']


@retry(stop_max_delay=10_000, wait_fixed=1000)
def get_release_assets(secrets, release_id, required_assets):
    r = github_api(
        'get', f'repos/{secrets.test_repo}/releases/{release_id}/assets', secrets.bot_token)
    asset_list = json.loads(r.text)
    asset_names = [asset['name'] for asset in asset_list]
    missing_assets = list()
    for asset in required_assets:
        if asset not in asset_names:
            missing_assets.append(asset)
    if len(missing_assets) > 0:
        raise Exception(f"Missing release asset: {missing_assets}")


@retry(stop_max_delay=15_000, wait_fixed=1000)
def get_release_by_tag(secrets, release_tag):
    r = github_api(
        'get', f'repos/{secrets.test_repo}/releases', secrets.bot_token)
    releases = json.loads(r.text)
    for release in releases:
        if release['tag_name'] == release_tag:
            return release
    raise Exception("Release not published")


def get_pr(secrets, pr_number=None):
    pr_number = secrets.pr_number if pr_number is None else pr_number
    r = github_api(
        'post', f'repos/{secrets.test_repo}/pulls/{pr_number}', secrets.bot_token)
    pr = json.loads(r.text)
    return pr


def github_api_get(endpoint, bot_token, headers={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.get(f'{GITHUB_BASE_URL}/{endpoint}', headers=headers)

    return r


def github_api_delete(endpoint, bot_token, headers={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.delete(f'{GITHUB_BASE_URL}/{endpoint}', headers=headers)

    return r


def github_api_post(endpoint, bot_token, headers={}, json={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.post(f'{GITHUB_BASE_URL}/{endpoint}',
                      headers=headers, json=json)

    return r


def github_api(method, endpoint, bot_token, headers={}, data={}, json={}):
    if method == 'get':
        return github_api_get(endpoint, bot_token, headers=headers)
    elif method == 'post':
        return github_api_post(endpoint, bot_token, headers=headers, json=json)
    elif method == 'delete':
        return github_api_delete(endpoint, bot_token, headers=headers)
    else:
        raise ValueError(
            "Github API method not implemented in helper function")
