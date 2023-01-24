Feature: Check submitted charts
    New Openshift or chart-verifier will trigger (automatically or manually) a recursive checking on
    existing submitted charts under `charts/` directory with the specified Openshift and chart-verifier
    version.

    Besides, during workflow development, engineers would like to check if the changes will break checks
    on existing submitted charts.

    @version-change
    Scenario: [HC-15-001] A new Openshift or chart-verifier version is specified either by a cron job or manually
        Given there is a github workflow for testing existing charts
        When workflow for testing existing charts is triggered
        And a new Openshift or chart-verifier version is specified
        And the vendor type is specified, e.g. partner, and/or redhat
        Then submission tests are run for existing charts
        And all results are reported back to the caller
