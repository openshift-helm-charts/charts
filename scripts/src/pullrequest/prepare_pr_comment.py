import os
import sys

from tools import gitutils


def get_success_coment():
    return (
        "Congratulations! Your chart has been certified and will be published shortly."
    )


def get_content_failure_message():
    return "One or more errors were found with the pull request:"


def get_community_review_message():
    return "Community charts require maintainer review and approval, a review will be conducted shortly."


def get_failure_comment():
    return (
        "There were one or more errors while building and verifying your pull request."
    )


def get_comment_header(pr_number):
    return f"Thank you for submitting PR #{pr_number} for Helm Chart Certification!"


def get_verifier_errors_comment():
    return "[ERROR] The submitted chart has failed certification. Reason(s):"


def get_verifier_errors_trailer():
    return " ".join(
        [
            "Please create a valid report with the",
            "[chart-verifier](https://github.com/redhat-certification/chart-verifier)",
            "and ensure all mandatory checks pass.",
        ]
    )


def get_look_at_job_output_comment():
    return """To see the console output with the error messages, click the "Details" \
link next to "CI / Chart Certification" job status towards the end of this page."""


def prepare_failure_comment():
    """assembles the comment for certification failures

    Will attempt to read a file with error messaging from the filesystem
    and includes that information in its content. (e.g. ./pr/errors)
    """
    msg = get_failure_comment()
    msg = append_to(msg, get_look_at_job_output_comment())
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg = append_to(msg, get_verifier_errors_comment())
        msg = append_to(msg, errors)
        msg = append_to(msg, get_verifier_errors_trailer())
        gitutils.add_output("error-message", errors)
    else:
        gitutils.add_output("error-message", get_failure_comment())
    return msg


def prepare_pr_content_failure_comment():
    """Generate a message for PR Content Check Failures

    This function reaches into the environment for known variables
    that contain error messages.

    Error messages are then passed into the GITHUB_OUTPUT.

    Returns a formatted string containing error message contents.
    """
    msg = f"{get_content_failure_message()}"
    pr_content_error_msg = os.environ.get("PR_CONTENT_ERROR_MESSAGE", "")
    owners_error_msg = os.environ.get("OWNERS_ERROR_MESSAGE", "")
    if pr_content_error_msg:
        gitutils.add_output("error-message", pr_content_error_msg)
        msg = append_to(msg, f"{pr_content_error_msg}")
    if owners_error_msg:
        gitutils.add_output("error-message", owners_error_msg)
        msg = append_to(msg, f"{owners_error_msg}")
    return msg


def prepare_run_verifier_failure_comment():
    verifier_error_msg = os.environ.get("VERIFIER_ERROR_MESSAGE", "")
    gitutils.add_output("error-message", verifier_error_msg)
    msg = verifier_error_msg
    msg = append_to(msg, get_look_at_job_output_comment())
    return msg


def prepare_community_comment():
    msg = f"{get_community_review_message()}"
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg = append_to(
            msg,
            "However, **please note** that one or more errors were found while building and verifying your pull request:",
        )
        msg = append_to(msg, f"{errors}")
    return msg


def prepare_generic_fail_comment():
    msg = ""
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg = append_to(
            msg,
            "One or more errors were found while building and verifying your pull request:",
        )
        msg = append_to(msg, f"{errors}")
    else:
        msg = append_to(
            msg,
            "An unspecified error has occured while building and verifying your pull request.",
        )
    return msg


def prepare_oc_install_fail_comment():
    return " ".join(
        [
            "Unfortunately the certification process failed to install OpenShift Clientand could not complete.",
            "This problem will be addressed by maintainers and no further action is required from the submitter at this time.",
        ]
    )


def append_to(msg, new_content, use_horizontal_divider=False):
    """Appends new_content to the msg.

    This utility function helps simplify the building of our PR comment
    template. msg and new_content are joined with either a newline separator, or
    a horizontal line (if the keyword argument is provided).

    It should be used in cases where the caller needs to join semi-related
    ideas. Callers should instead use the join string method in cases where the
    msg being constructed is a part of the same 'idea', or 'paragraph'.

    Args:
        msg: The original message to which we should append new_content.
        new_content: the new string to add.
        use_horizontal_divider: Whether to divide the content
          with a horizontal line (in markdown.) Horizontal lines are surrounded
          in newlines to ensure that it does not inadvertently cause preceding
          content to become a Header.

    Returns the msg containing the new content.
    """
    divider_string = ""
    if use_horizontal_divider:
        divider_string = "\n---\n"

    return f"""
{msg}
{divider_string}
{new_content}
""".strip()  # Remove surrounding whitespace, like that which is added by putting """ on a newline here.


