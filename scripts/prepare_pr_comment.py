import os
import sys

def prepare_failure_comment(repository, issue_number, vendor_label, chart_name):
    msg = f"""\
Thank you for submitting pull request #{issue_number} for Helm Chart Certification!

There were one or more errors while building and verifying your pull request.
To see the console output with the error messages, click the "Details"
link next to "CI / Chart Certification" job status towards the end of this page.
"""
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg += f"""
[ERROR] The submitted chart has failed certification. Reason(s):

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
    msg = f"Thank you for submitting PR #{issue_number} for Helm Chart Certification!\n\n"
    msg += f"Congratulations! Your chart has been certified and will be published shortly.\n\n"
    msg += f'/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}\n\n'
    return msg

def prepare_sanity_failure_comment(issue_number, vendor_label, chart_name):
    msg = f"Thank you for submitting PR #{issue_number} for Helm Chart Certification!\n\n"
    msg += f"An error was found with the Pull Request: \n"
    msg += f"- Please ensure that only chart related files are included in the PullRequest.\n\n"
    msg += f'/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}\n\n'
    return msg

def main():
    sanity_result = sys.argv[1]
    verify_result = sys.argv[2]
    repository = sys.argv[3]
    issue_number = open("./pr/NR").read().strip()
    vendor_label = open("./pr/vendor").read().strip()
    chart_name = open("./pr/chart").read().strip()
    if sanity_result == "failure":
        msg = prepare_sanity_failure_comment(issue_number, vendor_label, chart_name)
    elif verify_result == "failure":
        msg = prepare_failure_comment(repository, issue_number, vendor_label, chart_name)
    else:
        msg = prepare_success_comment(issue_number, vendor_label, chart_name)

    with open("./pr/comment", "w") as fd:
        fd.write(msg)

if __name__ == "__main__":
    main()
