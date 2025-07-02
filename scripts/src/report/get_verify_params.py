import argparse
import os
import sys

sys.path.append("../")
from chartprreview import chartprreview
from signedchart import signedchart
from tools import gitutils


def get_report_full_path(category, organization, chart, version):
    return os.path.join(
        os.getcwd(), get_report_relative_path(category, organization, chart, version)
    )


def get_report_relative_path(category, organization, chart, version):
    return os.path.join("charts", category, organization, chart, version, "report.yaml")


def generate_verify_options(directory, category, organization, chart, version):
    print("[INFO] Generate verify options. %s, %s, %s" % (organization, chart, version))
    src = os.path.join(
        os.getcwd(), "charts", category, organization, chart, version, "src"
    )
    report_path = get_report_full_path(category, organization, chart, version)
    tar = os.path.join(
        os.getcwd(),
        "charts",
        category,
        organization,
        chart,
        version,
        f"{chart}-{version}.tgz",
    )

    print(f"[INF0] report path exists = {os.path.exists(report_path)} : {report_path}")
    print(f"[INF0] src path exists = {os.path.exists(src)} : {src}")
    print(f"[INF0] tarball path  = {os.path.exists(tar)} : {tar}")

    flags = f"--set profile.vendortype={category}"
    cluster_needed = True
    report_provided = False
    if os.path.exists(report_path):
        print("[INFO] report is included")
        flags = f"{flags} -e has-readme"
        cluster_needed = False
        report_provided = True

    if os.path.exists(src) and not os.path.exists(tar):
        print("[INFO] chart src included")
        return flags, src, True, cluster_needed, report_provided
    elif os.path.exists(tar) and not os.path.exists(src):
        print("[INFO] tarball included")
        if not os.path.exists(report_path):
            owners_file = os.path.join(
                os.getcwd(), "charts", category, organization, chart, "OWNERS"
            )
            signed_flags = signedchart.get_verifier_flags(tar, owners_file, directory)
            if signed_flags:
                print(f"[INFO] include flags for signed chart: {signed_flags}")
                flags = f"{flags} {signed_flags}"
        return flags, tar, True, cluster_needed, report_provided
    elif os.path.exists(tar) and os.path.exists(src):
        msg = "[ERROR] Both chart source directory and tarball should not exist"
        chartprreview.write_error_log(directory, msg)
        sys.exit(1)
    else:
        print("[INFO] report only")
        return "", "", False, False, report_provided


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--api-url",
        dest="api_url",
        type=str,
        required=True,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-d",
        "--directory",
        dest="directory",
        type=str,
        required=True,
        help="artifact directory for archival",
    )

    args = parser.parse_args()

    category, organization, chart, version = chartprreview.get_modified_charts(
        args.directory, args.api_url
    )

    (
        flags,
        chart_uri,
        report_needed,
        cluster_needed,
        report_provided,
    ) = generate_verify_options(args.directory, category, organization, chart, version)
    gitutils.add_output("report_provided", report_provided)
    gitutils.add_output(
        "provided_report_relative_path",
        get_report_relative_path(category, organization, chart, version),
    )
    gitutils.add_output("report_needed", report_needed)
    gitutils.add_output("cluster_needed", cluster_needed)
    if report_needed:
        gitutils.add_output("verify_args", flags)
        gitutils.add_output("verify_uri", chart_uri)
