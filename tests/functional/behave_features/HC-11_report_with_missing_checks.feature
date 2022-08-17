Feature: Report does not include a check
    Partners, redhat and community users submits only report which does not include full set of checks
    
    Scenario Outline: [HC-11-001] A user submits a report with missing checks
        Given the vendor "<vendor>" has a valid identity as "<vendor_type>"
        And a "<report_path>" is provided
        And the report has a "<check>" missing
        When the user sends a pull request with the report
        Then the pull request is not merged
        And user gets the "<message>" in the pull request comment

        @partners @smoke @full
        Examples:
            | vendor_type  | vendor    | report_path            | check                  | message                                            |
	          | partners     | hashicorp | tests/data/report.yaml | v1.0/helm-lint         | Missing mandatory check : v1.0/helm-lint           |
	      
        @community @full
        Examples:
            | vendor_type  | vendor    | report_path            | check                  | message                                            |
            | community    | redhat    | tests/data/report.yaml | v1.0/helm-lint         | Missing mandatory check : v1.0/helm-lint           |
	      
        @partners @full
        Examples:
            | vendor_type  | vendor    | report_path            | check                  | message                                            |
            | partners     | hashicorp | tests/data/report.yaml | v1.0/not-contains-crds | Missing mandatory check : v1.0/not-contains-crds   |
            # Commented this scenario, since it is failing , raised bug : https://issues.redhat.com/browse/HELM-289 , we can uncomment again when the issue fixed 
	          #| redhat       | redhat    | tests/data/report.yaml |v1.0/helm-lint          | Missing mandatory check : v1.0/helm-lint           |