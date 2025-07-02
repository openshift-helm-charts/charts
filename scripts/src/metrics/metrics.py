import argparse
import itertools
import os
import re
import sys

import analytics
import requests
from github import Github

sys.path.append("../")
from collections import OrderedDict

from indexfile import index
from pullrequest import prepare_pr_comment as pr_comment
from reporegex import matchers

file_pattern = re.compile(
    matchers.submission_path_matcher(strict_categories=False) + r"/.*"
)
chart_downloads_event = "Chart Downloads v1.0"
ignore_users = [
    "zonggen",
    "mmulholla",
    "dperaza4dustbit",
    "openshift-helm-charts-bot",
    "baijum",
    "tisutisu",
    "rhrivero",
    "Kartikey-star",
]
pr_submission = "PR Submission v1.0"
pr_merged = "PR Merged v1.0"
pr_outcome = "PR Outcome v1.0"
charts = "charts"
xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"


def parse_response(response):
    result = []
    for obj in response:
        if "name" in obj and "assets" in obj:
            for asset in obj["assets"]:
                if asset["name"].endswith(".tgz"):
                    release = {
                        "name": obj["name"],
                        "asset": {asset.get("name"): asset.get("download_count", 0)},
                    }
                    result.append(release)
    return result


def get_release_metrics():
    result = []
    for i in itertools.count(start=1):
        request_headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        response = requests.get(
            f"https://api.github.com/repos/openshift-helm-charts/charts/releases?per_page=100&page={i}",
            headers=request_headers,
        )

        if not 200 <= response.status_code < 300:
            print(
                f"[ERROR] unexpected response getting release data : {response.status_code} : {response.reason}"
            )
            sys.exit(1)

        response_json = response.json()
        if xRateLimit in response.headers:
            print(f"[DEBUG] {xRateLimit} : {response.headers[xRateLimit]}")
        if xRateRemain in response.headers:
            print(f"[DEBUG] {xRateRemain}  : {response.headers[xRateRemain]}")

        if "message" in response_json:
            print(f'[ERROR] getting pr files: {response_json["message"]}')
            sys.exit(1)

        if len(response_json) == 0:
            break
        result.extend(response_json)
    return parse_response(result)


def send_release_metrics(write_key, downloads, prefix):
    metrics = {}
    chart_downloads = []
    chart_downloads_latest = []
    for release in downloads:
        _, provider, chart, _ = index.get_chart_info(release.get("name"))
        if len(provider) > 0:
            if provider not in metrics:
                metrics[provider] = {}
            if chart not in metrics[provider]:
                metrics[provider][chart] = {}

            for key in release.get("asset"):
                metrics[provider][chart][key] = release.get("asset")[key]

    for provider in metrics:
        for chart in metrics[provider]:
            ordered_download_perChart = OrderedDict(
                sorted(
                    metrics[provider][chart].items(), key=lambda i: i[1], reverse=True
                )
            )
            for key, value in ordered_download_perChart.items():
                chart_downloads_latest.append(
                    {"downloads": value, "name": key, "provider": provider}
                )
                break
            for key, value in metrics[provider][chart].items():
                chart_downloads.append(
                    {"downloads": value, "name": key, "provider": provider}
                )
    chart_downloads.sort(key=lambda k: k["downloads"], reverse=True)
    chart_downloads_latest.sort(key=lambda k: k["downloads"], reverse=True)

    for x in range(len(chart_downloads)):
        send_download_metric(
            write_key,
            chart_downloads[x]["provider"],
            chart_downloads[x]["downloads"],
            chart_downloads[x]["name"],
            x + 1,
            prefix,
        )

    for x in range(5):
        send_top_five_metric(
            write_key,
            chart_downloads_latest[x]["provider"],
            chart_downloads_latest[x]["downloads"],
            chart_downloads_latest[x]["name"],
            x + 1,
            prefix,
        )


def send_download_metric(write_key, partner, downloads, artifact_name, rank, prefix):
    id = f"{prefix}-{partner}-{artifact_name}"
    properties = {"downloads": downloads, "rank": rank, "name": artifact_name}

    send_metric(write_key, id, chart_downloads_event, properties)


def send_top_five_metric(write_key, partner, downloads, artifact_name, rank, prefix):
    id = f"{prefix}-top5"
    properties = {"downloads": downloads, "rank": rank, "name": artifact_name}

    send_metric(write_key, id, chart_downloads_event, properties)


