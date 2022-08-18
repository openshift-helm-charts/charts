Feature: Chart test takes longer time and exceeds default timeout
  Partners, redhat or community user submit charts which result in errors

  Examples:
    | chart_path                                  | 
    | tests/data/vault-test-timeout-0.17.0.tgz    | 

  Scenario Outline: [HC-16-001] A partner or community user submits chart that takes more than 30 mins
    Given the vendor <vendor> has a valid identity as <vendor_type>
    And an error-free chart tarball is used in <chart_path>
    When the user sends a pull request with the chart
    Then the pull request is not merged
    And user gets the <message> in the pull request comment

    Examples:
      | vendor_type  | vendor         | message                                                                                     |
      | partners     | hashicorp      | Chart test failure: timed out waiting for the condition                                     |
      | community    | redhat         | Community charts require maintainer review and approval, a review will be conducted shortly |
  
  Scenario Outline: [HC-16-002] A redhat associate submits a chart that takes more than 30 mins
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And an error-free chart tarball is used in <chart_path>
        When the user sends a pull request with the chart
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and chart tarball
    
    Examples:
      | vendor_type  | vendor       |
      | redhat       | redhat       |

