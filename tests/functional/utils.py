# -*- coding: utf-8 -*-
"""Common utility functions used by tests"""

import os
import tarfile

import pytest
import requests
import yaml


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
