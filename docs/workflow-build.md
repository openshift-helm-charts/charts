# Workflow for Partner, Red Hat, and Community Charts

## Worflow Overview

Currently the chart submission to OpenShift Helm Charts repository is automated with a GitHub workflow. The workflow first checks the submitted PR and according to the path of the changed files, it categorizes the chart submission as one of the `partner`, `redhat`, and `community`. The paths allowed are `charts/partners`, `charts/redhat`, and `charts/community`. Note that only chart related files for one single chart are allowed in a PR submission, otherwise it will not pass the pr content check. Then according to the category it runs different verification checks and follows different procedures to publish the chart.

## Partner

The partner workflow verifies the submitted report and generates the report if the user did not submit one. If the verification succeeds, it will automatically merge the PR and create a release with the submitted chart and report. If the verification fails, the user will need to update the PR according to the report to pass the checks, or else the user will notify the maintainers for manually review. Note that partners need to seek for exception approvals in order to publish charts with failed checks.

## Red Hat

The Red Hat workflow verifies the submitted report and generates the report if the user did not submit one. If the verification succeeds, it will automatically merge the PR and create a release with the submitted chart and report. If the verification checks contain failures, different from the partner workflow, it will always automatically merge the PR and create a release with the submitted chart and report. But the `charts.openshift.io/providerType` annotation in the released `index.yaml` will be changed to from `redhat` to `community` in case of failures.

## Community

The community workflow verifies the submitted report and generates one if the user did not submit one. Different from `Partner` and `Red Hat` charts, the workflow never auto-merges or releases the chart. Instead, it will stop at the verification step and require reviews from the maintainers. A manual review and `force-publish` is required by the maintainers even if the report passed all verification steps. 
