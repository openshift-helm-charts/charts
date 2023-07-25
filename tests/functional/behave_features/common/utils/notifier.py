# -*- coding: utf-8 -*-
"""Utility module for sending chart owners notifications."""

import json
import os
import sys

import requests

from common.utils.setttings import *

endpoint_data = {}

CHECKS_FAILED = "checks failed"

def _set_endpoint_key(key, env_var):
    if key not in endpoint_data:
        if env_var in os.environ:
            endpoint_data[key] = os.environ[env_var]
        else:
            raise Exception(
                f"Environment variables {env_var} is required to connect to github")


def _set_endpoint():
    _set_endpoint_key("access_token", "GITHUB_AUTH_TOKEN")
    _set_endpoint_key("organization", "GITHUB_ORGANIZATION")
    _set_endpoint_key("repo", "GITHUB_REPO")


def _make_gihub_request(method, uri, body=None, params={}, headers={}, verbose=False):
    headers.update({"Authorization": f'Bearer {endpoint_data["access_token"]}',
                    "Accept": "application/vnd.github.v3+json"})

    url = f'{GITHUB_BASE_URL}/repos/{endpoint_data["organization"]}/{endpoint_data["repo"]}/{uri}'

    print(f"API url: {url}")
    method_map = {"get": requests.get,
                  "post": requests.post,
                  "put": requests.put,
                  "delete": requests.delete,
                  "patch": requests.patch}
    request_method = method_map[method]
    response = request_method(url, params=params, headers=headers, json=body)
    if verbose:
        print(json.dumps(headers, indent=4, sort_keys=True))
        print(json.dumps(body, indent=4, sort_keys=True))
        print(json.dumps(params, indent=4, sort_keys=True))
        print(response.text)
    response.raise_for_status()
    try:
        resp_json = response.json()
    except Exception:
        resp_json = None
    if resp_json and verbose:
        print(json.dumps(resp_json, indent=4, sort_keys=True))
    return resp_json

# Call this method directly if you are not creating a verification issue nor a version change issue.
def create_an_issue(title, description, assignees=[], labels=[]):
    uri = "issues"
    method = "post"
    body = {"title": title,
            "body": description,
            "assignees": assignees,
            "labels": labels}
    _make_gihub_request(method, uri, body=body, verbose=False)


def _verify_endpoint(access_token):
    if "repo" not in endpoint_data:
        raise Exception("GITHUB_REPO environment variable not defined")

    if "organization" not in endpoint_data:
        raise Exception("GITHUB_ORGANIZATION environment variable not defined")

    if access_token:
        endpoint_data["access_token"] = access_token


def create_verification_issue(chart, chart_owners, failure_type, notify_developers, pr_url, report_url, software_name, software_version, access_token=None, dry_run=False):
    """Create and issue with chart-verifier findings after a version change trigger.

    chart_name -- Name of the chart that was verified. Include version for more verbose information\n
    chart_owners -- Github IDs of the chart owners\n
    failure_type - Indication of the type of failure
    report_url -- URL or the report resulting from verification if applicable\n
    kube-version -- The kubeVersion attribute of the chart if it is bade.\n
    software_name -- Name of the software dependency that changed e.g, OCP and Chart Verifier\n
    software_version -- The softwared dependency version used\n
    access_token -- An optional github access token secret. If not passed will try to get from GITHUB_AUTH_TOKEN environment variable\
    dry-run -- Set if the test run is a dry-run.
    """


    title = f"Chart {chart}"
    if dry_run:
        title = f"Dry Run: Chart {chart}"

    if failure_type == CHECKS_FAILED:
        title = f"{title} has failures with {software_name} version {software_version}"
        report_result = "some chart checks have failed. Please review the failures and, if required, consider submitting a new chart version with the appropriate additions/corrections."
        body = (f"FYI @{' @'.join(notify_developers)}, in PR {pr_url} we triggered the chart certification workflow against chart {chart} because the workflow "
                f"now supports {software_name} version {software_version}. We have found that {report_result}. Check details in the report: "
                f"{report_url}, Chart owners are: {chart_owners}")
    else:
        title = f"{title} does not support {software_name} version {software_version}"
        body = (f"FYI @{' @'.join(notify_developers)}, we checked the OCP versions supported by {chart} because the workflow "
        f"now supports {software_name} version {software_version}. We have found that {failure_type}. Chart owners are: {chart_owners}")

    _set_endpoint()
    _verify_endpoint(access_token)
    create_an_issue(title, body)




def create_version_change_issue(chart_name, chart_owners, software_name, software_version, access_token=None):
    """Create and issue with new version of software dependencies supported by certitifcation program.

    chart_name -- Name of the chart afected. Include version for more verbose information
    chart_owners -- Github IDs of the chart owners\n
    software_name -- Name of the software dependency that changed e.g, OCP and Chart Verifier\n
    software_version -- The softwared dependency version used\n
    access_token -- An optional github access token secret. If not passed will try to get from GITHUB_AUTH_TOKEN environment variable\n
    """

    title = f"Action needed for {chart_name} after a certification dependency change"

    body = (f"FYI @{' @'.join(chart_owners)}, {software_name} {software_version} is now supported by the certification program. "
            "Consider submiting a new chart version.")

    _set_endpoint()
    _verify_endpoint(access_token)
    create_an_issue(title, body)


if __name__ == "__main__":
    # Collecting info interactively
    print("Enter the chart name: ")
    chart_name = sys.stdin.readline().strip()
    print("Enter chart owners: ")
    chart_owners = sys.stdin.readline().strip().split()
    print("Enter the github organization: ")
    organization = sys.stdin.readline().strip()
    print("Enter the github repo: ")
    repo = sys.stdin.readline().strip()

    # setting endpoint
    print(f"Creating custom issue in https://github.com/{organization}/{repo}")
    endpoint_data["organization"] = organization
    endpoint_data["repo"] = repo

    print("Enter the name of software dependency that changed: ")
    software_name = sys.stdin.readline().strip()
    print("Enter the version of software dependency that changed: ")
    software_version = sys.stdin.readline().strip()

    print("What type of issue are you creating (verification/version-change)?: ")
    issue_type = sys.stdin.readline().strip()

    if issue_type == "verification":
        print("Enter the report url: ")
        report_url = sys.stdin.readline().strip()
        print("Did the chart verification pass (yes/no)?: ")
        pass_answer = sys.stdin.readline().strip()
        pass_verification = pass_answer == "yes"
        create_verification_issue(chart_name, chart_owners, report_url,
                                  software_name, software_version, pass_verification=pass_verification)
    else:
        create_version_change_issue(
            chart_name, chart_owners, software_name, software_version)
