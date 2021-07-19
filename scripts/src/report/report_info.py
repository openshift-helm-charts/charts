
import os
import sys
import docker
import logging
import json
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

REPORT_ANNOTATIONS = "annotations"
REPORT_RESULTS = "results"
REPORT_DIGESTS = "digests"
REPORT_METADATA= "metadata"

def getReportInfo(report_path,info_type,profile_type,profile_version):

    docker_command = "report " + info_type + " charts/"+os.path.basename(report_path)

    set_values = ""
    if profile_type:
        set_values = "profile.vendortype="+profile_type
    if profile_version:
        if set_values:
            set_values = set_values + ","
        set_values = set_values + "profile.version="+profile_version

    if set_values:
        docker_command += " --set " + set_values

    client = docker.from_env()
    report_directory = os.path.dirname(os.path.abspath(report_path))
    output = client.containers.run(os.environ.get("VERIFIER_IMAGE"),docker_command,stdin_open=True,tty=True,stderr=True,volumes={report_directory: {'bind': '/charts/', 'mode': 'rw'}})
    report_out = json.loads(output)

    if not info_type in report_out:
        print(f"Error extracting {info_type} from the report:", r.strip())
        sys.exit(1)

    if info_type == REPORT_ANNOTATIONS:
        annotations = {}
        for report_annotation in report_out[REPORT_ANNOTATIONS]:
            annotations[report_annotation["name"]] = report_annotation["value"]

        return annotations

    return report_out[info_type]


def getReportAnnotations(report_path):
    annotations = getReportInfo(report_path,REPORT_ANNOTATIONS,"","")
    print("[INFO] report annotations :",annotations)
    return annotations

def getReportResults(report_path,profile_type,profile_version):
    results = getReportInfo(report_path,REPORT_RESULTS,profile_type,profile_version)
    print("[INFO] report results :",results)
    results["failed"] = int(results["failed"])
    results["passed"] = int(results["passed"])
    return results
    
def getReportDigests(report_path):
    digests = getReportInfo(report_path,REPORT_DIGESTS,"","")
    print("[INFO] report digests :",digests)
    return digests

def getReportMetadata(report_path):
    metadata = getReportInfo(report_path,REPORT_METADATA,"","")
    print("[INFO] report digests :",digests)
    return metadata

def getReportChartUrl(report_path):
     metadata = getReportInfo(report_path,REPORT_METADATA,"","")
     print("[INFO] report chart-uri :",metadata["chart-uri"])
     return metadata["chart-uri"]

def getReportChart(report_path):
     metadata = getReportInfo(report_path,REPORT_METADATA,"","")
     print("[INFO] report chart :",metadata["chart"])
     return metadata["chart"]




