import json
import sys

import requests
import semantic_version
import yaml

sys.path.append("../")

INDEX_FILE = "https://charts.openshift.io/index.yaml"


def _make_http_request(url, body=None, params={}, headers={}, verbose=False):
    response = requests.get(url, params=params, headers=headers, json=body)
    if verbose:
        print(json.dumps(headers, indent=4, sort_keys=True))
        print(json.dumps(body, indent=4, sort_keys=True))
        print(json.dumps(params, indent=4, sort_keys=True))
        print(response.text)
    return response.text


def _load_index_yaml():
    yaml_text = _make_http_request(INDEX_FILE)
    dct = yaml.safe_load(yaml_text)
    return dct


def get_chart_info(tar_name):
    index_dct = _load_index_yaml()
    for entry, charts in index_dct["entries"].items():
        if tar_name.startswith(entry):
            for chart in charts:
                index_tar_name = f"{entry}-{chart['version']}"
                if tar_name == index_tar_name:
                    print(f"[INFO] match found: {tar_name}")
                    providerType = chart["annotations"][
                        "charts.openshift.io/providerType"
                    ]
                    provider = chart["annotations"]["charts.openshift.io/provider"]
                    return providerType, provider, chart["name"], chart["version"]
    print(f"[INFO] match not found: {tar_name}")
    return "", "", "", ""


def get_charts_info():
    chart_info_list = []

    index_dct = _load_index_yaml()
    for entry, charts in index_dct["entries"].items():
        for chart in charts:
            chart_info = {}
            chart_info["name"] = chart["name"]
            chart_info["version"] = chart["version"]
            chart_info["providerType"] = chart["annotations"][
                "charts.openshift.io/providerType"
            ]
            chart_info["provider"] = entry.removesuffix(f'-{chart["name"]}')
            # print(f'[INFO] found chart : {chart_info["provider"]} {chart["name"]} {chart["version"]} ')
            if "charts.openshift.io/supportedOpenShiftVersions" in chart["annotations"]:
                chart_info["supportedOCP"] = chart["annotations"][
                    "charts.openshift.io/supportedOpenShiftVersions"
                ]
            else:
                chart_info["supportedOCP"] = ""
            if "kubeVersion" in chart:
                chart_info["kubeVersion"] = chart["kubeVersion"]
            else:
                chart_info["kubeVersion"] = ""
            chart_info_list.append(chart_info)

    return chart_info_list


def get_latest_charts():
    chart_list = get_charts_info()

    print(f"{len(chart_list)} charts found in Index file")

    chart_in_process = {"name": ""}
    chart_latest_version = ""
    latest_charts = []

    for index, chart in enumerate(chart_list):
        chart_name = chart["name"]
        # print(f'[INFO] look for latest chart : {chart_name} {chart["version"]}')
        if chart_name == chart_in_process["name"]:
            new_version = semantic_version.Version.coerce(chart["version"])
            # print(f'   [INFO] compare chart versions : {new_version}({chart["version"]}) : {chart_latest_version}')
            if new_version > chart_latest_version:
                # print(f'   [INFO] a new latest chart version : {new_version}')
                chart_latest_version = new_version
                chart_in_process = chart
        else:
            if chart_in_process["name"] != "":
                # print(f'   [INFO] chart completed : {chart_in_process["name"]} {chart_in_process["version"]}')
                latest_charts.append(chart_in_process)

                # print(f'[INFO] new  chart found : {chart_name} {chart["version"]}')
                chart_in_process = chart
                chart_version = chart["version"]
                if chart_version.startswith("v"):
                    chart_version = chart_version[1:]
                chart_latest_version = semantic_version.Version.coerce(chart_version)
            else:
                chart_in_process = chart

        if index + 1 == len(chart_list):
            # print(f'   [INFO] last chart completed : {chart_in_process["name"]} {chart_in_process["version"]}')
            latest_charts.append(chart_in_process)

    return latest_charts
