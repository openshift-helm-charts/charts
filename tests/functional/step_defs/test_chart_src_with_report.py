# -*- coding: utf-8 -*-
"""Chart source submission with report

Partners, redhat and community users can publish their chart by submitting
error-free chart in source format with a report.
"""
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test Chart Source With Report'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/HC-07_report_and_chart_src.feature', "[HC-07-001] A partner or redhat associate submits an error-free chart source with report")
def test_partner_or_redhat_user_submits_chart_src_with_report():
    """A partner or redhat associate submits an error-free chart source with report."""

@scenario('../features/HC-07_report_and_chart_src.feature', "[HC-07-002] A community user submits an error-free chart source with report")
def test_community_user_submits_chart_src_with_report():
    """A community user submits an error-free chart source with report"""
