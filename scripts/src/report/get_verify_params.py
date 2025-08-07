import argparse
import os
import sys

from submission import submission, validate

sys.path.append("../")
from chartprreview import chartprreview
from signedchart import signedchart
from tools import gitutils


def generate_verify_options(directory: str, s: submission.Submission):
    """Prepare a set of GitHub outputs, including the options for chart-verifier verify

    Args:
        directory (str): Local directory in which to write the error logs
        s (Submission): Submitted GitHub Pull Request

    Returns:
        str: The flags used by chert-verifier verify command
        str: The path to the chart (tarball or source)
        bool: Whether a report needs to be generated
        bool: Whether a cluster is needed

    """
    print("[INFO] Generate verify options")

    flags = f"--set profile.vendortype={s.chart.category}"
    cluster_needed = True
    if s.report.found:
        print("[INFO] report is included")
        flags = f"{flags} -e has-readme"
        cluster_needed = False

    if s.source.found and not s.tarball.found:
        print("[INFO] chart src included")
        src_full_path = os.path.join(os.getcwd(), s.source.path)
        return flags, src_full_path, True, cluster_needed
    elif s.tarball.found and not s.source.found:
        print("[INFO] tarball included")
        tarball_full_path = os.path.join(os.getcwd(), s.tarball.path)
        if not s.report.found:
            full_owners_path = os.path.join(os.getcwd(), s.chart.get_owners_path())
            signed_flags = signedchart.get_verifier_flags(
                tarball_full_path, full_owners_path, directory
            )
            if signed_flags:
                print(f"[INFO] include flags for signed chart: {signed_flags}")
                flags = f"{flags} {signed_flags}"
        return flags, tarball_full_path, True, cluster_needed
    elif s.tarball.found and s.source.found:
        msg = "[ERROR] Both chart source directory and tarball should not exist"
        chartprreview.write_error_log(directory, msg)
        sys.exit(1)
    else:
        print("[INFO] report only")
        return "", "", False, False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        dest="directory",
        type=str,
        required=True,
        help="artifact directory for archival",
    )

    args = parser.parse_args()

    submission_path = os.environ.get("SUBMISSION_PATH")
    s = validate.read_submission_from_file(articact_path=submission_path)

    flags, chart_uri, report_needed, cluster_needed = generate_verify_options(
        args.directory, s
    )
    gitutils.add_output("report_provided", s.report.found)
    gitutils.add_output("provided_report_relative_path", s.report.path)
    gitutils.add_output("report_needed", report_needed)
    gitutils.add_output("cluster_needed", cluster_needed)
    if report_needed:
        gitutils.add_output("verify_args", flags)
        gitutils.add_output("verify_uri", chart_uri)
