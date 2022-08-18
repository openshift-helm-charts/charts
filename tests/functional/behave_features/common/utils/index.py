
import logging
import semantic_version
import sys

sys.path.append('../../../../../scripts/src')
from chartrepomanager import indexannotations
from indexfile import index



def check_index_entries(ocpVersion):

    all_chart_list = index.get_latest_charts()
    failed_chart_list = []

    OCP_VERSION = semantic_version.Version.coerce(ocpVersion)

    for chart in all_chart_list:
        if "supportedOCP" in chart and chart["supportedOCP"] != "N/A" and chart["supportedOCP"] != "":
            if OCP_VERSION in semantic_version.NpmSpec(chart["supportedOCP"]):
                logging.info(f'PASS: Chart {chart["name"]} {chart["version"]} supported OCP version {chart["supportedOCP"]} includes: {OCP_VERSION}')
            else:
                chart["message"] = f'chart {chart["name"]} {chart["version"]} supported OCP version {chart["supportedOCP"]} does not include latest OCP version {OCP_VERSION}'
                logging.info(f'   ERROR: Chart {chart["name"]} {chart["version"]} supported OCP version {chart["supportedOCP"]} does not include {OCP_VERSION}')
                failed_chart_list.append(chart)
        elif "kubeVersion" in chart and chart["kubeVersion"] != "":
            supportedOCPVersion = indexannotations.getOCPVersions(chart["kubeVersion"])
            if OCP_VERSION in semantic_version.NpmSpec(supportedOCPVersion):
                logging.info(f'PASS: Chart {chart["name"]} {chart["version"]} kubeVersion  {chart["kubeVersion"]} (OCP: {supportedOCPVersion}) includes OCP version: {OCP_VERSION}')
            else:
                chart["message"] = f'chart {chart["name"]} {chart["version"]} kubeVersion {chart["kubeVersion"]} (OCP: {supportedOCPVersion}) does not include latest OCP version {OCP_VERSION}'
                logging.info(f'   ERROR: Chart {chart["name"]} {chart["version"]} kubeVersion {chart["kubeVersion"]} (OCP: {supportedOCPVersion}) does not include {OCP_VERSION}')
                failed_chart_list.append(chart)

    return failed_chart_list







