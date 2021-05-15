Feature: Pull request with the report but without the chart

    Scenario: Partner submits report without any errors
        Given the partner has created a report without any errors
        When the partner sends the pull request with the report
        Then the partner should see the pull request getting merged
        And the index.yaml is updated with a new entry

