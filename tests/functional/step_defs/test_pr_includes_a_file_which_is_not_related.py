# -*- coding: utf-8 -*-
"""
PR includes a non chart related file
Partners, redhat or community user submit charts which includes a file which is not part of the chart
"""
import pytest
from pytest_bdd import scenario

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Test PR Includes A Non Related File'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/pr_includes_a_file_which_is_not_chart_related.feature', "A user submits a chart with non chart related file")
def test_user_submits_chart_with_non_related_file():
    """A user submits a chart with non chart related file"""

