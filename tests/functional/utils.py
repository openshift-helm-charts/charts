# -*- coding: utf-8 -*-
"""Common utility functions used by tests"""

import os
import tarfile
import json

import pytest
import requests
import yaml
from retrying import retry


@retry(stop_max_delay=30_000)
def get_run_id(secrets, pr_number=None):
    pr_number = secrets.pr_number if pr_number is None else pr_number
    r = github_api(
        'post', f'https://api.github.com/repos/{secrets.test_repo}/pulls/{pr_number}', secrets.bot_token)
    pr = json.loads(r.text)

    r = github_api(
        'get', f'https://api.github.com/repos/{secrets.test_repo}/actions/runs', secrets.bot_token)
    runs = json.loads(r.text)

    for run in runs['workflow_runs']:
        if run['head_sha'] == pr['head']['sha']:
            return run['id']
    else:
        pytest.fail("Workflow for the submitted PR did not run.")


@retry(stop_max_delay=60_000*10)
def get_run_result(secrets, run_id):
    r = github_api(
        'get', f'https://api.github.com/repos/{secrets.test_repo}/actions/runs/{run_id}', secrets.bot_token)
    run = json.loads(r.text)

    if run['conclusion'] is None:
        pytest.fail("Workflow is still running.")

    return run['conclusion']


@retry(stop_max_delay=15_000)
def get_release_by_tag(secrets, release_tag):
    r = github_api(
        'get', f'https://api.github.com/repos/{secrets.test_repo}/releases', secrets.bot_token)
    releases = json.loads(r.text)
    for release in releases:
        if release['tag_name'] == release_tag:
            return release
    raise Exception("Release not published")

# TODO: Support `community` as vendor_type.
def get_all_charts(charts_path: str, vendor_types: str) -> list:
    """Gets charts with src or tgz under `charts/` given vendor_types.

    Parameters:
    charts_path (str): path to the `charts/` directory
    vendor_types (str): vendor type to look for, any combination of `partner`, `redhat`, separated
        by commas, or `all` to run both `partner` and `redhat`.

    Returns:
    list: list of (vendor_type, vendor, chart_name, chart_version) tuples
    """
    ret = []
    # Pre-process vendor types
    vendor_types = vendor_types.replace('partner', 'partners')
    vendor_types = [vt.strip() for vt in vendor_types.split(',')]
    vendor_types = list(
        {'partners', 'redhat', 'all'}.intersection(set(vendor_types)))
    vendor_types = ['partners',
                    'redhat'] if 'all' in vendor_types else vendor_types

    # Iterate through `charts/` to find chart submission with src or tgz
    for vt in vendor_types:
        charts_path_vt = f'{charts_path}/{vt}'
        vendor_names = [name for name in os.listdir(
            charts_path_vt) if os.path.isdir(f'{charts_path_vt}/{name}')]
        for vn in vendor_names:
            charts_path_vt_vn = f'{charts_path_vt}/{vn}'
            chart_names = [name for name in os.listdir(
                charts_path_vt_vn) if os.path.isdir(f'{charts_path_vt_vn}/{name}')]
            for cn in chart_names:
                charts_path_vt_vn_cn = f'{charts_path_vt_vn}/{cn}'
                file_names = [name for name in os.listdir(
                    charts_path_vt_vn_cn)]
                if 'OWNERS' not in file_names:
                    continue
                chart_versions = [name for name in os.listdir(
                    charts_path_vt_vn_cn) if os.path.isdir(f'{charts_path_vt_vn_cn}/{name}')]
                # Only interest in latest chart version
                if len(chart_versions) == 0:
                    continue
                cv = max(chart_versions)
                charts_path_vt_vn_cn_cv = f'{charts_path_vt_vn_cn}/{cv}'
                file_names = [name for name in os.listdir(
                    charts_path_vt_vn_cn_cv)]
                if f'{cn}-{cv}.tgz' in file_names or 'src' in file_names:
                    ret.append((vt, vn, cn, cv))
    return ret


def get_name_and_version_from_report(path):
    """
    Parameters:
    path (str): path to the report.yaml

    Returns:
    str: chart name
    str: chart version
    """
    with open(path, 'r') as fd:
        try:
            report = yaml.safe_load(fd)
        except yaml.YAMLError as err:
            pytest.fail(f"error parsing '{path}': {err}")
    chart = report['metadata']['chart']
    return chart['name'], chart['version']


def get_name_and_version_from_chart_tar(path):
    """
    Parameters:
    path (str): path to the chart tar file

    Returns:
    str: chart name
    str: chart version
    """
    tar = tarfile.open(path)
    for member in tar.getmembers():
        if member.name.split('/')[-1] == 'Chart.yaml':
            chart = tar.extractfile(member)
            if chart is not None:
                content = chart.read()
                try:
                    chart_yaml = yaml.safe_load(content)
                    return chart_yaml['name'], chart_yaml['version']
                except yaml.YAMLError as err:
                    pytest.fail(f"error parsing '{path}': {err}")
    else:
        pytest.fail(f"Chart.yaml not in {path}")


def get_name_and_version_from_chart_src(path):
    """
    Parameters:
    path (str): path to the chart src directory

    Returns:
    str: chart name
    str: chart version
    """
    chart_path = os.path.join(path, 'Chart.yaml')
    with open(chart_path, 'r') as fd:
        try:
            chart_yaml = yaml.safe_load(fd)
        except yaml.YAMLError as err:
            pytest.fail(f"error parsing '{path}': {err}")
    return chart_yaml['name'], chart_yaml['version']


def github_api_get(endpoint, bot_token, headers={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.get(endpoint, headers=headers)

    return r


def github_api_delete(endpoint, bot_token, headers={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.delete(endpoint, headers=headers)

    return r


def github_api_post(endpoint, bot_token, headers={}, json={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.post(endpoint, headers=headers, json=json)

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
