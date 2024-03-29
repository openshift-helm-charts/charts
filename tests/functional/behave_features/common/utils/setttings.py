# -*- coding: utf-8 -*-
"""Settings and global variables for e2e tests"""

GITHUB_BASE_URL = "https://api.github.com"
# The sandbox repository where we run all our tests on
TEST_REPO = "openshift-helm-charts/sandbox"
# The prod repository where we create notification issues
PROD_REPO = "openshift-helm-charts/charts"
# The prod branch where we store all chart files
PROD_BRANCH = "main"
# (Deprecated) This is used to find chart certification workflow run id
CERTIFICATION_CI_NAME = "CI"
# (Replaces the above) The name of the workflow for certification, used to get its ID.
WORKFLOW_CERTIFICATION_CI = "CI"
# The name of the workflow for Red Hat OWNERS check submissions, used to get its ID.
WORKFLOW_REDHAT_OWNERS_CHECK = "Red Hat OWNERS Files"
# GitHub actions bot email for git email
GITHUB_ACTIONS_BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
