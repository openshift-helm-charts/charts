Feature: SHA value in the report does not match
    Partners, redhat and community users submits chart tar with report
    where chart sha does not match with sha value digests.chart in the report

    Examples:
      | chart_path                     | report_path               |
      | tests/data/vault-0.17.0.tgz    | tests/data/report.yaml    |
    
    Scenario Outline: A user submits a chart tarball with report
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And a chart tarball is used in <chart_path> and report in <report_path>
        And the report contains an <error>
        When the user sends a pull request with the chart tar and report
        Then the pull request is not merged
        And user gets the <message> in the pull request comment

        Examples:
            | vendor_type  | vendor    | error        | message                 |
            | partners     | hashicorp | sha_mismatch | Digest is not matching  | 
            | redhat       | redhat    | sha_mismatch | Digest is not matching  |
            | community    | redhat    | sha_mismatch | Digest is not matching  |
