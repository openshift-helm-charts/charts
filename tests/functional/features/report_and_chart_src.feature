Feature: Report and chart source submission
    Partners or redhat associates can publish their chart by submitting
    error-free chart in source format with the report.

    Scenario: The partner hashicorp submits an error-free chart source with report for vault
        Given hashicorp is a valid partner
        And hashicorp has created an error-free chart source and report for vault
        When hashicorp sends a pull request with the vault source chart and report
        Then hashicorp sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release for the vault chart is published with corresponding report and chart tarball

    Scenario: A redhat associate submits an error-free chart source with report for vault
        Given a redhat associate has a valid identity
        And the redhat associate has created an error-free chart source and report for vault
        When the redhat associate sends a pull request with the vault source chart and report
        Then the redhat associate sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release for the vault chart is published with corresponding report and chart tarball
