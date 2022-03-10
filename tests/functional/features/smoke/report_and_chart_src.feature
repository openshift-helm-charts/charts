Feature: Chart source submission with report
    Partners, redhat and community users can publish their chart by submitting
    error-free chart in source format with a report.

    Examples:
        | chart_path                     | report_path               |
        | tests/data/vault-0.17.0.tgz    | tests/data/report.yaml    |

    Scenario Outline: A partner or redhat associate submits an error-free chart source with report
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And an error-free chart source is used in <chart_path> and report in <report_path>
        When the user sends a pull request with the chart and report
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and chart tarball

        Examples:
            | vendor_type  | vendor    |
            | partners     | hashicorp |

    Scenario Outline: A community user submits an error-free chart source with report
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And an error-free chart source is used in <chart_path> and report in <report_path>
        When the user sends a pull request with the chart and report
        Then the pull request is not merged
        And user gets the <message> in the pull request comment

        Examples:
            | vendor_type   | vendor    | message                                                                                     |
            | community     | redhat    | Community charts require maintainer review and approval, a review will be conducted shortly |
