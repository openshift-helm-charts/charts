# -*- coding: utf-8 -*-
"""
Report only submission in json format
Partners, redhat and community users trying to publish chart by submitting report in json format
"""
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test Report in Json Format'
    test_report = 'tests/data/report.json'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/report_in_json_format.feature', "An user submits an report in json format")
def an_user_submits_report_in_json_format():
    """An user submits an report in json format."""

