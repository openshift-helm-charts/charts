# -*- coding: utf-8 -*-
"""
Report does not include a check
Partners, redhat and community users submits only report which does not include full set of checks
"""
import pytest
from pytest_bdd import (
        scenario,
        given,
        parsers
)

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Report with missing checks'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/HC-11_report_with_missing_checks.feature', "[HC-11-001] A user submits a report with missing checks")
def test_report_submission_with_missing_checks():
    """A user submits a report with missing checks."""


@given(parsers.parse("the report has a <check> missing"))
def report_has_a_check_missing(workflow_test, check):
    workflow_test.process_report(missing_check=check)
