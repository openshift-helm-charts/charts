
import os
import sys
import docker
import json
import subprocess

REPORT_ANNOTATIONS = "annotations"
REPORT_RESULTS = "results"
REPORT_DIGESTS = "digests"
REPORT_METADATA = "metadata"

def _get_report_info(report_path, report_info_path,info_type, profile_type, profile_version):

    if report_info_path and len(report_info_path) > 0:
        print(f"[INFO] Using existing report info: {report_info_path}")
        report_out = json.load(open(report_info_path))
    else:
        command = f"report"
        set_values = ""
        if profile_type:
            set_values = "profile.vendortype=%s" % profile_type
        if profile_version:
            if set_values:
                set_values = "%s,profile.version=%s" % (set_values,profile_version)
            else:
                set_values = "profile.version=%s" % profile_version

        if os.environ.get("VERIFIER_IMAGE"):
            print(f"[INFO] Generate report info using docker  : {report_path}")
            docker_command = f"{command} {info_type} /charts/{os.path.basename(report_path)}"
            if set_values:
                docker_command = "%s --set %s" % (docker_command, set_values)

            client = docker.from_env()
            report_directory = os.path.dirname(os.path.abspath(report_path))
            print(f'Call docker using image: {os.environ.get("VERIFIER_IMAGE")}, docker command: {docker_command}, report directory: {report_directory}')
            output = client.containers.run(os.environ.get("VERIFIER_IMAGE"),docker_command,stdin_open=True,tty=True,stdout=True,volumes={report_directory: {'bind': '/charts/', 'mode': 'rw'}})
        else:
            print(f"[INFO] Generate report info using chart-verifier on path : {os.path.abspath(report_path)}")
            if set_values:
                out = subprocess.run(["chart-verifier",command,info_type,"--set",set_values,os.path.abspath(report_path)],capture_output=True)
            else:
                out = subprocess.run(["chart-verifier",command,info_type,os.path.abspath(report_path)],capture_output=True)
            output = out.stdout.decode("utf-8")

        try:
            report_out = json.loads(output)
        except BaseException as err:
            print(f"[ERROR] loading report output: /n{output}")
            print(f"[ERROR] exception was: {err=}, {type(err)=}")
            sys.exit(1)

    if not info_type in report_out:
        print(f"Error extracting {info_type} from the report:", report_out.strip())
        sys.exit(1)

    if info_type == REPORT_ANNOTATIONS:
        annotations = {}
        for report_annotation in report_out[REPORT_ANNOTATIONS]:
            annotations[report_annotation["name"]] = report_annotation["value"]

        return annotations

    return report_out[info_type]


def get_report_annotations(report_path=None,report_info_path=None):
    annotations = _get_report_info(report_path,report_info_path,REPORT_ANNOTATIONS,"","")
    print("[INFO] report annotations : %s" % annotations)
    return annotations


def get_report_results(report_path=None, profile_type=None, profile_version=None,report_info_path=None):
    results = _get_report_info(report_path,report_info_path,REPORT_RESULTS,profile_type,profile_version)
    print("[INFO] report results : %s" % results)
    results["failed"] = int(results["failed"])
    results["passed"] = int(results["passed"])
    return results
    
def get_report_digests(report_path=None,report_info_path=None):
    digests = _get_report_info(report_path,report_info_path,REPORT_DIGESTS,"","")
    print("[INFO] report digests : %s" % digests)
    return digests

def get_report_metadata(report_path=None,report_info_path=None):
    metadata = _get_report_info(report_path,report_info_path,REPORT_METADATA,"","")
    print("[INFO] report metadata : %s" % metadata)
    return metadata

def get_report_chart_url(report_path=None,report_info_path=None):
     metadata = _get_report_info(report_path,report_info_path,REPORT_METADATA,"","")
     print("[INFO] report chart-uri : %s" % metadata["chart-uri"])
     return metadata["chart-uri"]

def get_report_chart(report_path=None,report_info_path=None):
     metadata = _get_report_info(report_path,report_info_path,REPORT_METADATA,"","")
     print("[INFO] report chart : %s" % metadata["chart"])
     return metadata["chart"]

def main():

    print("\n\n\n\nDocker image results:\n")
    os.environ["VERIFIER_IMAGE"] = "quay.io/redhat-certification/chart-verifier:main"
    get_report_results("./report.yaml","","")
    get_report_results("./report.yaml","community","v1.1")
    get_report_digests("./report.yaml")
    get_report_metadata("./report.yaml")
    get_report_annotations("./report.yaml")
    get_report_chart_url("./report.yaml")
    get_report_chart("./report.yaml")

    print("\n\n\n\nverifier command results:\n")
    os.environ["VERIFIER_IMAGE"] = ""
    get_report_results("./report.yaml","","")
    get_report_results("./report.yaml","community","v1.1")
    get_report_digests("./report.yaml")
    get_report_metadata("./report.yaml")
    get_report_annotations("./report.yaml")
    get_report_chart_url("./report.yaml")
    get_report_chart("./report.yaml")

    print("\n\n\n\nexisting report results:\n")
    get_report_results(report_info_path="./report_info.json")
    get_report_digests(report_info_path="./report_info.json")
    get_report_metadata(report_info_path="./report_info.json")
    get_report_annotations(report_info_path="./report_info.json")
    get_report_chart_url(report_info_path="./report_info.json")
    get_report_chart(report_info_path="./report_info.json")


if __name__ == '__main__':
    main()


