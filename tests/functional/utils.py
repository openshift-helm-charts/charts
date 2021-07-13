# -*- coding: utf-8 -*-
"""Common utility functions used by tests"""

import yaml
import pytest
import tarfile
import os


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
            with open(member.name, 'r') as fd:
                try:
                    chart_yaml = yaml.safe_load(fd)
                except yaml.YAMLError as err:
                    pytest.fail(f"error parsing '{path}': {err}")
            return chart_yaml['name'], chart_yaml['version']
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
