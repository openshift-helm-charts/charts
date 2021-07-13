Feature: Chart source only submission
    Partners or redhat associates can publish their chart by submitting
    error-free chart in source format without the report.

    Scenario: The partner hashicorp submits a error-free chart source for vault
        Given hashicorp is a valid partner
        And hashicorp has created an error-free chart source for vault
        When hashicorp sends a pull request with the vault source chart
        Then hashicorp should see the pull request getting merged
        And the index.yaml file is updated with a new entry
        And a release for the vault chart is published with corresponding report and chart tarball

    Scenario: The redhat associate submits a error-free report for the vault chart
        Given a redhat associate has a valid identity
        And the redhat associate has created an error-free chart source for vault
        When the redhat associate sends a pull request with the vault source chart
        Then the redhat associate should see the pull request getting merged
        And the index.yaml file is updated with a new entry
        And a release for the vault chart is published with corresponding report and chart tarball
