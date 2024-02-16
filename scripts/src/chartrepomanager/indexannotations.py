import sys

import semantic_version

sys.path.append("../")
from report import report_info


def getIndexAnnotations(ocp_version_range, report_path):
    """Get the annotations set in the report file.

    This function replaces the certifiedOpenShiftVersions annotation with the
    testedOpenShiftVersion annotation. It also adds the
    supportedOpenShiftVersions in the case it is not already set.

    It leaves all other annotations untouched.

    Args:
        ocp_version_range (str): Range of supported OCP versions
        report_path (str): Path to the report.yaml file

    Returns:
        dict: mapping of annotations names to their values
    """
    annotations = report_info.get_report_annotations(report_path)

    set_annotations = {}
    OCPSupportedSet = False
    for annotation in annotations:
        if annotation == "charts.openshift.io/certifiedOpenShiftVersions":
            full_version = annotations[annotation]
            if full_version != "N/A" and semantic_version.validate(full_version):
                ver = semantic_version.Version(full_version)
                set_annotations["charts.openshift.io/testedOpenShiftVersion"] = (
                    f"{ver.major}.{ver.minor}"
                )
            else:
                set_annotations["charts.openshift.io/testedOpenShiftVersion"] = (
                    annotations[annotation]
                )
        else:
            if annotation == "charts.openshift.io/supportedOpenShiftVersions":
                OCPSupportedSet = True
            set_annotations[annotation] = annotations[annotation]

    if not OCPSupportedSet:
        set_annotations["charts.openshift.io/supportedOpenShiftVersions"] = (
            ocp_version_range
        )

    return set_annotations
