import os
import sys

def prepare_failure_comment(repository, issue_number, vendor_label, chart_name):
    runid = open("./pr/build-verify-check-run-id").read()
    run_url = f"https://github.com/{repository}/pull/{issue_number}/checks?check_run_id={runid}".strip()
    msg = f"""\
Thank you for the pull request #{issue_number}!

There are few errors while building and verifying your pull request.
Please check the error log for more details:
{run_url}
(open this link in a new tab/window)
"""
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg += f"""
The following issues require changes in the pull request:

{errors}
"""

    msg += f"""
---
/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}

Partner Support: http://bit.ly/technology-partner-success-desk
"""
    return msg

def prepare_success_comment(issue_number, vendor_label, chart_name):
    msg = f"Thank you for the PR #{issue_number}!\n\n"
    msg += f'/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}\n\n'
    return msg

def main():
    result = sys.argv[1]
    repository = sys.argv[2]
    issue_number = open("./pr/NR").read().strip()
    vendor_label = open("./pr/vendor").read().strip()
    chart_name = open("./pr/chart").read().strip()
    if result == "failure":
        msg = prepare_failure_comment(repository, issue_number, vendor_label, chart_name)
    else:
        msg = prepare_success_comment(issue_number, vendor_label, chart_name)

    with open("./pr/comment", "w") as fd:
        fd.write(msg)

if __name__ == "__main__":
    main()
