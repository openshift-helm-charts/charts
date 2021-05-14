import os
import sys

def prepare_failure_comment(repository, issue_number, vendor_label, chart_name):
    msg = f"""\
Thank you for the pull request #{issue_number}!

There are few errors while building and verifying your pull request.
To see the console output with the error messages, click the "Details"
link next to "Build and Verify" job status towards the end of this page.
"""
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg += f"""
[ERROR] The submitted chart has failed verification. Reason(s):

{errors}

Please run the [chart-verifier](https://github.com/redhat-certification/chart-verifier) \
and ensure all mandatory checks pass.
"""

    msg += f"""
---
/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}

For support, connect with our [Technology Partner Success Desk](https://redhat-connect.gitbook.io/red-hat-partner-connect-general-guide/managing-your-account/getting-help/technology-partner-success-desk).
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
