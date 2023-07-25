# -*- coding: utf-8 -*-
""" Chart test takes longer time and exceeds default timeout
    Partners, redhat or community user submit charts which result in errors
"""
import logging
import datetime
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Chart test takes more than 30mins'
    test_chart = 'tests/data/vault-test-timeout-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    start_time = datetime.datetime.now()
    yield workflow_test
    workflow_test.cleanup()
    end_time = datetime.datetime.now()
    time_diff = end_time - start_time
    total_diff_seconds = time_diff.total_seconds()
    if not int(total_diff_seconds) >= 1800:
        pytest.fail(f"Timeout is not as expected: {total_diff_seconds}")


@scenario('../features/HC-16_chart_test_takes_more_than_30mins.feature', "[HC-16-001] A partner or community user submits chart that takes more than 30 mins")
def test_partner_or_community_chart_test_takes_more_than_30mins():
    """ A partner or community submitted chart takes more than 30 mins"""

@scenario('../features/HC-16_chart_test_takes_more_than_30mins.feature', "[HC-16-002] A redhat associate submits a chart that takes more than 30 mins")
def test_redhat_chart_test_takes_more_than_30mins():
    """ A redhat submitted chart takes more than 30 mins"""