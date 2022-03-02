# -*- coding: utf-8 -*-
"""Chart tarball submission with report

Partners, redhat and community users can publish their chart by submitting
error-free chart in tarball format with a report.
"""
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test Chart Tarball With Report'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/report_and_chart_tar.feature', "A partner or redhat associate submits an error-free chart tarball with report")
def test_partners_or_redhat_user_submits_chart_tarball_with_report():
    """A partner or redhat associate submits an error-free chart tarball with report."""

@scenario('../features/report_and_chart_tar.feature', "A community user submits an error-free chart tarball with report")
def test_community_user_submits_chart_tarball_with_report():
    """A community user submits an error-free chart tarball with report"""

