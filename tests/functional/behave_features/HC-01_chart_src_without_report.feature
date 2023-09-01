Feature: Chart source submission without report
    Partners, redhat and community users can publish their chart by submitting
    error-free chart in source format without a report.

    Scenario Outline: [HC-01-001] A partner or redhat associate submits an error-free chart source
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And an error-free chart source is used in "<chart_path>"
        When the user sends a pull request with the chart
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and chart tarball
    
        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | chart_path                  |
            | partners     | hashicorp | tests/data/vault-0.17.0.tgz |
            
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                  |
            | redhat       | redhat    | tests/data/vault-0.17.0.tgz |

    Scenario Outline: [HC-01-002] A community user submits an error-free chart source without report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And an error-free chart source is used in "<chart_path>"
        When the user sends a pull request with the chart
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment

        @community @full
        Examples:
            | vendor_type   | vendor    | chart_path                  | message                                                                                     |
            | community     | redhat    | tests/data/vault-0.17.0.tgz | Community charts require maintainer review and approval, a review will be conducted shortly |
