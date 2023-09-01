import pytest
from pytest_bdd import (
    given,
    then,
    when,
    parsers
)

########### GIVEN ####################
@given(parsers.parse("A <user> wants to submit a chart in <chart_path>"))
def user_wants_to_submit_a_chart(workflow_test, user, chart_path):
    """A <user> wants to submit a chart in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.secrets.bot_name = user

@given(parsers.parse("An authorized user wants to submit a chart in <chart_path>"))
def authorized_user_wants_to_submit_a_chart(workflow_test, chart_path):
    """A <user> wants to submit a chart in <chart_path>."""
    workflow_test.update_test_chart(chart_path)

@given(parsers.parse("<vendor> of <vendor_type> wants to submit <chart> of <version>"))
def vendor_of_vendor_type_wants_to_submit_chart_of_version(workflow_test, vendor, vendor_type, chart, version):
    """<vendor> of <vendor_type> wants to submit <chart> of <version>"""
    workflow_test.set_vendor(vendor, vendor_type)
    workflow_test.chart_name, workflow_test.chart_version = chart, version

@given(parsers.parse("Chart.yaml specifies a <bad_version>"))
def chart_yaml_specifies_bad_version(workflow_test, bad_version):
    """ Chart.yaml specifies a <bad_version> """
    if bad_version != '':
        workflow_test.secrets.bad_version = bad_version

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

@given(parsers.parse("an error-free chart source is used in <chart_path>"))
def user_has_created_error_free_chart_src(workflow_test, chart_path):
    """an error-free chart source is used in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)
    workflow_test.push_chart(is_tarball=False)

@given(parsers.parse("an error-free chart tarball is used in <chart_path> and report in <report_path>"))
def user_has_created_error_free_chart_tarball_and_report(workflow_test, chart_path, report_path):
    """an error-free chart tarball is used in <chart_path> and report in <report_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.update_test_report(report_path)

    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=True)
    workflow_test.process_report()
    workflow_test.push_chart(is_tarball=True)

@given(parsers.parse("an error-free chart tarball is used in <chart_path>"))
def user_has_created_error_free_chart_tarball(workflow_test, chart_path):
    """an error-free chart tarball is used in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=True)
    workflow_test.push_chart(is_tarball=True)

@given(parsers.parse("report is used in <report_path>"))
@given(parsers.parse("an error-free report is used in <report_path>"))
def user_has_created_error_free_report(workflow_test, report_path):
    """an error-free report is used in <report_path>."""
    workflow_test.update_test_report(report_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_report()

@given(parsers.parse("a <report_path> is provided"))
def user_generated_a_report(workflow_test, report_path):
    """report used in <report_path>"""
    workflow_test.update_test_report(report_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()


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

@given(parsers.parse("chart source is used in <chart_path>"))
def user_has_used_chart_src(workflow_test, chart_path):
    """chart source is used in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)

@given(parsers.parse("a chart tarball is used in <chart_path> and report in <report_path>"))
def user_has_created_a_chart_tarball_and_report(workflow_test, chart_path, report_path):
    """an error-free chart tarball is used in <chart_path> and report in <report_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.update_test_report(report_path)

    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=True)

@given("README file is missing in the chart")
def readme_file_is_missing(workflow_test):
    """README file is missing in the chart"""
    workflow_test.remove_readme_file()

@given(parsers.parse("the report contains an <invalid_url>"))
def sha_value_does_not_match(workflow_test, invalid_url):
    workflow_test.process_report(update_url=True, url=invalid_url)

@given("user adds a non chart related file")
def user_adds_a_non_chart_related_file(workflow_test):
    """user adds a non chart related file"""
    workflow_test.add_non_chart_related_file()

@given(parsers.parse("the report contains an <error>"))
def sha_value_does_not_match(workflow_test, error):
    if error == 'sha_mismatch':
        workflow_test.process_report(update_chart_sha=True)
    else:
        pytest.fail(f"This {error} handling is not implemented yet")

############### WHEN ####################
@when("the user sends a pull request with the report")
@when("the user sends a pull request with the chart")
@when("the user sends a pull request with the chart and report")
def user_sends_pull_request_with_chart_src_and_report(workflow_test):
    """the user sends a pull request with the chart and report."""
    workflow_test.send_pull_request()


@when("the user pushed the chart and created pull request")
def user_pushed_the_chart_and_created_pull_request_with_chart_src(workflow_test):
    """the user pushed the chart and created pull request"""
    workflow_test.push_chart(is_tarball=False)
    workflow_test.send_pull_request()

@when("the user sends a pull request with both chart and non related file")
def user_sends_pull_request_with_chart_and_non_related_file(workflow_test):
    """the user sends a pull request with both chart and non related file"""
    workflow_test.push_chart(is_tarball=False, add_non_chart_file=True)
    workflow_test.send_pull_request()

@when("the user sends a pull request with the chart tar and report")
def user_sends_pull_request_with_chart_tarball_and_report(workflow_test):
    """the user sends a pull request with the chart and report."""
    workflow_test.push_chart(is_tarball=True)
    workflow_test.send_pull_request()

################ THEN ################
@then("the user sees the pull request is merged")
def user_should_see_pull_request_getting_merged(workflow_test):
    """the user sees the pull request is merged."""
    workflow_test.check_workflow_conclusion(expect_result='success')
    workflow_test.check_pull_request_result(expect_merged=True)
    workflow_test.check_pull_request_labels()

@then("the pull request is not merged")
def the_pull_request_is_not_getting_merged(workflow_test):
    """the pull request is not merged"""
    workflow_test.check_workflow_conclusion(expect_result='failure')
    workflow_test.check_pull_request_result(expect_merged=False)

@then("the index.yaml file is updated with an entry for the submitted chart")
def index_yaml_is_updated_with_new_entry(workflow_test):
    """the index.yaml file is updated with an entry for the submitted chart."""
    workflow_test.check_index_yaml()

@then("the index.yaml file is updated with an entry for the submitted chart with correct providerType")
def index_yaml_is_updated_with_new_entry_with_correct_provider_type(workflow_test):
    """the index.yaml file is updated with an entry for the submitted chart with correct providerType"""
    workflow_test.check_index_yaml(check_provider_type=True)

@then("a release is published with corresponding report and chart tarball")
def release_is_published(workflow_test):
    """a release is published with corresponding report and chart tarball."""
    workflow_test.check_release_result()

@then(parsers.parse("user gets the <message> in the pull request comment"))
def user_gets_the_message_in_the_pull_request_comment(workflow_test, message):
    """user gets the message in the pull request comment"""
    workflow_test.check_pull_request_comments(expect_message=message)