def get_support_information():
    reqs_doc_link = "https://github.com/redhat-certification/chart-verifier/blob/main/docs/helm-chart-checks.md#types-of-helm-chart-checks"
    support_link = "https://access.redhat.com/articles/6463941"
    return "\n".join(
        [
            "For information on the certification process see:",
            f"- [Red Hat certification requirements and process for Kubernetes applications that are deployed using Helm charts.]({reqs_doc_link}).",
            f"- For support, connect with our [Partner Acceleration Desk]({support_link}).",
        ]
    )


def metadata_label(vendor_label, chart_name):
    """Returns the metadata context that must suffix PR comments."""
    return (
        f'/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}'
    )


def task_table(task_tuples):
    """returns a markdown table containing tasks and their outcome

    Args:
        task_tuples: a list of two-length tuples where index 0 is the task
          and index 1 is the outcome. These values should be short.
    """
    sorted(task_tuples)
    msg = "|task|outcome|" + "\n|---|---|"
    for task_tuple in task_tuples:
        msg += f"\n|{task_tuple[0]}|{task_tuple[1]}|"
    return msg


def overall_outcome(outcome):
    return append_to("### Outcome:", f"**{outcome}**")


def main():
    pr_content_result = sys.argv[1]
    run_verifier_result = sys.argv[2]
    verify_result = sys.argv[3]
    issue_number = open("./pr/NR").read().strip()
    vendor_label = open("./pr/vendor").read().strip()
    chart_name = open("./pr/chart").read().strip()

    community_manual_review = os.environ.get("COMMUNITY_MANUAL_REVIEW", False)
    oc_install_result = os.environ.get("OC_INSTALL_RESULT")

    msg = get_comment_header(issue_number)

    # Assemble the detail separately to control order in which it is added to
    # the overall output.
    detail_message = "### Detail"

    outcome = "Failed"

    # Handle success explicitly
    if (
        pr_content_result == "success"
        # run_verifier may not run if a report is not needed.
        and run_verifier_result in ["success", "skipped"]
        and verify_result == "success"
        # installation of oc may not run if a cluster is not needed.
        and oc_install_result in ["success", "skipped"]
    ):
        outcome = "Passed"
        detail_message = append_to(detail_message, get_success_coment())
        gitutils.add_output("pr_passed", "true")
    else:  # Handle various failure scenarios.
        if pr_content_result == "failure":
            detail_message = append_to(
                detail_message, prepare_pr_content_failure_comment()
            )
            gitutils.add_output("pr_passed", "false")
        elif run_verifier_result == "failure":
            detail_message = append_to(
                detail_message, prepare_run_verifier_failure_comment()
            )
            gitutils.add_output("pr_passed", "false")
        elif verify_result == "failure":
            if community_manual_review:
                outcome = "Pending Manual Review"
                detail_message = append_to(detail_message, prepare_community_comment())
                gitutils.add_output("pr_passed", "true")
            else:
                detail_message = append_to(detail_message, prepare_failure_comment())
                gitutils.add_output("pr_passed", "false")
        elif oc_install_result == "failure":
            detail_message = append_to(
                detail_message, prepare_oc_install_fail_comment()
            )
            gitutils.add_output("pr_passed", "false")
        else:
            detail_message = append_to(detail_message, prepare_generic_fail_comment())
            gitutils.add_output("pr_passed", "false")

    msg = append_to(msg, overall_outcome(outcome))
    msg = append_to(msg, detail_message)
    if outcome != "Passed":
        table = task_table(
            [
                ("PR Content Check", pr_content_result),
                ("Run Chart Verifier", run_verifier_result),
                ("Result Verification", verify_result),
                ("OpenShift Client Installation", oc_install_result),
            ]
        )
        msg = append_to(msg, "### Task Insights")
        msg = append_to(msg, "Here are the outcomes of tasks driving this result.")
        msg = append_to(msg, table)

    # All comments get helpful links and a metadata
    msg = append_to(msg, get_support_information(), use_horizontal_divider=True)
    msg = append_to(msg, metadata_label(vendor_label, chart_name))

    # Print to the console so it's easily visible from CI.
    print("*" * 30)
    print(msg)
    print("*" * 30)

    with open("./pr/comment", "w") as fd:
        fd.write(msg)
        gitutils.add_output("message-file", fd.name)


if __name__ == "__main__":
    main()