def send_pull_request_metrics(write_key, g):
    chart_submissions = 0
    partners = []
    partner_charts = []
    charts_merged = 0
    charts_abandoned = 0
    charts_in_progress = 0
    abandoned = []
    repo = g.get_repo("openshift-helm-charts/charts")
    pull_requests = repo.get_pulls(state="all")
    for pr in pull_requests:
        pr_content, type, provider, chart, version = check_and_get_pr_content(pr, repo)
        if pr_content != "not-chart":
            chart_submissions += 1
            if pr.closed_at and not pr.merged_at:
                charts_abandoned += 1
                print(f"[INFO] Abandoned PR: {pr.number} ")
                abandoned.append(pr.number)
            elif pr.merged_at:
                charts_merged += 1
                if type == "partner":
                    if provider not in partners:
                        partners.append(provider)
                    if chart not in partner_charts:
                        partner_charts.append(chart)
            else:
                charts_in_progress += 1

        check_rate_limit(g, False)

    print(f"[INFO] abandoned PRS: {abandoned}")
    send_summary_metric(
        write_key,
        chart_submissions,
        charts_merged,
        charts_abandoned,
        charts_in_progress,
        len(partners),
        len(partner_charts),
    )


def get_pr_files(pr):
    files = pr.get_files()
    pr_chart_submission_files = []
    for file in files:
        pr_chart_submission_files.append(file.filename)
    return pr_chart_submission_files


def process_report_fails(message_file):
    fails = "0"
    num_error_messages = 0
    error_messages = []
    checks_failed = []

    fails_started = False
    check_failures = False
    non_check_failures = False

    with open(message_file) as file:
        message_lines = [line.rstrip() for line in file]
        for message_line in message_lines:
            if not fails_started:
                fails_started = pr_comment.get_verifier_errors_comment() in message_line
            else:
                if "[ERROR] Chart verifier report includes failures:" in message_line:
                    check_failures = True
                if pr_comment.get_verifier_errors_trailer() in message_line:
                    break
                elif "Number of checks failed" in message_line:
                    body_line_parts = message_line.split(":")
                    fails = body_line_parts[1].strip()
                    print(f"[INFO] Number of failures in report: {fails}")
                elif fails != "0":
                    if "Error message(s)" in message_line:
                        num_error_messages = 1
                    elif num_error_messages <= int(fails):
                        print(f"[INFO] add error message: {message_line.strip()}")
                        error_messages.append(message_line.strip())
                        num_error_messages += 1
                elif not check_failures and len(message_line) > 0:
                    non_check_failures = True
                    print(f"[INFO] non-check message: {message_line.strip()}")
                    error_messages.append(message_line.strip())

    if check_failures:
        for error_message in error_messages:
            if (
                "Missing required annotations" in error_message
                or "Empty metadata in chart" in error_messages
            ):
                checks_failed.append("required-annotations-present")
            elif "Chart test files do not exist" in error_message:
                checks_failed.append("contains-test")
            elif "API version is not V2, used in Helm 3" in error_message:
                checks_failed.append("is-helm-v3")
            elif "Values file does not exist" in error_message:
                checks_failed.append("contains-values")
            elif "Values schema file does not exist" in error_message:
                checks_failed.append("contains-values-schema")
            elif (
                "Kubernetes version is not specified" in error_message
                or "Error converting kubeVersion to an OCP range" in error_message
            ):
                checks_failed.append("has-kubeversion")
            elif "Helm lint has failed" in error_message:
                checks_failed.append("helm_lint")
            elif (
                "Failed to certify images" in error_message
                or "Image is not Red Hat certified" in error_message
            ):
                if "images-are-certified" not in checks_failed:
                    checks_failed.append("images-are-certified")
            elif "Chart does not have a README" in error_message:
                checks_failed.append("has-readme")
            elif "Missing mandatory check" in error_messages:
                checks_failed.append("missing-mandatory-check")
            elif "Chart contains CRDs" in error_messages:
                checks_failed.append("not-contains-crds")
            elif "CSI objects exist" in error_message:
                checks_failed.append("not-contain-csi-objects")
            else:
                checks_failed.append("chart-testing")
    elif non_check_failures:
        fails = "1"
        checks_failed.append("other-non-check-failure")

    return int(fails), checks_failed


def process_comments(repo, pr):
    issue = repo.get_issue(number=pr.number)
    comments = issue.get_comments()
    num_builds = 0
    for comment in comments:
        report_result = parse_message(comment.body, pr.number)
        if report_result != "not-found":
            num_builds += 1

    return num_builds


def process_comment_file(message_file, pr_number):
    with open(message_file, "r") as file:
        message = file.read()

    return parse_message(message, pr_number)


