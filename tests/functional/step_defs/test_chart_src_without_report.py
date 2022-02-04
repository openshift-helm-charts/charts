# -*- coding: utf-8 -*-
"""Chart source submission without report

Partners, redhat and community users can publish their chart by submitting
error-free chart in source format without a report.
"""
import pytest
from pytest_bdd import scenario


from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test Chart Source Without Report'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/chart_src_without_report.feature', "A partner or redhat associate submits an error-free chart source")
def test_partner_or_redhat_user_submits_chart_src():
    """A partner or redhat associate submits an error-free chart source."""

@scenario('../features/chart_src_without_report.feature', "A community user submits an error-free chart source without report")
def test_community_user_submits_chart_src():
    """A community user submits an error-free chart source without report"""
