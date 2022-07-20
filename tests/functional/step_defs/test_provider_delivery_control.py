# -*- coding: utf-8 -*-
"""Chart tarball submission with report

Partners, redhat and community users can publish their chart by submitting
error-free chart in tarball format with a report.
"""
import pytest
from pytest_bdd import (
    scenario,
    given,
    parsers,
    then
)
from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test Porvider Delivery Control'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/HC-06_provider_delivery_control.feature', "[HC-06-001] A partner associate submits an error-free report with provider controlled delivery")
def test_partners_submits_error_free_report_for_provider_controlled_delivery():
    """A partner submits an error-free report for provider controlled delivery."""

@scenario('../features/HC-06_provider_delivery_control.feature', "[HC-06-002] A partner associate submits an error-free report and chart with provider controlled delivery")
def test_partners_submits_error_free_report_and_chart_for_provider_controlled_delivery():
    """A partner submits an error-free report and chart for provider controlled delivery."""

@scenario('../features/HC-06_provider_delivery_control.feature', "[HC-06-003] A partner associate submits an error-free report with inconsistent provider controlled delivery setting")
def test_partners_submits_error_free_report_with_inconsistent_provider_controlled_delivery_settings():
    """A partner submits an error-free report with inconsistent settings for provider controlled delivery."""

@given(parsers.parse("provider delivery control is set to <provider_control_owners> in the OWNERS file"))
def provider_delivery_control_set_in_owners(workflow_test,provider_control_owners):
    if provider_control_owners == "true":
        print("[INFO] set provider delivery control_in owners file")
        workflow_test.secrets.provider_delivery=True
    else:
        print("[INFO] un-set provider delivery control_in owners file")
        workflow_test.secrets.provider_delivery=False

@given(parsers.parse("provider delivery control is set to <provider_control_report> in the report"))
def provider_delivery_control_set_in_report(workflow_test,provider_control_report):
    if provider_control_report == "true":
        print("[INFO] set provider delivery control_in report")
        workflow_test.process_report(update_provider_delivery=True,provider_delivery=True)
    else:
        print("[INFO] un-set provider delivery control_in report")
        workflow_test.process_report(update_provider_delivery=True,provider_delivery=False)

@given(parsers.parse("provider delivery control is set to <provider_control_report> and a package digest is <package_digest_set> in the report"))
def provider_delivery_control_and_package_digest_set_in_report(workflow_test,provider_control_report,package_digest_set=True):
    if package_digest_set == "true":
        no_package_digest = False
    else:
        no_package_digest = True

    if provider_control_report == "true":
        print("[INFO] set provider delivery control_in report")
        workflow_test.process_report(update_provider_delivery=True,provider_delivery=True,unset_package_digest=no_package_digest)
    else:
        print("[INFO] un-set provider delivery control_in report")
        workflow_test.process_report(update_provider_delivery=True,provider_delivery=False,unset_package_digest=no_package_digest)

@then(parsers.parse("the <index_file> is updated with an entry for the submitted chart"))
def index_file_is_updated(workflow_test,index_file):
    workflow_test.secrets.index_file = index_file
    workflow_test.check_index_yaml(True)
