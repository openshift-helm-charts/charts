from behave import given, when, then
from common.utils.chart import Chart, Chart_Type, Release_Type

############### Common step definitions ###############
@given(u'the vendor "{vendor}" has a valid identity as "{vendor_type}"')
def vendor_has_valid_identity(context, vendor, vendor_type):
    context.workflow_test.set_vendor(vendor, vendor_type)

@given(u'an error-free chart source is used in "{chart_path}"')
def chart_source_is_used(context, chart_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC, chart_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.push_charts()

@given(u'chart source is used in "{chart_path}"')
def user_has_used_chart_src(context, chart_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC, chart_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()

@given(u'an error-free chart tarball is used in "{chart_path}"')
def user_has_created_error_free_chart_tarball(context, chart_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR, chart_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.push_charts()

@given(u'a signed chart tarball is used in "{chart_path}" and public key in "{public_key_file}"')
def user_has_created_signed_chart_tarball(context, chart_path, public_key_file):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR, chart_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file(public_key_file=public_key_file)
    context.workflow_test.process_charts(include_prov_file=True)
    context.workflow_test.push_charts()

@given(u'signed chart tar used in "{chart_path}"')
def user_has_created_signed_chart_tarball(context, chart_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR, chart_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts(include_prov_file=True)
    context.workflow_test.push_charts()

@given(u'an error-free chart tarball used in "{chart_path}" and report in "{report_path}"')
def user_has_created_error_free_chart_tarball_and_report(context, chart_path, report_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR_AND_REPORT, chart_path, report_path)])

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.process_report()
    context.workflow_test.push_charts()

@given(u'a signed chart tar is used in "{chart_path}", report in "{report_path}" and public key in "{public_key_file}"')
def user_has_created_error_free_chart_tarball_and_report(context, chart_path, report_path, public_key_file):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR_AND_REPORT, chart_path, report_path)])

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file(public_key_file=public_key_file)
    context.workflow_test.process_charts(include_prov_file=True)
    context.workflow_test.process_report()
    context.workflow_test.push_charts()

@given(u'unsigned chart tarball is used in "{chart_path}" and public key used "{public_key_file}" in owners')
def user_has_created_error_free_chart_tarball(context, chart_path, public_key_file):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR, chart_path)])

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file(public_key_file=public_key_file)
    context.workflow_test.process_charts()
    context.workflow_test.push_charts()

@given(u'a chart tarball is used in "{chart_path}" and report in "{report_path}"')
def user_has_created_a_chart_tarball_and_report(context, chart_path, report_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR_AND_REPORT, chart_path, report_path)])

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()

@given(u'an error-free chart source used in "{chart_path}" and report in "{report_path}"')
def user_has_created_error_free_chart_src_and_report(context, chart_path, report_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC_AND_REPORT, chart_path, report_path)])

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.process_report()
    context.workflow_test.push_charts()

@given(u'report is used in "{report_path}"')
@given(u'an error-free report is used in "{report_path}"')
def user_has_created_error_free_report(context, report_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.REPORT, report_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_report()

@given(u'signed chart report used in "{report_path}" and public key in "{public_key_file}"')
def user_has_created_error_free_report(context, report_path, public_key_file):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.REPORT, report_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file(public_key_file=public_key_file)
    context.workflow_test.process_report()

@given(u'user wants to send two reports as in "{report_path_1}" and "{report_path_2}"')
def user_has_created_error_free_report(context, report_path_1, report_path_2):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.REPORT, report_path_1), (Chart_Type.REPORT, report_path_2)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_report()

@given(u'user wants to send two chart sources as in "{chart_path_1}" and "{chart_path_2}"')
def user_wants_to_send_two_chart_sources(context, chart_path_1, chart_path_2):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC, chart_path_1), (Chart_Type.SRC, chart_path_2)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.push_charts()

@given(u'user wants to send two chart tars as in "{chart_path_1}" and "{chart_path_2}"')
def user_wants_to_send_two_chart_tars(context, chart_path_1, chart_path_2):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR, chart_path_1), (Chart_Type.TAR, chart_path_2)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.push_charts()

