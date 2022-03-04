import pytest
from pytest_bdd import (
    scenario,
    given,
    parsers
)

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test Edited Report Failures'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/report_only_edited.feature', "A partner or redhat associate submits an edited report")
def test_partner_or_redhat_user_submits_edited_report():
    """A partner or redhat associate submits an edited report."""


@given(parsers.parse("the report includes <tested> and <supported> OpenshiftVersion values and chart <kubeversion> value"))
def report_includes_specified_versions(workflow_test,tested,supported,kubeversion):
    workflow_test.process_report(update_versions=True,supported_versions=supported,tested_version=tested,kube_version=kubeversion)



