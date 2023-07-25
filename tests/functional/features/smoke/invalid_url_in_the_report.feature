Feature: Report contains an invalid URL
    Partners, redhat and community users submits only report with an invalid URL

    Examples:
      | report_path               |
      | tests/data/report.yaml    |
    
    Scenario Outline: A user submits a report with an invalid url
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And a <report_path> is provided
        And the report contains an <invalid_url>
        When the user sends a pull request with the report
        Then the pull request is not merged
        And user gets the <message> in the pull request comment

        Examples:
            | vendor_type  | vendor    | invalid_url                                | message                 |
            | partners     | hashicorp | example.com/vault-0.13.0.tgz               | Missing schema in URL   |
            | redhat       | redhat    | htts://example.com/vault-0.13.0.tgz        | Invalid schema          |
            | community    | redhat    | https:example.comvault-0.13.0.tgz          | Invalid URL             |
