# -*- coding: utf-8 -*-
""" Chart submission with errors
    Partners, redhat or community user submit charts which result in errors
"""
import logging
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Chart Submission with Errors'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/HC-14_user_submits_chart_with_errors.feature', "[HC-14-001] An unauthorized user submits a chart")
def test_chart_submission_by_unauthorized_user():
    """An unauthorized user submits a chart"""

@scenario('../features/HC-14_user_submits_chart_with_errors.feature', "[HC-14-002] An authorized user submits a chart with incorrect version")
def test_chart_submission_with_incorrect_version():
    """ An authorized user submits a chart with incorrect version """

