# Certification Tests for Partner and Red Hat Charts

This test suite contains multiple behavior-driven development (BDD) tests that trigger automated pull request creations and running the chart submission workflow under the [sandbox repository](https://github.com/openshift-helm-charts/sandbox). Currently there are two main motivations. Accordingly, two test workdlows are implemented to address the problems.

## Motivation #1

As an OpenShift Helm partner or Red Hat associate, I would like Red Hat to automatically run a certification flow for my existing charts whenever there is a significant change to the certification flow (e.g. new OpenShift or chart-verifier version), so that I know whether my charts can be auto-certified or I need to take action to submit a new chart version.

## Motivation #2

During the development of GitHub workflow, we want to automate the process of chart submission process so that no manual forks and PR submissions are needed to test the workflow changes. Previously, all processes are done manually from creating pull requests with test charts to cleaning up the release assets.

## Test Submitted Charts on OpenShift / Chart Verifier Update

![CI Test Logic](../assets/ci_test_logic_schedule.png "CI Test Logic (Schedule)")

For every new release of chart verifier or any upgrade to certification clusters, we will run a certification test for all charts that do contain a chart package but without a report. Given that the certification test passes, we will ask the chart owners for permissions through GitHub issues and update the index.yaml to indicate the certification is also valid for the new version of OpenShift or the new version of chart verifier. In the event where the test fails we will notify the owners through GitHub issues of the version change and invite them to submit a new version of the chart that meets the new certification criteria. All test branches as well as the releases under the sandbox are cleaned up after the tests are finished.

Refer to [workflow file](../.github/workflows/test.yml) for implementation details.

## Test Release Workflow on Pull Requests

![CI Test Logic](../assets/ci_test_logic_pr.png "CI Test Logic (Pull Request)")

For any pull request that updates workflow under `.github/workflows`, dependency scripts under `scripts/src`, or tests under `tests/`, we first sanity checks that the submitter of the PR is listed under `approver` of `OWNERS` file and then run the automated tests. All test branches as well as the releases under the sandbox are cleaned up after the tests are finished.

Refer to [workflow file](../.github/workflows/schedule.yml) for implementation details.
