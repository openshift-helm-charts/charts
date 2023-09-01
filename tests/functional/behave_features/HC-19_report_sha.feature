Feature: Report sha value in report
  Users attempt to publish their chart by submitting report with a report sha value.
  The sha value must match the report.

  Scenario Outline: [HC-19-001] A partner or redhat associate submits an error-free report with report sha value
    Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
    And an error-free report is used in "<report_path>"
    When the user sends a pull request with the report
    Then the user sees the pull request is merged
    And the index.yaml file is updated with an entry for the submitted chart

    @partners @full @reportSha
    Examples:
      | vendor_type  | vendor    | report_path               |
      | partners     | hashicorp | tests/data/HC-19/report_sha_good/report.yaml    |



  Scenario Outline: [HC-19-002] A partner or redhat associate submits a report with invalid report sha value
    Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
    And an error-free report is used in "<report_path>"
    When the user sends a pull request with the report
    Then the pull request is not merged
    And user gets the "<message>" in the pull request comment

    @partners @full @smoke @reportSha
    Examples:
      | vendor_type  | vendor    | report_path                                          | message                                         |
      | partners     | hashicorp | tests/data/HC-19/report_sha_bad/report.yaml          | digest in report did not match report content  |

    @partners @full @reportSha
    Examples:
      | vendor_type  | vendor    | report_path                                          | message                                         |
      | partners     | hashicorp | tests/data/HC-19/report_edited_sha_bad/report.yaml   | digest in report did not match report content  |
