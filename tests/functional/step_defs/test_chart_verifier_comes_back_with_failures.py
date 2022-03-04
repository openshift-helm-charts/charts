# -*- coding: utf-8 -*-
"""
Chart verifier comes back with a failure
Partners, redhat or community user submit charts which does not contain README file
"""
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test Chart Submission Without Readme'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/chart_verifier_comes_back_with_failures.feature', "A partner or community user submits a chart which does not contain a readme file")
def test_partner_or_community_user_submits_chart_without_readme():
    """A partner or community user submits a chart which does not contain a readme file"""

@scenario('../features/chart_verifier_comes_back_with_failures.feature', "A redhat user submits a chart which does not contain a readme file")
def test_redhat_user_submits_chart_without_readme():
    """A redhat user submits a chart which does not contain a readme file"""

