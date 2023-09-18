# -*- coding: utf-8 -*-
"""Utility module for processing chart files."""

import os
import tarfile
import pytest
import yaml
import shutil


def get_name_and_version_from_report(path):
    """
    Parameters:
    path (str): path to the report.yaml

    Returns:
    str: chart name
    str: chart version
    """
    with open(path, "r") as fd:
        try:
            report = yaml.safe_load(fd)
        except yaml.YAMLError as err:
            pytest.fail(f"error parsing '{path}': {err}")
    chart = report["metadata"]["chart"]
    return chart["name"], chart["version"]


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
        if member.name.split("/")[-1] == "Chart.yaml":
            chart = tar.extractfile(member)
            if chart is not None:
                content = chart.read()
                try:
                    chart_yaml = yaml.safe_load(content)
                    return chart_yaml["name"], chart_yaml["version"]
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
    chart_path = os.path.join(path, "Chart.yaml")
    with open(chart_path, "r") as fd:
        try:
            chart_yaml = yaml.safe_load(fd)
        except yaml.YAMLError as err:
            pytest.fail(f"error parsing '{path}': {err}")
    return chart_yaml["name"], chart_yaml["version"]


def extract_chart_tgz(src, dst, secrets, logger):
    """Extracts the chart tgz file into the target location under 'charts/' for PR submission tests

    Parameters:
    src (str): path to the test chart tgz
    dst (str): path to the extract destination, e.g. 'charts/partners/hashicorp/vault/0.13.0'
    """
    try:
        logger.info(f"Remove existing local '{dst}/src'")
        shutil.rmtree(f"{dst}/src")
    except FileNotFoundError:
        logger.info(f"'{dst}/src' does not exist")
    finally:
        with tarfile.open(src, "r") as fd:
            fd.extractall(dst)
            os.rename(f"{dst}/{secrets.chart_name}", f"{dst}/src")


def get_all_charts(charts_path: str, vendor_types: str) -> list:
    # TODO: Support `community` as vendor_type.
    """Gets charts with src or tgz under `charts/` given vendor_types and without report.

    Parameters:
    charts_path (str): path to the `charts/` directory
    vendor_types (str): vendor type to look for, any combination of `partner`, `redhat`, separated
        by commas, or `all` to run both `partner` and `redhat`.

    Returns:
    list: list of (vendor_type, vendor, chart_name, chart_version) tuples
    """
    ret = []
    # Pre-process vendor types
    vendor_types = vendor_types.replace("partner", "partners")
    vendor_types = [vt.strip() for vt in vendor_types.split(",")]
    vendor_types = list({"partners", "redhat", "all"}.intersection(set(vendor_types)))
    vendor_types = ["partners", "redhat"] if "all" in vendor_types else vendor_types

    # Iterate through `charts/` to find chart submission with src or tgz
    for vt in vendor_types:
        charts_path_vt = f"{charts_path}/{vt}"
        vendor_names = [
            name
            for name in os.listdir(charts_path_vt)
            if os.path.isdir(f"{charts_path_vt}/{name}")
        ]
        for vn in vendor_names:
            charts_path_vt_vn = f"{charts_path_vt}/{vn}"
            chart_names = [
                name
                for name in os.listdir(charts_path_vt_vn)
                if os.path.isdir(f"{charts_path_vt_vn}/{name}")
            ]
            for cn in chart_names:
                charts_path_vt_vn_cn = f"{charts_path_vt_vn}/{cn}"
                file_names = [name for name in os.listdir(charts_path_vt_vn_cn)]
                if "OWNERS" not in file_names:
                    continue
                chart_versions = [
                    name
                    for name in os.listdir(charts_path_vt_vn_cn)
                    if os.path.isdir(f"{charts_path_vt_vn_cn}/{name}")
                ]
                # Only interest in latest chart version
                if len(chart_versions) == 0:
                    continue
                cv = max(chart_versions)
                charts_path_vt_vn_cn_cv = f"{charts_path_vt_vn_cn}/{cv}"
                file_names = [name for name in os.listdir(charts_path_vt_vn_cn_cv)]
                if "report.yaml" not in file_names and (
                    f"{cn}-{cv}.tgz" in file_names or "src" in file_names
                ):
                    ret.append((vt, vn, cn, cv))
    return ret