def parse_message(message, pr_number):
    report_result = "not-found"
    if pr_comment.get_comment_header(pr_number) in message:
        if pr_comment.get_verifier_errors_comment() in message:
            report_result = "report-failure"
        elif pr_comment.get_content_failure_message() in message:
            report_result = "content-failure"
        elif pr_comment.get_success_coment() in message:
            report_result = "report-pass"
        elif pr_comment.get_community_review_message() in message:
            report_result = "community_review"

    print(f"[INFO] report_result : {report_result}")
    return report_result


def get_pr_content(pr):
    pr_content = "not-chart"
    pr_chart_submission_files = get_pr_files(pr)
    if len(pr_chart_submission_files) > 0:
        match = file_pattern.match(pr_chart_submission_files[0])
        if match:
            type, org, chart, version = match.groups()
            if type == "partners":
                type = "partner"
            print(
                f"[INFO] Found PR {pr.number}:{pr.user.login}: type: {type},org: {org},chart: {chart},version: {version}, #files: {len(pr_chart_submission_files)}, file match: {pr_chart_submission_files[0]}"
            )
            tgz_found = False
            report_found = False
            src_found = False
            for file in pr_chart_submission_files:
                filename = os.path.basename(file)
                if filename == "report.yaml":
                    report_found = True
                elif filename.endswith(".tgz"):
                    tgz_found = True
                elif filename == "Chart.yaml" and len(pr_chart_submission_files) > 2:
                    src_found = True

            if report_found:
                if tgz_found:
                    pr_content = "report and tgz"
                elif src_found:
                    pr_content = "src and report"
                else:
                    pr_content = "report only"
            elif tgz_found:
                pr_content = "tgz only"
            elif src_found:
                pr_content = "src only"

            return pr_content, type, org, chart, version

    return pr_content, "", "", "", ""


def check_and_get_pr_content(pr, repo):
    repo_name = repo.full_name
    if (
        (pr.user.login in ignore_users and pr.user.login not in repo_name)
        or pr.draft
        or pr.base.ref != "main"
    ):
        print(
            f"[INFO] Ignore pr, user: {pr.user.login}, draft: {pr.draft}, target_branch: {pr.base.ref}"
        )
        return "not-chart", "", "", "", ""

    return get_pr_content(pr)


def process_pr(write_key, repo, message_file, pr_number, action, prefix, pr_directory):
    pr = repo.get_pull(int(pr_number))
    pr_content, type, provider, chart, version = check_and_get_pr_content(pr, repo)
    if pr_content != "not-chart":
        if action == "opened":
            send_submission_metric(
                write_key,
                type,
                provider,
                chart,
                pr_number,
                pr_content,
                prefix,
                pr_directory,
            )

        pr_result = process_comment_file(message_file, pr_number)
        num_fails = 0
        if pr_result == "report-failure":
            num_fails, checks_failed = process_report_fails(message_file)
            for check in checks_failed:
                send_check_metric(write_key, type, provider, chart, pr_number, check)
        elif pr_result == "content-failure":
            num_fails = 1

        send_outcome_metric(
            write_key, type, provider, chart, pr_number, pr_result, num_fails, prefix
        )

        # if pr is merged we can collect summary stats
        if pr.merged_at:
            builds = process_comments(repo, pr)
            print(f"[INFO]    PR  build cycles : {builds}")
            builds_out = str(builds)
            if builds > 5:
                builds_out = "> 5"

            elapsed_time = pr.merged_at - pr.created_at
            # round up to an hour to avoid 0 time
            elapsed_hours = elapsed_time.total_seconds() // 3600
            duration = "0-1 hours"
            if 24 > elapsed_hours > 1:
                duration = "1-24 hours"
            elif 168 > elapsed_hours > 24:
                duration = "1-7 days"
            elif elapsed_hours > 168:
                duration = "> 7 days"

            send_merge_metric(
                write_key,
                type,
                provider,
                chart,
                duration,
                pr_number,
                builds_out,
                pr_content,
                prefix,
                pr_directory,
            )


def send_summary_metric(
    write_key,
    num_submissions,
    num_merged,
    num_abandoned,
    num_in_progress,
    num_partners,
    num_charts,
):
    properties = {
        "submissions": num_submissions,
        "merged": num_merged,
        "abandoned": num_abandoned,
        "in_progress": num_in_progress,
        "partners": num_partners,
        "partner_charts": num_charts,
    }
    id = "helm-metric-summary"

    send_metric(write_key, id, "PR Summary", properties)


def send_outcome_metric(
    write_key, type, provider, chart, pr_number, outcome, num_fails, prefix
):
    properties = {
        "type": type,
        "provider": provider,
        "chart": chart,
        "pr": pr_number,
        "outcome": outcome,
        "failures": num_fails,
    }
    id = f"{prefix}-{type}-{provider}"

    send_metric(write_key, id, pr_outcome, properties)


