from behave import given, when, then

@given('a Red Hat OWNERS file is submitted for a chart with name "{chart_name}"')
def impl_chart_name(context, chart_name: str):
    context.owners_file_test.set_chart_name(chart_name)

@when('the vendor label set to "{vendor_label}" and vendor name set to {vendor_name}')
def impl_label_and_name(context, vendor_label: str, vendor_name: str):
    context.owners_file_test.vendor_label = vendor_label
    context.owners_file_test.vendor_name = vendor_name
    context.owners_file_test.vendor_category = 'redhat'
    context.owners_file_test.create_and_commit_owners_file()
    context.owners_file_test.send_pull_request()

@then('validation CI should conclude with result "{result}"')
def impl_ci_conclusion(context, result: str):
    context.owners_file_test.check_workflow_conclusion(result)