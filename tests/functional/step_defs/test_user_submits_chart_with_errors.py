# -*- coding: utf-8 -*-
""" Chart submission with errors
    Partners, redhat or community user submit charts which result in errors
"""
import logging
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
    parsers
)

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Chart Submission with Errors'
    test_chart = 'tests/data/vault-0.13.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/user_submits_chart_with_errors.feature', "An unauthorized user submits a chart")
def test_chart_submission_by_unauthorized_user():
    """An unauthorized user submits a chart"""

@scenario('../features/user_submits_chart_with_errors.feature', "An authorized user submits a chart with incorrect version")
def test_chart_submission_with_incorrect_version():
    """ An authorized user submits a chart with incorrect version """

@given(parsers.parse("A <user> wants to submit a chart in <chart_path>"))
def user_wants_to_submit_a_chart(workflow_test, user, chart_path):
    """A <user> wants to submit a chart in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    logging.info(f"User: {user}")
    workflow_test.secrets.bot_name = user

@given(parsers.parse("<vendor> of <vendor_type> wants to submit <chart> of <version>"))
def vendor_of_vendor_type_wants_to_submit_chart_of_version(workflow_test, vendor, vendor_type, chart, version):
    """<vendor> of <vendor_type> wants to submit <chart> of <version>"""
    logging.info(f"Vendor: {vendor} Vendor Type: {vendor_type} Chart: {chart} Version: {version}")
    workflow_test.set_vendor(vendor, vendor_type)
    workflow_test.chart_name, workflow_test.chart_version = chart, version

@given(parsers.parse("Chart.yaml specifies a <bad_version>"))
def chart_yaml_specifies_bad_version(workflow_test, bad_version):
    """ Chart.yaml specifies a <bad_version> """
    logging.info(f"Bad Version: {bad_version}")
    if bad_version != '':
        workflow_test.secrets.bad_version = bad_version

@given("the user creates a branch to add a new chart version")
def the_user_creates_a_branch_to_add_a_new_chart_version(workflow_test):
    """the user creates a branch to add a new chart version."""
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)
    if workflow_test.secrets.bad_version:
        workflow_test.update_chart_version_in_chart_yaml(workflow_test.secrets.bad_version)
    workflow_test.push_chart(is_tarball=False)

@when("the user sends a pull request with chart")
def the_user_sends_a_pull_request_with_chart(workflow_test):
    """The user sends the pull request with the chart."""
    workflow_test.send_pull_request()

@then("the pull request is not merged")
def the_pull_request_is_not_getting_merged(workflow_test):
    """the pull request is not merged"""
    workflow_test.check_workflow_conclusion(expect_result='failure')
    workflow_test.check_pull_request_result(expect_merged=False)

@then(parsers.parse("user gets the <message> with steps to follow for resolving the issue in the pull request"))
def user_gets_the_message_with_steps_to_follow_for_resolving_the_issue_in_the_pull_request(workflow_test, message):
    """user gets the message with steps to follow for resolving the issue in the pull request"""
    workflow_test.check_pull_request_comments(expect_message=message)
