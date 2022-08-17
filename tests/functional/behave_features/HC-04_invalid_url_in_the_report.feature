Feature: Report contains an invalid URL
    Partners, redhat and community users submits only report with an invalid URL

    Scenario Outline: [HC-04-001] A user submits a report with an invalid url
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And a "<report_path>" is provided
        And the report contains an "<invalid_url>"
        When the user sends a pull request with the report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment

        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | report_path            | invalid_url                         | message               |
            | partners     | hashicorp | tests/data/report.yaml | example.com/vault-0.13.0.tgz        | Missing schema in URL |
        
        @redhat @smoke @full
        Examples:
            | vendor_type  | vendor    | report_path            | invalid_url                         | message               |
            | redhat       | redhat    | tests/data/report.yaml | htts://example.com/vault-0.13.0.tgz | Invalid schema        |
        
        @community @smoke @full
        Examples:
            | vendor_type  | vendor    | report_path            | invalid_url                         | message               |
            | community    | redhat    | tests/data/report.yaml | https:example.comvault-0.13.0.tgz   | Invalid URL           |
        
        @partners @full
        Examples:
            | vendor_type  | vendor    | report_path            | invalid_url                         | message               |
            | partners     | hashicorp | tests/data/report.yaml | htts://example.com/vault-0.13.0.tgz | Invalid schema        |
            | partners     | hashicorp | tests/data/report.yaml | https:example.comvault-0.13.0.tgz   | Invalid URL           |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | report_path            | invalid_url                         | message               |
            | redhat       | redhat    | tests/data/report.yaml | example.com/vault-0.13.0.tgz        | Missing schema in URL |
            | redhat       | redhat    | tests/data/report.yaml | https:example.comvault-0.13.0.tgz   | Invalid URL           |
        
        @community @full
        Examples:
            | vendor_type  | vendor    | report_path            | invalid_url                         | message               |
            | community    | redhat    | tests/data/report.yaml | example.com/vault-0.13.0.tgz        | Missing schema in URL |
            | community    | redhat    | tests/data/report.yaml | htts://example.com/vault-0.13.0.tgz | Invalid schema        |
            
