Feature: Report contains an invalid URL
    Partners, redhat and community users submits only report with an invalid URL

    Scenario Outline: [HC-04-001] A user submits a report with an invalid url
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And report is used in "<report_path>"
        When the user sends a pull request with the report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment

        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | report_path                          | message               |
            | partners     | hashicorp | tests/data/HC-04/partner/report.yaml | Missing schema in URL |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | report_path                         | message               |
            | redhat       | redhat    | tests/data/HC-04/redhat/report.yaml | Missing schema in URL |
        
        @community @full
        Examples:
            | vendor_type  | vendor    | report_path                            | message               |
            | community    | redhat    | tests/data/HC-04/community/report.yaml | Missing schema in URL |
            
