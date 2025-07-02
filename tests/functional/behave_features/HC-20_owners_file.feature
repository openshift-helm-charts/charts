Feature: OWNERS file submissions
    redhat can submit OWNERS file.

    Scenario Outline: [HC-20-001] An OWNERS file is submitted by redhat
        Given a Red Hat OWNERS file is submitted for a chart with name "<chart_name>"
        When the vendor label set to "<vendor_label>" and vendor name set to "<vendor_name>"
        Then validation CI should conclude with result "<result>"
            
        @owners @full @smoke
        Examples:
            | chart_name      | vendor_label | vendor_name   | result  |
            | redhat-prefixed | redhat       | Red Hat       | success |
            | missing-prefix  | redhat       | Red Hat       | failure |
            | redhat-prefixed | notredhat    | Red Hat       | failure |
            | redhat-prefixed | redhat       | Not Red Hat   | failure |