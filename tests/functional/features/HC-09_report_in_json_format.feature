Feature: Report only submission in json format
    Partners, redhat and community users trying to publish chart by submitting report in json format

    Examples:
        | report_path               | message                                                         |
        | tests/data/report.json    | One of these must be modified: report, chart source, or tarball |
    

    Scenario Outline: [HC-09-001] An user submits an report in json format
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And report is used in <report_path>
        When the user sends a pull request with the report
        Then the pull request is not merged
        And user gets the <message> in the pull request comment
    
        Examples:
            | vendor_type  | vendor    | 
            | partners     | hashicorp | 
            | redhat       | redhat    |
            | community    | redhat    |
