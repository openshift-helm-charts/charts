# -*- coding: utf-8 -*-
"""
Report contains an invalid URL
Partners, redhat and community users submits only report with an invalid URL
"""
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Invalid Chart URL'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/HC-04_invalid_url_in_the_report.feature', "[HC-04-001] A user submits a report with an invalid url")
def test_report_submission_with_invalid_url():
    """A user submits a report with an invalid url."""


