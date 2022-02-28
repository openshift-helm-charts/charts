"""
Used by github actions,specifically as part of the charts auto release process defined in
.github/workflow/release.yml.

Used to loosely determine if a submitted report is valid and has not been tampered with.

An invalid valid report:
- does not load as a yaml file.
- does not include  a "kind" attribute set the "verify-report" .
- does not include sections: "tool.metadata", "tool.chart", "results".

A tampered report is only determined if the chart-testing check has passed:
- certifiedOpenShiftVersions or testOpenShiftVersion contain valid semantic versions.
- certifiedOpenShiftVersions or testOpenShiftVersion specify an OCP version with helm support  (>=4.1.0)
- if the has-kubeversion check has also passed
  - v1.0 profile:
    - if a valid kubeVersion is specified in the chart it must include the certifiedOpenShiftVersions
  - v1.1 profile and later
    - a valid kubeVersion is specified in the chart
    - supportedOpenShiftVersions is consistent the kubeVersion specified in the chart
    - testOpenShiftVersion is within the supportedOpenShiftVersions

These are not comprehensive lists - other certification checks will preform further checks
"""

import sys
import os
import semantic_version
import docker
import json

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

sys.path.append('../')
from chartrepomanager import indexannotations
from report import report_info

MIN_SUPPORTED_OPENSHIFT_VERSION = semantic_version.SimpleSpec(">=4.1.0")
TESTED_VERSION_ANNOTATION = "charts.openshift.io/testedOpenShiftVersion"
CERTIFIED_VERSION_ANNOTATION = "charts.openshift.io/certifiedOpenShiftVersions"
SUPPORTED_VERSIONS_ANNOTATION = "charts.openshift.io/supportedOpenShiftVersions"
KUBE_VERSION_ATTRIBUTE = "kubeVersion"

def get_report_data(report_path):
    try:
        with open(report_path) as report_data:
            report_content = yaml.load(report_data,Loader=Loader)
        return True,report_content
    except Exception as err:
        print(f"Exception 2 loading file: {err}")
        return False,""

def get_result(report_data,check_name):
    outcome = False
    for result in report_data["results"]:
        if result["check"].endswith(check_name):
            if result["outcome"] == "PASS":
                outcome = True
            break
    return outcome

def get_chart_testing_result(report_data):
    return get_result(report_data,"/chart-testing")

def get_has_kubeversion_result(report_data):
    return get_result(report_data,"/has-kubeversion")

def get_profile_version(report_data):
    profile_version = "1.1"
    try:
        profile_version = report_data["metadata"]["tool"]["profile"]["version"][1:]
    except Exception:
        pass
    return profile_version

def report_is_valid(report_data):
    outcome = True

    if not "kind" in report_data or report_data["kind"] != "verify-report":
        print('[ERROR] kind attribute invalid or missing from report')
        return False

    if not "results" in report_data:
        print("No results section in report")
        outcome = False
    if not "metadata" in report_data:
        print("No metadata section in report")
        outcome = False
    else:
        if not  "tool" in report_data["metadata"]:
            print("No tool metadata  section in report")
            outcome = False
        if not "chart" in report_data["metadata"]:
            print("No tool chart  section in report")
            outcome = False

    return outcome


