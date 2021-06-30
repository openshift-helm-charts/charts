# Workflow for Partner, Red Hat, and Community Charts

## Worflow Overview

![workflow](https://user-images.githubusercontent.com/26239939/124007268-36fa3600-d9a9-11eb-9c94-b0278ae4deab.png)

Currently the chart submission to OpenShift Helm Charts repository is automated with a GitHub workflow as shown above. The workflow first runs a `Triage` job
to sanity check and categorize the submitted chart as one of `partner`, `redhat` or  `community` submission. Then according to the category, it runs one of the `Partner`, `Red Hat`,
and `Community` jobs.

## Jobs

### Triage

This job sanity checks the submitted PR and according to the path of the changed files, it categorizes the chart submission as one of the `partner`, `redhat`,
and `community`. The paths allowed are `charts/partners`, `charts/redhat`, and `charts/community`. Note that only changes to chart related files are allowed
in a PR submission, otherwise it will not pass the sanity check.

## Partner

This job verifies the submitted report and generates one if the user did not submit one. If the verification succeeds, it will automatically merge
the PR and create a release with the submitted chart and report. If the verification fails, the user will need to update the PR according to the report to pass
the checks, or the user will notify the maintainers for manually review. Note that maintainers have the option to manually merge and release the PR content if
necessary.

## Red Hat

This job verifies the submitted report and generates one if the user did not submit one. If the verification succeeds, it will automatically merge the
PR and create a release with the submitted chart and report. However, if the verification fails, it will fall back to the `Community (Red Hat)` verification
job.

## Community (Red Hat)

This job depends on the `Red Hat` verification job and only runs when the `Red Hat` job fails. Since different categories of charts have different checks to
verify and community charts have a more lenient requirement than a `Red Hat` chart, we give the charts that didn't pass the red hat verification more opportunity
to get published. Though for `Community (Red Hat)`, manual review, merge and release are required by the maintainers. In addition, the `charts.openshift.io/providerType: redhat`
annotation will be changed to `charts.openshift.io/providerType: community` in the `index.yaml`.


## Community

This job verifies the submitted report and generates one if the user did not submit one. Different from `Partner` and `Red Hat` charts, the workflow never
auto-merges and releases the PR. Instead, a manual review and merge is required by the maintainers, even if the report passed all verification steps. 
