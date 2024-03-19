from behave import fixture, use_fixture
from common.utils.owner_file_submission import OwnersFileSubmissionsE2ETest
from common.utils.chart_certification import ChartCertificationE2ETestSingle
from common.utils.chart_certification import ChartCertificationE2ETestMultiple


@fixture
def workflow_test(context):
    context.workflow_test = ChartCertificationE2ETestSingle(test_name=context.test_name)
    yield context.workflow_test
    context.workflow_test.cleanup()


@fixture
def submitted_chart_test(context):
    context.chart_test = ChartCertificationE2ETestMultiple()
    yield context.chart_test
    context.chart_test.cleanup()

@fixture
def owners_file_test(context):
    context.owners_file_test = OwnersFileSubmissionsE2ETest(test_name=context.test_name)
    yield context.owners_file_test
    context.owners_file_test.cleanup()

def before_scenario(context, scenario):
    context.test_name = scenario.name.split("@")[0][:-4].split("]")[1]
    if "version-change" in scenario.tags:
        print("[INFO] Using submitted charts fixture")
        use_fixture(submitted_chart_test, context)
    elif 'owners' in scenario.tags:
        # TODO(komish): This if/else logic doesn't scale nicely when E2E context
        # are added OTHER than simply "chart certification". Right now, if I had
        # a feature file that had both a chart certification AND an OWNERS file
        # test, we would not have the chart certification related fixtures in
        # the context.
        #
        # In the future, rework this such that the necessary fixtures are all
        # added to the context for each scenario. That might mean adding tags to
        # existing features to indicate what type of E2E scenario it is and
        # adding the necessary fixture that way.
        #
        # E.g @certification to indicate the workflow_test fixture is necessary.
        print('[INFO]: adding owners file tests fixture to context')
        use_fixture(owners_file_test, context)
    else:
        print('[INFO]: adding certification workflow test fixture to context')
        use_fixture(workflow_test, context)
