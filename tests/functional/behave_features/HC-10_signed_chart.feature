Feature: Signed chart submission
    Partners or redhat users can publish their signed chart

    Scenario Outline: [HC-10-001] A partner or redhat associate submits a signed chart tarball without report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And a signed chart tarball is used in "<chart_path>" and public key in "<public_key_file>"
        When the user sends a pull request with the chart
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report, tarball, prov and key

        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | chart_path                                     | public_key_file                                   |
            | partners     | hashicorp | tests/data/HC-10/signed_chart/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/public_key_good.asc |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                                     | public_key_file                                   |
            | redhat       | redhat    | tests/data/HC-10/signed_chart/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/public_key_good.asc |

    Scenario Outline: [HC-10-002] A partner or redhat associate submits a signed chart tarball with report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And a signed chart tar is used in "<chart_path>", report in "<report_path>" and public key in "<public_key_file>"
        When the user sends a pull request with the chart
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report, tarball, prov and key

        @partners @full
        Examples:
            | vendor_type  | vendor    | chart_path                                     | report_path                                              | public_key_file                                   |
            | partners     | hashicorp | tests/data/HC-10/signed_chart/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/report/partner/report.yaml | tests/data/HC-10/signed_chart/public_key_good.asc |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                                     | report_path                                             | public_key_file                                   |
            | redhat       | redhat    | tests/data/HC-10/signed_chart/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/report/redhat/report.yaml | tests/data/HC-10/signed_chart/public_key_good.asc |
    
    Scenario Outline: [HC-10-003] A partner or redhat associate submits a signed chart report
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And signed chart report used in "<report_path>" and public key in "<public_key_file>"
        When the user sends a pull request with the report
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and key

        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | report_path                                              | public_key_file                                   |
            | partners     | hashicorp | tests/data/HC-10/signed_chart/report/partner/report.yaml | tests/data/HC-10/signed_chart/public_key_good.asc |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | report_path                                             | public_key_file                                   |
            | redhat       | redhat    | tests/data/HC-10/signed_chart/report/redhat/report.yaml | tests/data/HC-10/signed_chart/public_key_good.asc |
    
    Scenario Outline: [HC-10-004] A partner or redhat associate submits an unsigned chart tarball
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And unsigned chart tarball is used in "<chart_path>" and public key used "<public_key_file>" in owners
        When the user sends a pull request with the chart
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and chart tarball

        @partners @full
        Examples:
            | vendor_type  | vendor    | chart_path                  | public_key_file                                   |
            | partners     | hashicorp | tests/data/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/public_key_good.asc |
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                  | public_key_file                                   |
            | redhat       | redhat    | tests/data/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/public_key_good.asc |
    
    Scenario Outline: [HC-10-005] A partner or redhat associate submits a signed chart tarball when public key is not in owners
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And signed chart tar used in "<chart_path>"
        When the user sends a pull request with the chart
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report, chart tar and prov file

        @partners @full
        Examples:
            | vendor_type  | vendor    | chart_path                                     | 
            | partners     | hashicorp | tests/data/HC-10/signed_chart/vault-0.17.0.tgz | 
        
        @redhat @full
        Examples:
            | vendor_type  | vendor    | chart_path                                     | 
            | redhat       | redhat    | tests/data/HC-10/signed_chart/vault-0.17.0.tgz |
    
    Scenario Outline: [HC-10-006] A partner or redhat associate submits a signed chart tarball with wrong key in OWNERS file
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And a signed chart tarball is used in "<chart_path>" and public key in "<public_key_file>"
        When the user sends a pull request with the chart
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment

        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | chart_path                                     | public_key_file                                  | message                       |
            | partners     | hashicorp | tests/data/HC-10/signed_chart/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/public_key_bad.asc | Signature verification failed |
        
        # @redhat @full
        # Examples:
        #     | vendor_type  | vendor    | chart_path                                     | public_key_file                                  | message                       | 
        #     | redhat       | redhat    | tests/data/HC-10/signed_chart/vault-0.17.0.tgz | tests/data/HC-10/signed_chart/public_key_bad.asc | Signature verification failed |


