Feature: Chart submission with errors
  Partners, redhat or community user submit charts which result in errors

  Examples:
  | vendor_type  | vendor    | chart   | version  | chart_path                     |
  | partners     | hashicorp | vault   | 0.13.0   | tests/data/vault-0.13.0.tgz    |
  | redhat       | redhat    | vault   | 0.13.0   | tests/data/vault-0.13.0.tgz    |
  | community    | redhat    | vault   | 0.13.0   | tests/data/vault-0.13.0.tgz    |

  Scenario Outline: An unauthorized user submits a chart
    Given A <user> wants to submit a chart in <chart_path>
    And <vendor> of <vendor_type> wants to submit <chart> of <version>
    And the user creates a branch to add a new chart version
    When the user sends a pull request with chart
    Then the pull request is not merged
    And user gets the <message> with steps to follow for resolving the issue in the pull request

    Examples:
      | message                                          | user         |
      | is not allowed to submit the chart on behalf of  | unauthorized |

  Scenario Outline: An authorized user submits a chart with incorrect version
    Given A <user> wants to submit a chart in <chart_path>
    And <vendor> of <vendor_type> wants to submit <chart> of <version>
    And Chart.yaml specifies a <bad_version>
    And the user creates a branch to add a new chart version
    When the user sends a pull request with chart
    Then the pull request is not merged
    And user gets the <message> with steps to follow for resolving the issue in the pull request

    Examples:
      | message                               | bad_version | user                      |
      | doesn't match the directory structure | 9.9.9       | openshift-helm-charts-bot |