@given(u'user wants to send two charts one with source "{chart_path}" and other with report "{report_path}"')
def user_wants_to_send_multiple_chart_one_with_src_and_other_with_report(context, chart_path, report_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC, chart_path), (Chart_Type.REPORT, report_path)])

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.process_report()
    context.workflow_test.push_charts()

@given(u'user wants to send two charts one with tar "{chart_path}" and other with report "{report_path}"')
def user_wants_to_send_multiple_chart_one_with_tar_and_other_with_report(context, chart_path, report_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.TAR, chart_path), (Chart_Type.REPORT, report_path)])

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    context.workflow_test.process_report()
    context.workflow_test.push_charts()

@given(u'a "{report_path}" is provided')
def user_generated_a_report(context, report_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.REPORT, report_path)])
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()

@when(u'the user sends a pull request with the report')
@when(u'the user sends a pull request with the chart')
@when(u'the user sends a pull request with the chart and report')
def user_sends_a_pull_request(context):
    context.workflow_test.send_pull_request()

@when(u'the user pushed the chart and created pull request')
def user_pushed_the_chart_and_created_pull_request(context):
    context.workflow_test.push_charts()
    context.workflow_test.send_pull_request()

@then(u'the user sees the pull request is merged')
def pull_request_is_merged(context):
    context.workflow_test.check_workflow_conclusion(expect_result='success')
    context.workflow_test.check_pull_request_result(expect_merged=True)
    context.workflow_test.check_pull_request_labels()

@then(u'the index.yaml file is updated with an entry for the submitted chart')
def index_yaml_updated_with_submitted_chart(context):
    context.workflow_test.check_index_yaml()

@then(u'a release is published with report only')
def release_is_published(context):
    context.workflow_test.check_release_result(release_type=Release_Type.REPORT_ONLY)

@then(u'a release is published with corresponding report and chart tarball')
def release_is_published(context):
    context.workflow_test.check_release_result(release_type=Release_Type.CHART_AND_REPORT)

@then(u'a release is published with corresponding report, tarball, prov and key')
def release_is_published_for_signed_chart(context):
    context.workflow_test.check_release_result(release_type=Release_Type.CHART_REPORT_PROV_AND_KEY)

@then(u'a release is published with corresponding report and key')
def release_is_published_for_signed_chart(context):
    context.workflow_test.check_release_result(release_type=Release_Type.REPORT_AND_KEY)

@then(u'a release is published with corresponding report, chart tar and prov file')
def release_is_published_for_signed_chart_and_report(context):
    context.workflow_test.check_release_result(release_type=Release_Type.CHART_PROV_AND_REPORT)

@then(u'the pull request is not merged')
def pull_request_is_not_merged(context):
    context.workflow_test.check_workflow_conclusion(expect_result='failure')
    context.workflow_test.check_pull_request_result(expect_merged=False)

@then(u'user gets the "{message}" in the pull request comment')
def user_gets_a_message(context, message):
    context.workflow_test.check_pull_request_comments(expect_message=message)

########## Unique step definitions #################

@given(u'README file is missing in the chart')
def readme_file_is_missing(context):
    context.workflow_test.remove_readme_file()

@then(u'the index.yaml file is updated with an entry for the submitted chart with correct providerType')
def index_yaml_is_updated_with_new_entry_with_correct_provider_type(context):
    context.workflow_test.check_index_yaml(check_provider_type=True)

@given(u'the report contains an "{invalid_url}"')
def invalid_url_in_the_report(context, invalid_url):
    context.workflow_test.process_report(update_url=True, url=invalid_url)

@given(u'user adds a non chart related file')
def user_adds_a_non_chart_related_file(context):
    context.workflow_test.add_non_chart_related_file()

@when(u'the user sends a pull request with both chart and non related file')
def user_sends_pull_request_with_chart_and_non_related_file(context):
    context.workflow_test.push_charts(add_non_chart_file=True)
    context.workflow_test.send_pull_request()

@given(u'provider delivery control is set to "{provider_control_owners}" in the OWNERS file')
def provider_delivery_control_set_in_owners(context, provider_control_owners):
    context.workflow_test.update_provided_delivery(provider_control_owners)