def send_check_metric(write_key, type, partner, chart, pr_number, check):
    properties = {
        "type": type,
        "provider": partner,
        "chart": chart,
        "pr": pr_number,
        "check": check,
    }
    id = f"helm-metric-{partner}"

    send_metric(write_key, id, "PR Report Fails", properties)


def send_merge_metric(
    write_key,
    type,
    partner,
    chart,
    duration,
    pr_number,
    num_builds,
    pr_content,
    prefix,
    pr_directory,
):
    update = getChartUpdate(type, partner, chart, pr_directory)
    id = f"{prefix}-{type}-{partner}"
    properties = {
        "type": type,
        "provider": partner,
        "chart": chart,
        "pr": pr_number,
        "builds": num_builds,
        "duration": duration,
        "content": pr_content,
        "update": update,
    }

    send_metric(write_key, id, pr_merged, properties)


def send_submission_metric(
    write_key, type, partner, chart, pr_number, pr_content, prefix, pr_directory
):
    update = getChartUpdate(type, partner, chart, pr_directory)
    id = f"{prefix}-{type}-{partner}"
    properties = {
        "type": type,
        "provider": partner,
        "chart": chart,
        "pr": pr_number,
        "pr content": pr_content,
        "update": update,
    }

    send_metric(write_key, id, pr_submission, properties)


def on_error(error, items):
    print("An error occurred creating metrics:", error)
    print("error with items:", items)
    sys.exit(1)


def send_metric(write_key, id, event, properties):
    analytics.write_key = write_key
    analytics.on_error = on_error

    print(f"[INFO] Add track:  id: {id},  event:{event},  properties:{properties}")

    analytics.track(id, event, properties)


def check_rate_limit(g, force):
    rate_limit = g.get_rate_limit()
    if force or rate_limit.core.remaining < 10:
        print(f"[INFO] rate limit info: {rate_limit.core}")


def getChartUpdate(type, partner, chart, cwd):
    if type == "partner":
        directory_type = "partners"
    else:
        directory_type = type
    directoryPath = os.path.join(cwd, charts, directory_type, partner, chart)
    # Checking if the directory contains only the OWNERS file
    print(os.listdir(directoryPath))
    if len(os.listdir(directoryPath)) == 1:
        return "new chart"
    else:
        return "new version"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k",
        "--write-key",
        dest="write_key",
        type=str,
        required=True,
        help="segment write key",
    )
    parser.add_argument(
        "-t",
        "--metric-type",
        dest="type",
        type=str,
        required=True,
        help="metric type, releases or pull_request",
    )
    parser.add_argument(
        "-m",
        "--message-file",
        dest="message_file",
        type=str,
        required=False,
        help="message for metric",
    )
    parser.add_argument(
        "-n",
        "--pr-number",
        dest="pr_number",
        type=str,
        required=False,
        help="number of teh pr",
    )
    parser.add_argument(
        "-a",
        "--pr-action",
        dest="pr_action",
        type=str,
        required=False,
        help="The event action of the pr",
    )
    parser.add_argument(
        "-r",
        "--repository",
        dest="repository",
        type=str,
        required=False,
        help="The repository of the pr",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        dest="prefix",
        type=str,
        required=False,
        help="The prefix of the id in segment",
    )
    parser.add_argument(
        "-d",
        "--pr_dir",
        dest="pr_dir",
        type=str,
        required=False,
        help="Directory of pull request code.",
    )

    args = parser.parse_args()
    print("Input arguments:")
    print(f"   --write-key length : {len(args.write_key)}")
    print(f"   --metric-type : {args.type}")
    print(f"   --messsage-file : {args.message_file}")
    print(f"   --pr-number : {args.pr_number}")
    print(f"   --pr-action : {args.pr_action}")
    print(f"   --repository : {args.repository}")
    print(f"   --prefix : {args.prefix}")
    print(f"   --pr_dir : {args.pr_dir}")

    if not args.write_key:
        print("Error: Segment write key not set")
        sys.exit(1)

    g = Github(os.environ.get("BOT_TOKEN"))

    if args.type == "pull_request":
        repo_current = g.get_repo(args.repository)
        process_pr(
            args.write_key,
            repo_current,
            args.message_file,
            args.pr_number,
            args.pr_action,
            args.prefix,
            args.pr_dir,
        )
    else:
        check_rate_limit(g, True)
        send_release_metrics(args.write_key, get_release_metrics(), args.prefix)
        check_rate_limit(g, True)
        send_pull_request_metrics(args.write_key, g)
        check_rate_limit(g, True)


if __name__ == "__main__":
    main()
