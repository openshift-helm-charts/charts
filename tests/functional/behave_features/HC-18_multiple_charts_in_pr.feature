Feature: Multiple charts submission in one PR
    If partners, redhat and community users try to submit multiple charts in one single PR
    they will get an appropriate error message

    Scenario Outline: [HC-18-001] A user submits a PR with multiple reports
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And user wants to send two reports as in "<report_path_1>" and "<report_path_2>"
        When the user sends a pull request with the report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment
    
        @partners @full @smoke
        Examples:
            | vendor_type  | vendor    | report_path_1                         | report_path_2                        | message                                                                         |
            | partners     | hashicorp | tests/data/common/partner/report.yaml | tests/data/HC-18/partner/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | report_path_1                        | report_path_2                       | message                                                                         |
            | redhat       | redhat    | tests/data/common/redhat/report.yaml | tests/data/HC-18/redhat/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @community @full
        Examples:
            | vendor_type  | vendor    | report_path_1                           | report_path_2                          | message                                                                         |
            | community    | redhat    | tests/data/common/community/report.yaml | tests/data/HC-18/community/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |

    Scenario Outline: [HC-18-002] A user submits a PR with multiple chart sources
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And user wants to send two chart sources as in "<chart_path_1>" and "<chart_path_2>"
        When the user sends a pull request with the chart
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment
    
        @partners @full
        Examples:
            | vendor_type  | vendor    | chart_path_1                | chart_path_2                | message                                                                         |
            | partners     | hashicorp | tests/data/vault-0.17.0.tgz | tests/data/vault-0.18.0.tgz | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path_1                | chart_path_2                | message                                                                         |
            | redhat       | redhat    | tests/data/vault-0.17.0.tgz | tests/data/vault-0.18.0.tgz | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @community @full
        Examples:
            | vendor_type  | vendor    | chart_path_1                | chart_path_2                | message                                                                         |
            | community    | redhat    | tests/data/vault-0.17.0.tgz | tests/data/vault-0.18.0.tgz | A PR must contain only one chart. Current PR includes files for multiple charts |

    Scenario Outline: [HC-18-003] A user submits a PR with multiple chart tars
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And user wants to send two chart tars as in "<chart_path_1>" and "<chart_path_2>"
        When the user sends a pull request with the chart
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment
    
        @partners @full
        Examples:
            | vendor_type  | vendor    | chart_path_1                | chart_path_2                | message                                                                         |
            | partners     | hashicorp | tests/data/vault-0.17.0.tgz | tests/data/vault-0.18.0.tgz | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @redhat @full @smoke
        Examples:
            | vendor_type  | vendor    | chart_path_1                | chart_path_2                | message                                                                         |
            | redhat       | redhat    | tests/data/vault-0.17.0.tgz | tests/data/vault-0.18.0.tgz | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @community @full
        Examples:
            | vendor_type  | vendor    | chart_path_1                | chart_path_2                | message                                                                         |
            | community    | redhat    | tests/data/vault-0.17.0.tgz | tests/data/vault-0.18.0.tgz | A PR must contain only one chart. Current PR includes files for multiple charts |
    
    Scenario Outline: [HC-18-004] A user submits a PR with multiple chart one with source and other with report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And user wants to send two charts one with source "<chart_path>" and other with report "<report_path>"
        When the user sends a pull request with the chart and report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment
    
        @partners @full
        Examples:
            | vendor_type  | vendor    | chart_path                  | report_path                          | message                                                                         |
            | partners     | hashicorp | tests/data/vault-0.17.0.tgz | tests/data/HC-18/partner/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                  | report_path                         | message                                                                         |
            | redhat       | redhat    | tests/data/vault-0.17.0.tgz | tests/data/HC-18/redhat/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @community @full @smoke
        Examples:
            | vendor_type  | vendor    | chart_path                  | report_path                            | message                                                                         |
            | community    | redhat    | tests/data/vault-0.17.0.tgz | tests/data/HC-18/community/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |

    Scenario Outline: [HC-18-005] A user submits a PR with multiple chart one with tar and other with report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And user wants to send two charts one with tar "<chart_path>" and other with report "<report_path>"
        When the user sends a pull request with the chart and report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment
    
        @partners @full
        Examples:
            | vendor_type  | vendor    | chart_path                  | report_path                          | message                                                                         |
            | partners     | hashicorp | tests/data/vault-0.17.0.tgz | tests/data/HC-18/partner/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                  | report_path                         | message                                                                         |
            | redhat       | redhat    | tests/data/vault-0.17.0.tgz | tests/data/HC-18/redhat/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |
        
        @community @full
        Examples:
            | vendor_type  | vendor    | chart_path                  | report_path                            | message                                                                         |
            | community    | redhat    | tests/data/vault-0.17.0.tgz | tests/data/HC-18/community/report.yaml | A PR must contain only one chart. Current PR includes files for multiple charts |
