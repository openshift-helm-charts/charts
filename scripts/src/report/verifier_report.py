"""
Used by github actions, specifically as part of the charts auto release process defined in
.github/workflow/release.yml.

Used to loosely determine if a submitted report is valid and has not been tampered with.

An invalid valid report:
- does not load as a yaml file.
- does not include a "kind" attribute set to "verify-report".
- does not include sections: "tool.metadata", "tool.chart", "results".

A tampered report is only determined if the chart-testing check has passed:
- certifiedOpenShiftVersions or testOpenShiftVersion contain valid semantic versions.
- certifiedOpenShiftVersions or testOpenShiftVersion specify an OCP version with helm support (>=4.1.0)
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

import semantic_version
import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

sys.path.append("../")
from report import report_info

MIN_SUPPORTED_OPENSHIFT_VERSION = semantic_version.SimpleSpec(">=4.1.0")
TESTED_VERSION_ANNOTATION = "charts.openshift.io/testedOpenShiftVersion"
CERTIFIED_VERSION_ANNOTATION = "charts.openshift.io/certifiedOpenShiftVersions"
SUPPORTED_VERSIONS_ANNOTATION = "charts.openshift.io/supportedOpenShiftVersions"
KUBE_VERSION_ATTRIBUTE = "kubeVersion"


class ConfigKeyMissing(Exception):
    pass


def get_report_data(report_path):
    """Load and returns the report data contained in report.yaml

    Args:
        report_path (str): Path to the report.yaml file.

    Returns:
        (bool, dict): A boolean indicating if the loading was successfull and the
                      content of the report.yaml file.
    """
    try:
        with open(report_path) as report_data:
            report_content = yaml.load(report_data, Loader=SafeLoader)
        return True, report_content
    except Exception as err:
        print(f"Exception 2 loading file: {err}")
        return False, ""


def get_result(report_data, check_name):
    """Parse the report.yaml content for the result of a given check.

    Args:
        report_data (dict): The content of the report.yaml file.
        check_name (str): The name of the check to get the result for.

    Returns:
        (bool, str): a boolean to True if the test passed, false otherwise
                     and the corresponding "reason" field.
    """
    outcome = False
    reason = "Not Found"
    for result in report_data["results"]:
        if result["check"].endswith(check_name):
            reason = result["reason"]
            if result["outcome"] == "PASS":
                outcome = True
            break
    return outcome, reason


def get_chart_testing_result(report_data):
    return get_result(report_data, "/chart-testing")


def get_has_kubeversion_result(report_data):
    return get_result(report_data, "/has-kubeversion")


def get_signature_is_valid_result(report_data):
    return get_result(report_data, "/signature-is-valid")


def get_profile_version(report_data):
    profile_version = "1.1"
    try:
        profile_version = report_data["metadata"]["tool"]["profile"]["version"][1:]
    except Exception:
        pass
    return profile_version


def get_web_catalog_only(report_data, raise_if_missing=False):
    """Check the delivery method set in the report data.

    Args:
        report_data (dict): Content of the report file. Typically this is the return value of the
            get_report_data function.
        raise_if_missing (bool, optional): Whether to raise an Exception if the delivery method is
            not set in the report data. If set to False, the function returns False.

    Raises:
        ConfigKeyMissing: if the key is not found in OWNERS and raise_if_missing is set to True

    """
    keyFound = False
    web_catalog_only = False
    try:
        if "webCatalogOnly" in report_data["metadata"]["tool"]:
            web_catalog_only = report_data["metadata"]["tool"]["webCatalogOnly"]
            keyFound = True
        if "providerControlledDelivery" in report_data["metadata"]["tool"]:
            web_catalog_only = report_data["metadata"]["tool"][
                "providerControlledDelivery"
            ]
            keyFound = True
    except Exception as err:
        print(
            f"Exception getting webCatalogOnly/providerControlledDelivery {err=}, {type(err)=}"
        )
        pass

    if not keyFound and raise_if_missing:
        raise ConfigKeyMissing(
            "Neither webCatalogOnly nor providerControlledDelivery keys were set"
        )

    return web_catalog_only


def get_package_digest(report_data):
    package_digest = None
    try:
        digests = report_data["metadata"]["tool"]["digests"]
        if "package" in digests:
            package_digest = digests["package"]
    except Exception as err:
        print(f"Exception getting package digest {err=}, {type(err)=}")
        pass
    return package_digest


def get_public_key_digest(report_data):
    """Get the public key digest from report.yaml

    Args:
        report_data (dict): the report.yaml content

    Returns:
        str: The public key digest from report.yaml. Set to None if not found.
    """
    public_key_digest = None
    try:
        digests = report_data["metadata"]["tool"]["digests"]
        if "publicKey" in digests:
            public_key_digest = digests["publicKey"]
    except Exception as err:
        print(f"Exception getting publicKey digest {err=}, {type(err)=}")
        pass
    return public_key_digest


def report_is_valid(report_data):
    """Check that the report.yaml contains the expected YAML structure

    Args:
        dict: The content of report.yaml

    Returns:
        bool: set to True if the report contains the correct structure, False otherwise.
    """
    outcome = True

    if "kind" not in report_data or report_data["kind"] != "verify-report":
        print("[ERROR] kind attribute invalid or missing from report")
        return False

    if "results" not in report_data:
        print("No results section in report")
        outcome = False
    if "metadata" not in report_data:
        print("No metadata section in report")
        outcome = False
    else:
        if "tool" not in report_data["metadata"]:
            print("No tool metadata  section in report")
            outcome = False
        if "chart" not in report_data["metadata"]:
            print("No tool chart  section in report")
            outcome = False

    return outcome


def validate(report_path, ocp_version_range):
    """Validate report.yaml by running a serie of checks.

    * Checks that the report.yaml contains valid YAML.
    * Checks that the report.yaml contains the correct structure.
    * Checks that the Chart has been successully tested (result of /chart-testing).
    * Checks that the profile version used is valid SemVer.
    * Checks that the expected annotation is present.
    * Checks that the reported version of OCP and Kubernetes are valid and are coherent.

    Args:
        report_path (str): Path to the report.yaml file
        ocp_version_range (str): Range of supported OCP versions

    Returns:
        (bool, str): if the checks all passed, this returns a bool set to True and an
                     empty str. Otherwise, this returns a bool set to True and the
                     corresponding error message.
    """
    is_valid_yaml, report_data = get_report_data(report_path)

    if not is_valid_yaml:
        return False, f"Report is not valid yaml: {report_path}"

    if not report_is_valid(report_data):
        return False, f"Report is incomplete and cannot be processed: {report_path}"

    # No value in checking if chart testing failed
    chart_testing_outcome, _ = get_chart_testing_result(report_data)
    if chart_testing_outcome:
        profile_version_string = get_profile_version(report_data)

        try:
            profile_version = semantic_version.Version.coerce(profile_version_string)
            v1_0_profile = False
            if profile_version.major == 1 and profile_version.minor == 0:
                v1_0_profile = True
        except ValueError:
            message = f"Invalid profile version in report : {profile_version_string}"
            print(message)
            return False, message

        annotations = report_info.get_report_annotations(report_path)

        if v1_0_profile:
            tested_version_annotation = CERTIFIED_VERSION_ANNOTATION
        else:
            tested_version_annotation = TESTED_VERSION_ANNOTATION

        if tested_version_annotation in annotations:
            tested_version_string = annotations[tested_version_annotation]
        else:
            return False, f"No annotation provided for {tested_version_annotation}"

        try:
            tested_version = semantic_version.Version.coerce(tested_version_string)
            if tested_version not in MIN_SUPPORTED_OPENSHIFT_VERSION:
                return (
                    False,
                    f"{tested_version_annotation} {tested_version_string} is not a supported OpenShift version.",
                )
        except ValueError:
            return (
                False,
                f"{tested_version_annotation} {tested_version_string} is not a valid semantic version.",
            )

        has_kubeversion_outcome, _ = get_chart_testing_result(report_data)
        if has_kubeversion_outcome:
            if not v1_0_profile:
                chart = report_info.get_report_chart(report_path)
                kube_supported_versions = semantic_version.NpmSpec(ocp_version_range)

                if tested_version not in kube_supported_versions:
                    return (
                        False,
                        f"Tested OpenShift version {str(tested_version)} not within specified kube-versions : {ocp_version_range}",
                    )

                if SUPPORTED_VERSIONS_ANNOTATION in annotations:
                    supported_versions_string = annotations[
                        SUPPORTED_VERSIONS_ANNOTATION
                    ]
                    try:
                        supported_versions = semantic_version.NpmSpec(
                            supported_versions_string
                        )
                    except ValueError:
                        return (
                            False,
                            f"{SUPPORTED_VERSIONS_ANNOTATION}: {supported_versions_string} is not a valid semantic version.",
                        )
                else:
                    return (
                        False,
                        f"Missing annotation in report: {SUPPORTED_VERSIONS_ANNOTATION}",
                    )

                if tested_version not in supported_versions:
                    return (
                        False,
                        f"Tested OpenShift version {str(tested_version)} not within supported versions : {supported_versions_string}",
                    )

                if supported_versions_string and supported_versions_string != str(
                    kube_supported_versions
                ):
                    return (
                        False,
                        f"Kube Version {chart[KUBE_VERSION_ATTRIBUTE]} -> {str(kube_supported_versions)} does not match supportedOpenShiftVersions: {supported_versions_string}",
                    )
    else:
        print("[INFO] Chart testing failed so skip report checking")

    return True, ""
