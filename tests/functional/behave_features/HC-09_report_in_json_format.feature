Feature: Report only submission in json format
    If partners, redhat and community users try to publish chart by submitting report 
    in json format then will receive an error message

    Scenario Outline: [HC-09-001] An user submits a report in json format
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And report is used in "<report_path>"
        When the user sends a pull request with the report
        Then the pull request is not merged
        #this step is failing currently https://issues.redhat.com/browse/HELM-396
        And user gets the "<message>" in the pull request comment
    
        @partners
        Examples:
            | vendor_type  | vendor    | report_path                          | message                                                         |
            | partners     | hashicorp | tests/data/HC-09/partner/report.json | One of these must be modified: report, chart source, or tarball |

        @redhat
        Examples:
            | vendor_type  | vendor    | report_path                         | message                                                         |
            | redhat       | redhat    | tests/data/HC-09/redhat/report.json | One of these must be modified: report, chart source, or tarball |
        
        @community
        Examples:
            | vendor_type  | vendor    | report_path                            | message                                                         |
            | community    | redhat    | tests/data/HC-09/community/report.json | One of these must be modified: report, chart source, or tarball |
    
