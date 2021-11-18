# -*- coding: utf-8 -*-
"""Check submitted charts

New Openshift or chart-verifier will trigger (automatically or manually) a recursive checking on
existing submitted charts under `charts/` directory with the specified Openshift and chart-verifier
version.

Besides, during workflow development, engineers would like to check if the changes will break checks
on existing submitted charts.
"""
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
from functional.utils.chart_certification import ChartCertificationE2ETestMultiple

@pytest.fixture
def workflow_test():
    workflow_test = ChartCertificationE2ETestMultiple()
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/check_submitted_charts.feature', "A new Openshift or chart-verifier version is specified either by a cron job or manually")
def test_submitted_charts():
    """A new Openshift or chart-verifier version is specified either by a cron job or manually."""


@given("there's a github workflow for testing existing charts")
def theres_github_workflow_for_testing_charts():
    """there's a github workflow for testing existing charts."""


@when("a new Openshift or chart-verifier version is specified")
def new_openshift_or_verifier_version_is_specified():
    """a new Openshift or chart-verifier version is specified."""


@when("the vendor type is specified, e.g. partner, and/or redhat")
def vendor_type_is_specified():
    """the vendor type is specified, e.g. partner, and/or redhat."""


@when("workflow for testing existing charts is triggered")
def workflow_is_triggered():
    """workflow for testing existing charts is triggered."""


@then("submission tests are run for existing charts")
def submission_tests_run_for_submitted_charts(workflow_test):
    """submission tests are run for existing charts."""
    workflow_test.process_all_charts()


@then("all results are reported back to the caller")
def all_results_report_back_to_caller():
    """all results are reported back to the caller."""
