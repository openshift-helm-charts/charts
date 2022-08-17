Feature: Chart submission with errors
  Partners, redhat or community user submit charts which result in errors

  Scenario Outline: [HC-14-001] An unauthorized user submits a chart
    Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
    And A "<user>" wants to submit a chart in "<chart_path>"
    And the user creates a branch to add a new chart version
    When the user sends a pull request with the chart
    Then the pull request is not merged
    And user gets the "<message>" in the pull request comment

    @partners @smoke @full
    Examples:
      | vendor_type  | vendor    | chart_path                     | message                                          | user         |
      | partners     | hashicorp | tests/data/vault-0.17.0.tgz    | is not allowed to submit the chart on behalf of  | unauthorized |
    
    @redhat @full
    Examples:
      | vendor_type  | vendor    | chart_path                     | message                                          | user         |
      | redhat       | redhat    | tests/data/vault-0.17.0.tgz    | is not allowed to submit the chart on behalf of  | unauthorized |
    
    @community @full
    Examples:
      | vendor_type  | vendor    | chart_path                     | message                                          | user         |
      | community    | redhat    | tests/data/vault-0.17.0.tgz    | is not allowed to submit the chart on behalf of  | unauthorized |

  Scenario Outline: [HC-14-002] An authorized user submits a chart with incorrect version
    Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
    And An authorized user wants to submit a chart in "<chart_path>"
    And Chart.yaml specifies a "<bad_version>"
    And the user creates a branch to add a new chart version
    When the user sends a pull request with the chart
    Then the pull request is not merged
    And user gets the "<message>" in the pull request comment

    @partners @smoke @full
    Examples:
      | vendor_type  | vendor    | chart_path                     | message                               | bad_version | 
      | partners     | hashicorp | tests/data/vault-0.17.0.tgz    | doesn't match the directory structure | 9.9.9       |
    
    @redhat @full
    Examples:
      | vendor_type  | vendor    | chart_path                     | message                               | bad_version |
      | redhat       | redhat    | tests/data/vault-0.17.0.tgz    | doesn't match the directory structure | 9.9.9       |
    
    @community @full
    Examples:
      | vendor_type  | vendor    | chart_path                     | message                               | bad_version |
      | community    | redhat    | tests/data/vault-0.17.0.tgz    | doesn't match the directory structure | 9.9.9       |