def validate(report_path):

    is_valid_yaml,report_data = get_report_data(report_path)

    if not is_valid_yaml:
        return False,f"Report is not valid yaml: {report_path}"

    if not report_is_valid(report_data):
        return False,f"Report is incomplete and cannot be processed: {report_path}"

    ## No value in checking if chart testing failed
    if get_chart_testing_result(report_data):

        profile_version_string = get_profile_version(report_data)

        try:
            profile_version = semantic_version.Version.coerce(profile_version_string)
            v1_0_profile = False
            if profile_version.major == 1 and profile_version.minor == 0:
                v1_0_profile = True
        except Exception:
            message = f"Invalid profile version in report : {profile_version_string}"
            print(message)
            return False,message


        annotations = report_info.get_report_annotations(report_path)

        if v1_0_profile:
            tested_version_annotation = CERTIFIED_VERSION_ANNOTATION
        else:
            tested_version_annotation = TESTED_VERSION_ANNOTATION

        if tested_version_annotation  in annotations:
            tested_version_string = annotations[tested_version_annotation]
        else:
            return False,f"No annotation provided for {tested_version_annotation}"

        try:
            tested_version = semantic_version.Version.coerce(tested_version_string)
            if tested_version not in MIN_SUPPORTED_OPENSHIFT_VERSION:
                return False,f"{tested_version_annotation} {tested_version_string} is not a supported OpenShift version."
        except ValueError:
            return False,f"{tested_version_annotation} {tested_version_string} is not a valid semantic version."

        if get_has_kubeversion_result:

            chart = report_info.get_report_chart(report_path)
            if KUBE_VERSION_ATTRIBUTE in chart:
                kube_supported_ocp_versions_string = indexannotations.getOCPVersions(chart[KUBE_VERSION_ATTRIBUTE])
                try:
                    kube_supported_versions =  semantic_version.NpmSpec(kube_supported_ocp_versions_string)
                except ValueError:
                    if v1_0_profile:
                        return True,""
                    else:
                        return False,f'Kube Version {chart[KUBE_VERSION_ATTRIBUTE]} translates to an invalid OCP version range {kube_supported_ocp_versions_string}'
            else:
                if v1_0_profile:
                    return True,""
                else:
                    return False,f'{KUBE_VERSION_ATTRIBUTE} missing from chart!'

            if tested_version not in kube_supported_versions:
                    return False,f"Tested OpenShift version {str(tested_version)} not within specified kube-versions : {kube_supported_ocp_versions_string}"

            if not v1_0_profile:

                if SUPPORTED_VERSIONS_ANNOTATION in annotations:
                    supported_versions_string = annotations[SUPPORTED_VERSIONS_ANNOTATION]
                    try:
                        supported_versions = semantic_version.NpmSpec(supported_versions_string)
                    except ValueError:
                         return False,f"{SUPPORTED_VERSIONS_ANNOTATION}: {supported_versions_string} is not a valid semantic version."
                else:
                    return False,f"Missing annotation in report: {SUPPORTED_VERSIONS_ANNOTATION}"

                if tested_version not in supported_versions:
                    return False,f"Tested OpenShift version {str(tested_version)} not within supported versions : {supported_versions_string}"

                if supported_versions_string and supported_versions_string != str(kube_supported_versions):
                     return False,f'Kube Version {chart[KUBE_VERSION_ATTRIBUTE]} -> {str(kube_supported_versions)} does not match supportedOpenShiftVersions: {supported_versions_string}'
    else:
        print("[INFO] Chart testing failed so skip report checking")

    return True,""

def generate_report(chart_dir,chart_file, kubeconfig, vendor_type):

    docker_command = f"report verify /charts/{chart_file}"

    if vendor_type:
        set_values = "profile.vendortype=%s" % vendor_type
        docker_command = "%s --set %s" % (docker_command, set_values)


    client = docker.from_env()

    print(f'[INFO] Call docker using imsge: {os.environ.get("VERIFIER_IMAGE")}, docker command: {docker_command}, chart: {chart_dir}/{chart_file}')
    print(f'[INFO] kubeconfig={kubeconfig}')

    try:
        output = client.containers.run(os.environ.get("VERIFIER_IMAGE"),docker_command,stdin_open=True,tty=True,stdout=True,auto_remove=True,
                                    volumes={chart_dir: {'bind': '/charts/', 'mode': 'rw'},kubeconfig: {'bind': '/kubeconfig', 'mode':'ro'}},
                                    environment={"KUBECONFIG": kubeconfig})
    except Exception as err:
        print(f"[ERROR]: exception from docker when generating the report: {err}")
        sys.exit(1)

    report_out = json.loads(output)
    return report_out

