# -*- coding: utf-8 -*-
"""Settings and global variables for e2e tests"""

GITHUB_BASE_URL = 'https://api.github.com'
# The sandbox repository where we run all our tests on
TEST_REPO = 'openshift-helm-charts/sandbox'
# The prod repository where we create notification issues
PROD_REPO = 'openshift-helm-charts/charts'
# The prod branch where we store all chart files
PROD_BRANCH = 'main'
# This is used to find chart certification workflow run id
CERTIFICATION_CI_NAME = 'CI'
# GitHub actions bot email for git email
GITHUB_ACTIONS_BOT_EMAIL = '41898282+github-actions[bot]@users.noreply.github.com'
