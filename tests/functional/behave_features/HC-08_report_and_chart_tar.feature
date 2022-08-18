Feature: Chart tarball submission with report
    Partners, redhat and community users can publish their chart by submitting
    error-free chart in tarball format with a report.

    Scenario Outline: [HC-08-001] A partner or redhat associate submits an error-free chart tarball with report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And an error-free chart tarball used in "<chart_path>" and report in "<report_path>"
        When the user sends a pull request with the chart and report
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and chart tarball

        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | chart_path                     | report_path               |
            | partners     | hashicorp | tests/data/vault-0.17.0.tgz    | tests/data/report.yaml    |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                     | report_path               |
            | redhat       | redhat    | tests/data/vault-0.17.0.tgz    | tests/data/report.yaml    |
    
    Scenario Outline: [HC-08-002] A community user submits an error-free chart tarball with report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And an error-free chart tarball used in "<chart_path>" and report in "<report_path>"
        When the user sends a pull request with the chart and report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment

        @community @smoke @full
        Examples:
            | vendor_type | vendor | chart_path                  | report_path            | message                                                                                     |
            | community   | redhat | tests/data/vault-0.17.0.tgz | tests/data/report.yaml | Community charts require maintainer review and approval, a review will be conducted shortly |
