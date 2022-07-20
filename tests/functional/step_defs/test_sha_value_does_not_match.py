# -*- coding: utf-8 -*-
"""SHA value in the report does not match
Partners, redhat and community users submits chart tar with report
where tar sha does not match with sha value digests.chart in the report
"""
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'SHA Value Does Not Match'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/HC-13_sha_value_does_not_match.feature', "[HC-13-001] A user submits a chart tarball with report")
def test_chart_submission_with_report():
    """A user submits a chart tarball with report."""

