
import re
import os
import sys
import docker
import argparse
import subprocess
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

def getReport(report_path):
    try:
        report = yaml.load(open(report_path), Loader=Loader)
    except yaml.scanner.ScannerError as err:
        msg = "[ERROR] YAML error: {0}".format(err)
        write_error_log(directory, msg)
        sys.exit(1)
    except:
        msg = "[ERROR] Unexpected error:", sys.exc_info()[0]
        write_error_log(directory, msg)
        sys.exit(1)
    return report

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

    print(f"[INFO] report {info_type} :",report_out)

    if not report_out[info_type]:
        print(f"Error extracting {info_type} from the report:", r.strip())
        sys.exit(1)

    if info_type == REPORT_ANNOTATIONS:
        annotations = {}
        for report_annotation in report_out[REPORT_ANNOTATIONS]:
            annotations[report_annotation["name"]] = report_annotation["value"]

        return annotations

    #return json.dumps(report_out[info_type])
    return report_out[info_type]


def getReportAnnotations(report_path):
    return getReportInfo(report_path,REPORT_ANNOTATIONS,"","")

def getReportResults(report_path,profile_type,profile_version):
    results = getReportInfo(report_path,REPORT_RESULTS,profile_type,profile_version)
    results["failed"] = int(results["failed"])
    results["passed"] = int(results["passed"])
    return results
    
def getReportDigests(report_path):
    return getReportInfo(report_path,REPORT_DIGESTS,"","")

def getReportMetadata(report_path):
    return getReportInfo(report_path,REPORT_METADATA,"","")

def getReportChartUrl(report_path):
     metadata = getReportInfo(report_path,REPORT_METADATA,"","")
     return metadata["chart-uri"]

def getReportChart(report_path):
     metadata = getReportInfo(report_path,REPORT_METADATA,"","")
     return metadata["chart"]