@given(u'provider delivery control is set to "{provider_control_report}" in the report')
def provider_delivery_control_set_in_report(context, provider_control_report):
    if provider_control_report == "true":
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=True)
    else:
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=False)

@given(u'provider delivery controls is set to "{provider_control_report}" and a package digest is "{package_digest_set}" in the report')
def provider_delivery_control_and_package_digest_set_in_report(context, provider_control_report, package_digest_set=True):
    if package_digest_set == "true":
        no_package_digest = False
    else:
        no_package_digest = True

    if provider_control_report == "true":
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=True, unset_package_digest=no_package_digest)
    else:
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=False, unset_package_digest=no_package_digest)

@then(u'the "{index_file}" is updated with an entry for the submitted chart')
def index_file_is_updated(context, index_file):
    context.workflow_test.secrets.index_file = index_file
    context.workflow_test.check_index_yaml(True)

@given(u'the report includes "{tested}" and "{supported}" OpenshiftVersion values and chart "{kubeversion}" value')
def report_includes_specified_versions(context, tested, supported, kubeversion):
    context.workflow_test.process_report(update_versions=True, supported_versions=supported, tested_version=tested, kube_version=kubeversion)

@given(u'the report has a "{check}" missing')
def report_has_a_check_missing(context, check):
    context.workflow_test.process_report(missing_check=check)

@given(u'A "{user}" wants to submit a chart in "{chart_path}"')
def user_wants_to_submit_a_chart(context, user, chart_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC, chart_path)])
    context.workflow_test.update_bot_name(user)

@given(u'An authorized user wants to submit a chart in "{chart_path}"')
def authorized_user_wants_to_submit_a_chart(context, chart_path):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC, chart_path)])

@given(u'a chart source used in "{chart_path}" and directory structure contains "{bad_version}"')
def a_user_wants_to_submit_a_chart_with_bad_semver(context, chart_path, bad_version):
    context.workflow_test.update_test_charts(test_charts=[(Chart_Type.SRC, chart_path)], new_chart_version=bad_version)

@given(u'the user creates a branch to add a new chart version')
def the_user_creates_a_branch_to_add_a_new_chart_version(context):
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_charts()
    if context.workflow_test.secrets.bad_version:
        context.workflow_test.update_chart_version_in_chart_yaml(context.workflow_test.secrets.bad_version)
    context.workflow_test.push_charts()

@given(u'Chart.yaml specifies a "{bad_version}"')
def chart_yaml_specifies_bad_version(context, bad_version):
    if bad_version != '':
        context.workflow_test.update_bad_version(bad_version)

@given(u'the report contains "{error}"')
def sha_value_does_not_match(context, error):
    if error == 'sha_mismatch':
        context.workflow_test.process_report(update_chart_sha=True)
    else:
        raise AssertionError(f"This {error} handling is not implemented yet")

@when(u'the user sends a pull request with the chart tar and report')
def user_sends_pull_request_with_chart_tarball_and_report(context):
    context.workflow_test.push_charts()
    context.workflow_test.send_pull_request()

######## Test Submitted Charts Step definitions ##########
@given(u'there is a github workflow for testing existing charts')
def theres_github_workflow_for_testing_charts(context):
    print("[INFO] Running step: there is a github workflow for testing existing charts")

@when(u'a new Openshift or chart-verifier version is specified')
def new_openshift_or_verifier_version_is_specified(context):
    print("[INFO] Running step: a new Openshift or chart-verifier version is specified")

@when(u'the vendor type is specified, e.g. partner, and/or redhat')
def vendor_type_is_specified(context):
    print("[INFO] Running step: the vendor type is specified, e.g. partner, and/or redhat")

@when(u'workflow for testing existing charts is triggered')
def workflow_is_triggered(context):
    print("[INFO] Running step: workflow for testing existing charts is triggered")

@then(u'submission tests are run for existing charts')
def submission_tests_run_for_submitted_charts(context):
    print("[INFO] Running step: submission tests are run for existing charts")
    context.chart_test.process_all_charts()

@then(u'all results are reported back to the caller')
def all_results_report_back_to_caller(context):
    print("[INFO] Running step: all results are reported back to the caller")