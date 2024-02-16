"""This files downloads and updates the Helm repository index data
"""

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import requests
import yaml
from environs import Env

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader


def _decode_chart_entry(chart_entry_encoded):
    """Decode the base64 encoded index entry to add.

    Args:
        chart_entry_encoded (str): base64 encode index entry for this chart

    Returns:
        dict: Decoded index entry

    """
    chart_entry_bytes = base64.b64decode(chart_entry_encoded)
    chart_entry_str = chart_entry_bytes.decode()

    return json.loads(chart_entry_str)


def download_index(index_file, repository, branch):
    """Download the index file to disk and retrieve its content.

    Args:
        index_file (str): Path to the index file to update
        repository (str): Name of the git Repository
        branch (str): Git branch that hosts the Helm repository index

    Returns:
        dict: The current content of the index
    """
    print(f"Downloading {index_file}")
    r = requests.get(
        f"https://raw.githubusercontent.com/{repository}/{branch}/{index_file}"
    )
    now = datetime.now(timezone.utc).astimezone().isoformat()

    if r.status_code == 200:
        data = yaml.load(r.text, Loader=Loader)
        data["generated"] = now
    else:
        data = {"apiVersion": "v1", "generated": now, "entries": {}}

    return data


def update_index(
    index_data,
    version,
    chart_url,
    chart_entry,
    web_catalog_only,
):
    """Update the Helm repository index file

    Args:
        index_data (dict): Content of the Helm repo index
        version (str): The version of the chart (ex: 1.4.0)
        chart_url (str): URL of the Chart
        chart_entry (dict): Index entry to add
        web_catalog_only (bool): Set to True if the provider has chosen the Web Catalog
                                 Only option.

    """
    now = datetime.now(timezone.utc).astimezone().isoformat()

    print("[INFO] Updating the chart entry with new version")
    crtentries = []
    entry_name = os.environ.get("CHART_ENTRY_NAME")
    if not entry_name:
        print("[ERROR] Internal error: missing chart entry name")
        sys.exit(1)
    d = index_data["entries"].get(entry_name, [])
    for v in d:
        if v["version"] == version:
            continue
        crtentries.append(v)

    chart_entry["urls"] = [chart_url]
    if not web_catalog_only:
        set_package_digest(chart_entry, chart_url)
    chart_entry["annotations"]["charts.openshift.io/submissionTimestamp"] = now
    crtentries.append(chart_entry)
    index_data["entries"][entry_name] = crtentries


def set_package_digest(chart_entry, chart_url):
    """Check that the digest of the provided chart matches the digest of the chart that
    has been uploaded in the GitHub release.

    Note that this  is the reason why the GitHub release must have been created before
    updating the index.

    Args:
        chart_entry (dict): Index entry to add
        chart_url (str): URL of the Chart

    """
    print("[INFO] set package digests.")

    head = requests.head(chart_url, allow_redirects=True)
    print(f"[DEBUG]: tgz url : {chart_url}")
    print(f"[DEBUG]: response code from head request: {head.status_code}")

    target_digest = ""
    if head.status_code == 200:
        response = requests.get(chart_url, allow_redirects=True)
        print(f"[DEBUG]: response code get request: {response.status_code}")
        target_digest = hashlib.sha256(response.content).hexdigest()
        print(f"[DEBUG]: calculated digest : {target_digest}")

    pkg_digest = ""
    if "digest" in chart_entry:
        pkg_digest = chart_entry["digest"]
        print(f"[DEBUG]: digest in report : {pkg_digest}")

    if target_digest:
        if not pkg_digest:
            # Digest was computed but not passed
            chart_entry["digest"] = target_digest
        elif pkg_digest != target_digest:
            # Digest was passed and computed but differ
            raise Exception(
                "Found an integrity issue. SHA256 digest passed does not match SHA256 digest computed."
            )
    elif not pkg_digest:
        # Digest was not passed and could not be computed
        raise Exception(
            "Was unable to compute SHA256 digest, please ensure chart url points to a chart package."
        )


def write_index_file(index_data, index_file):
    """Write the new content of the index to file

    Args:
        index_data (dict): Content of the Helm repo index
        index_file (str): Path to the index file to update

    """
    out = yaml.dump(index_data, Dumper=Dumper)
    print(f"{index_file} content:\n", out)
    with open(index_file, "w") as fd:
        fd.write(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b",
        "--index-branch",
        dest="index_branch",
        type=str,
        required=True,
        help="Git branch that hosts the Helm repository index",
    )
    parser.add_argument(
        "-f",
        "--index-file",
        dest="index_file",
        type=str,
        required=True,
        help="index file to update",
    )
    parser.add_argument(
        "-r",
        "--repository",
        dest="repository",
        type=str,
        required=True,
        help="Name of the git Repository",
    )
    parser.add_argument(
        "-u",
        "--chart-url",
        dest="chart_url",
        type=str,
        required=True,
        help="URL where the Chart is available",
    )
    parser.add_argument(
        "-e",
        "--chart-entry",
        dest="chart_entry_encoded",
        type=str,
        required=True,
        help="Index entry to add",
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        type=str,
        required=True,
        help="Version of the chart being added",
    )
    args = parser.parse_args()

    chart_entry = _decode_chart_entry(args.chart_entry_encoded)

    env = Env()
    web_catalog_only = env.bool("WEB_CATALOG_ONLY", False)

    index_data = download_index(args.index_file, args.repository, args.index_branch)
    update_index(
        index_data,
        args.version,
        args.chart_url,
        chart_entry,
        web_catalog_only,
    )
    write_index_file(index_data, args.index_file)
