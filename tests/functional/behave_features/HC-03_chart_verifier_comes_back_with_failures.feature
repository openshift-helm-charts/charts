Feature: Chart verifier comes back with a failure
  Partners, redhat or community user submit charts which does not contain README file

  Scenario Outline: [HC-03-001] A partner or community user submits a chart which does not contain a readme file
    Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
    And chart source is used in "<chart_path>"
    And README file is missing in the chart
    When the user pushed the chart and created pull request
    Then the pull request is not merged
    And user gets the "<message>" in the pull request comment

    @partners @smoke @full
    Examples:
        | vendor_type  | vendor    | chart_path                  | message                                                 | 
        | partners     | hashicorp | tests/data/vault-0.17.0.tgz | Chart does not have a README                            |

    @community @full
    Examples:
        | vendor_type  | vendor    | chart_path                  | message                                                 |
        | community    | redhat    | tests/data/vault-0.17.0.tgz | Community charts require maintainer review and approval |

  Scenario Outline: [HC-03-002] A redhat user submits a chart which does not contain a readme file
    Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
    And chart source is used in "<chart_path>"
    And README file is missing in the chart
    When the user pushed the chart and created pull request
    Then the user sees the pull request is merged
    And the index.yaml file is updated with an entry for the submitted chart with correct providerType
    And a release is published with corresponding report and chart tarball
  
    @redhat @full
    Examples:
        | vendor_type  | vendor    | chart_path                  |
        | redhat       | redhat    | tests/data/vault-0.17.0.tgz |

