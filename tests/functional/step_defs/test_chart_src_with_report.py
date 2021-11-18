# -*- coding: utf-8 -*-
"""Chart source submission with report

Partners, redhat and community users can publish their chart by submitting
error-free chart in source format with a report.
"""
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
    test_name = 'Test Chart Source With Report'
    test_chart = 'tests/data/vault-0.13.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/report_and_chart_src.feature', "A partner or redhat associate submits an error-free chart source with report")
def test_partner_or_redhat_user_submits_chart_src_with_report():
    """A partner or redhat associate submits an error-free chart source with report."""

@scenario('../features/report_and_chart_src.feature', "A community user submits an error-free chart source with report")
def test_community_user_submits_chart_src_with_report():
    """A community user submits an error-free chart source with report"""

@given(parsers.parse("the vendor <vendor> has a valid identity as <vendor_type>"))
def user_has_valid_identity(workflow_test, vendor, vendor_type):
    """the vendor <vendor> has a valid identity as <vendor_type>."""
    workflow_test.set_vendor(vendor, vendor_type)


@given(parsers.parse("an error-free chart source is used in <chart_path> and report in <report_path>"))
def user_has_created_error_free_chart_src_and_report(workflow_test, chart_path, report_path):
    """an error-free chart source is used in <chart_path> and report in <report_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.update_test_report(report_path)

    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)
    workflow_test.process_report()
    workflow_test.push_chart(is_tarball=False)


@when("the user sends a pull request with the chart and report")
def user_sends_pull_request_with_chart_src_and_report(workflow_test):
    """the user sends a pull request with the chart and report."""
    workflow_test.send_pull_request()

@then("the user sees the pull request is merged")
def user_should_see_pull_request_getting_merged(workflow_test):
    """the user sees the pull request is merged."""
    workflow_test.check_workflow_conclusion(expect_result='success')
    workflow_test.check_pull_request_result(expect_merged=True)


@then("the index.yaml file is updated with an entry for the submitted chart")
def index_yaml_is_updated_with_new_entry(workflow_test):
    """the index.yaml file is updated with an entry for the submitted chart."""
    workflow_test.check_index_yaml()


@then("a release is published with corresponding report and chart tarball")
def release_is_published(workflow_test):
    """a release is published with corresponding report and chart tarball."""
    workflow_test.check_release_result()

@then("the pull request is not merged")
def the_pull_request_is_not_getting_merged(workflow_test):
    """the pull request is not merged"""
    workflow_test.check_workflow_conclusion(expect_result='failure')
    workflow_test.check_pull_request_result(expect_merged=False)

@then(parsers.parse("user gets the <message> in the pull request comment"))
def user_gets_the_message_in_the_pull_request_comment(workflow_test, message):
    """user gets the message in the pull request comment"""
    workflow_test.check_pull_request_comments(expect_message=message)
