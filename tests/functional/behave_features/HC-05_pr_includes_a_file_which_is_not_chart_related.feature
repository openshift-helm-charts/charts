Feature: PR includes a non chart related file
  Partners, redhat or community user submit charts which includes a file which is not part of the chart

  Scenario Outline: [HC-05-001] A user submits a chart with non chart related file
    Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
    And chart source is used in "<chart_path>"
    And user adds a non chart related file
    When the user sends a pull request with both chart and non related file
    Then the pull request is not merged
    And user gets the "<message>" in the pull request comment

    @partners @smoke @full
    Examples:
        | vendor_type  | vendor    | chart_path                  | message                                             |
        | partners     | hashicorp | tests/data/vault-0.17.0.tgz | PR includes one or more files not related to charts |
    
    @redhat @full
    Examples:
        | vendor_type  | vendor    | chart_path                  | message                                             |
        | redhat       | redhat    | tests/data/vault-0.17.0.tgz | PR includes one or more files not related to charts |
    
    @community @full
    Examples:
        | vendor_type  | vendor    | chart_path                  | message                                             |
        | community    | redhat    | tests/data/vault-0.17.0.tgz | PR includes one or more files not related to charts |
