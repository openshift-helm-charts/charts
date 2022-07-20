#Smoke Test Suite

These feature files contains all the smoke tests (a subset of the all the feature files present under "features" directory).

Smoke tests will run as part of the any workflow change done in the certifcation flow.

This test suite cover the basic features of chart certification flow. Also tries to touch each verndor_type ie partners, redhat and community. 

Many scenarios contains either partners or redhat path as they mostly share a common code.

## Guideline for adding new testcases

Motivation to design this test suite was to minimize testing time and any future test addition to this test suite should not exceed testing time limit of 30 minutes.

Try to avoid expensive tests which require chart to be installed in certification cluster.