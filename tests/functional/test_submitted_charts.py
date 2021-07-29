# -*- coding: utf-8 -*-
"""Check submitted charts

New Openshift or chart-verifier will trigger (automatically or manually) a recursive checking on
existing submitted charts under `charts/` directory with the specified Openshift and chart-verifier
version.

Besides, during workflow development, engineers would like to check if the changes will break checks
on existing submitted charts.
"""
import os
import json
import base64
import pathlib
import logging
import shutil
from tempfile import TemporaryDirectory
from dataclasses import dataclass
from string import Template

import git
import yaml
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from functional.utils import get_name_and_version_from_report, github_api, get_run_id, get_run_result, get_all_charts, get_release_by_tag, TEST_REPO, PROD_REPO, PROD_BRANCH
from functional.notifier import create_verification_issue

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture
def secrets():
    @dataclass
    class Secret:
        software_name: str
        software_version: str
        test_repo: str
        bot_name: str
        bot_token: str
        vendor_type: str
        pr_base_branch: str
        base_branches: list
        pr_branches: list
        is_prod: bool

        submitted_charts: list = None
        owners_file_content: str = """\
chart:
  name: ${chart_name}
  shortDescription: Test chart for testing chart submission workflows.
publicPgpKey: null
users:
- githubUsername: ${bot_name}
vendor:
  label: ${vendor}
  name: ${vendor}
"""
        test_chart: str = 'tests/data/vault-0.13.0.tgz'
        test_report: str = 'tests/data/report.yaml'
        chart_name, chart_version = get_name_and_version_from_report(
            test_report)

    # Accepts 'True' or 'False', depending on whether we want to tag chart owners, or bot for testing
    is_prod = os.environ.get("IS_PROD")
    if not is_prod:
        # Default to False to avoid spamming tags to chart owners
        is_prod = False
    else:
        is_prod = is_prod == 'True'

    software_name = os.environ.get("SOFTWARE_NAME")
    if not software_name:
        raise Exception("SOFTWARE_NAME environment variable not defined")

    software_version = os.environ.get("SOFTWARE_VERSION")
    if not software_version:
        raise Exception("SOFTWARE_VERSION environment variable not defined")

    bot_name = os.environ.get("BOT_NAME")
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        bot_name = "github-actions[bot]"
        bot_token = os.environ.get("GITHUB_TOKEN")
        if not bot_token:
            raise Exception("BOT_TOKEN environment variable not defined")

    vendor_type = os.environ.get("VENDOR_TYPE")
    if not vendor_type:
        logger.info(
            f"VENDOR_TYPE environment variable not defined, default to `all`")
        vendor_type = 'all'

    base_branches = []
    pr_branches = []

    test_repo = TEST_REPO
    repo = git.Repo()
    pr_base_branch = repo.active_branch.name
    r = github_api(
        'get', f'repos/{test_repo}/branches', bot_token)
    branches = json.loads(r.text)
    branch_names = [branch['name'] for branch in branches]
    if pr_base_branch not in branch_names:
        logger.info(
            f"{test_repo}:{pr_base_branch} does not exists, creating with local branch")
    repo.git.push(f'https://x-access-token:{bot_token}@github.com/{test_repo}',
                  f'HEAD:refs/heads/{pr_base_branch}', '-f')

    secrets = Secret(software_name, software_version, test_repo, bot_name,
                     bot_token, vendor_type, pr_base_branch, base_branches, pr_branches, is_prod)
    yield secrets

    # Teardown step to cleanup branches
    repo.git.worktree('prune')
    for base_branch in secrets.base_branches:
        logger.info(f"Delete '{test_repo}:{base_branch}'")
        github_api(
            'delete', f'repos/{test_repo}/git/refs/heads/{base_branch}', bot_token)

        logger.info(f"Delete '{test_repo}:{base_branch}-gh-pages'")
        github_api(
            'delete', f'repos/{test_repo}/git/refs/heads/{base_branch}-gh-pages', bot_token)

        logger.info(f"Delete local '{base_branch}'")
        try:
            repo.git.branch('-D', base_branch)
        except git.exc.GitCommandError:
            logger.info(f"Local '{base_branch}' does not exist")

    for pr_branch in secrets.pr_branches:
        logger.info(f"Delete '{test_repo}:{pr_branch}'")
        github_api(
            'delete', f'repos/{test_repo}/git/refs/heads/{pr_branch}', bot_token)

    logger.info("Delete local 'tmp' branch")
    repo.git.branch('-D', 'tmp')


@scenario('features/check_submitted_charts.feature', "A new Openshift or chart-verifier version is specified either by a cron job or manually")
def test_submitted_charts():
    """A new Openshift or chart-verifier version is specified either by a cron job or manually."""


@given("there's a github workflow for testing existing charts")
def theres_github_workflow_for_testing_charts():
    """there's a github workflow for testing existing charts."""


@when("a new Openshift or chart-verifier version is specified")
def new_openshift_or_verifier_version_is_specified():
    """a new Openshift or chart-verifier version is specified."""


@when("the vendor type is specified, e.g. partner, and/or redhat")
def vendor_type_is_specified():
    """the vendor type is specified, e.g. partner, and/or redhat."""


@when("workflow for testing existing charts is triggered")
def workflow_is_triggered():
    """workflow for testing existing charts is triggered."""


@then("submission tests are run for existing charts")
def submission_tests_run_for_submitted_charts(secrets):
    """submission tests are run for existing charts."""

    with TemporaryDirectory(prefix='tci-') as temp_dir:
        owners_table = dict()
        pr_number_list = []

        repo = git.Repo(os.getcwd())
        if os.environ.get('WORKFLOW_DEVELOPMENT'):
            logger.info("Wokflow development enabled")
            repo.git.add(A=True)
            repo.git.commit('-m', 'Checkpoint')

        # Get SHA from 'pr_base_branch' branch
        r = github_api(
            'get', f'repos/{secrets.test_repo}/git/ref/heads/{secrets.pr_base_branch}', secrets.bot_token)
        j = json.loads(r.text)
        pr_base_branch_sha = j['object']['sha']

        # Make PR's from a temporary directory
        old_cwd = os.getcwd()
        logger.info(f'Worktree directory: {temp_dir}')
        repo.git.worktree('add', '--detach', temp_dir, f'HEAD')

        # Run submission flow test on charts from main branch
        os.chdir(temp_dir)
        repo = git.Repo(temp_dir)
        repo.git.fetch(
            f'https://github.com/{secrets.test_repo}.git', f'{PROD_BRANCH}:{PROD_BRANCH}', '-f')
        repo.git.checkout(PROD_BRANCH, 'charts')
        repo.git.restore('--staged', 'charts')
        secrets.submitted_charts = get_all_charts(
            'charts', secrets.vendor_type)
        logger.info(
            f"Found charts for {secrets.vendor_type}: {secrets.submitted_charts}")
        repo.git.checkout('-b', 'tmp')

        for vendor_type, vendor_name, chart_name, chart_version in secrets.submitted_charts:
            chart_dir = f'charts/{vendor_type}/{vendor_name}/{chart_name}'
            base_branch = f'{secrets.pr_base_branch}-{vendor_type}-{vendor_name}-{chart_name}-{chart_version}'
            pr_branch = f'{secrets.pr_base_branch}-{vendor_type}-{vendor_name}-{chart_name}-{chart_version}-pr'
            secrets.base_branches.append(base_branch)
            secrets.pr_branches.append(pr_branch)
            repo.git.checkout('tmp')
            repo.git.checkout('-b', base_branch)

            # Get SHA from 'dev-gh-pages' branch
            logger.info(
                f"Create '{secrets.test_repo}:{base_branch}-gh-pages' from '{secrets.test_repo}:dev-gh-pages'")
            r = github_api(
                'get', f'repos/{secrets.test_repo}/git/ref/heads/dev-gh-pages', secrets.bot_token)
            j = json.loads(r.text)
            dev_gh_pages_sha = j['object']['sha']

            # Create a new gh-pages branch for testing
            data = {'ref': f'refs/heads/{base_branch}-gh-pages',
                    'sha': dev_gh_pages_sha}
            r = github_api(
                'post', f'repos/{secrets.test_repo}/git/refs', secrets.bot_token, json=data)

            # Create a new base branch for testing current chart
            logger.info(
                f"Create {secrets.test_repo}:{base_branch} for testing")
            r = github_api(
                'get', f'repos/{secrets.test_repo}/branches', secrets.bot_token)
            branches = json.loads(r.text)
            branch_names = [branch['name'] for branch in branches]
            if base_branch in branch_names:
                logger.warning(
                    f"{secrets.test_repo}:{base_branch} already exists")
                continue

            data = {'ref': f'refs/heads/{base_branch}',
                    'sha': pr_base_branch_sha}
            r = github_api(
                'post', f'repos/{secrets.test_repo}/git/refs', secrets.bot_token, json=data)

            # Modify the OWNERS file so the bot account can test chart submission flow
            values = {'bot_name': secrets.bot_name,
                      'vendor': vendor_name, 'chart_name': chart_name}
            content = Template(secrets.owners_file_content).substitute(values)
            # Use bot account for notifications unless in production
            if secrets.is_prod:
                with open(f'{chart_dir}/OWNERS', 'r') as fd:
                    try:
                        owners = yaml.safe_load(fd)
                        # Pick owner ids for notification
                        owners_table[chart_dir] = [
                            owner.get(['githubUsername'], '') for owner in owners['users']]
                    except yaml.YAMLError as err:
                        logger.warning(
                            f"Error parsing OWNERS of {chart_dir}: {err}")
            else:
                owners_table[chart_dir] = [secrets.bot_name]
            with open(f'{chart_dir}/OWNERS', 'w') as fd:
                fd.write(content)

            # Push OWNERS file to the test_repo
            logger.info(
                f"Push OWNERS file to '{secrets.test_repo}:{base_branch}'")
            repo.git.add(f'{chart_dir}/OWNERS')
            repo.git.commit(
                '-m', f"Add {vendor_type} {vendor_name} {chart_name} OWNERS file")
            repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
                          f'HEAD:refs/heads/{base_branch}', '-f')

            # Push chart files to test_repo:pr_branch
            repo.git.add(f'{chart_dir}/{chart_version}')
            repo.git.commit(
                '-m', f"Add {vendor_type} {vendor_name} {chart_name} {chart_version} chart files")
            repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
                          f'HEAD:refs/heads/{pr_branch}', '-f')

            # Create PR from test_repo:pr_branch to test_repo:base_branch
            actions_bot_name = 'github-actions[bot]'
            if secrets.bot_name == actions_bot_name:
                head = pr_branch
            else:
                head = f'{secrets.bot_name}:{pr_branch}'
            data = {'head': head, 'base': base_branch,
                    'title': pr_branch}

            logger.info(
                f"Create PR with chart files from '{secrets.test_repo}:{pr_branch}' to '{secrets.test_repo}:{base_branch}'")
            r = github_api(
                'post', f'repos/{secrets.test_repo}/pulls', secrets.bot_token, json=data)
            j = json.loads(r.text)
            pr_number_list.append(
                (vendor_type, vendor_name, chart_name, chart_version, j['number']))

        os.chdir(old_cwd)
        for vendor_type, vendor_name, chart_name, chart_version, pr_number in pr_number_list:
            base_branch = f'{secrets.pr_base_branch}-{vendor_type}-{vendor_name}-{chart_name}-{chart_version}'
            # Check PRs are merged
            chart = f'{vendor_type} {vendor_name} {chart_name} {chart_version}'
            run_id = get_run_id(secrets, pr_number)
            conclusion = get_run_result(secrets, run_id)

            # Send notification to owner through GitHub issues
            r = github_api(
                'get', f'repos/{secrets.test_repo}/actions/runs/{run_id}', secrets.bot_token)
            run = r.json()
            run_html_url = run['html_url']
            chart_dir = f'charts/{vendor_type}/{vendor_name}/{chart_name}'
            chart_owners = owners_table[chart_dir]
            pass_verification = conclusion == 'success'
            os.environ['GITHUB_ORGANIZATION'] = PROD_REPO.split('/')[0]
            os.environ['GITHUB_REPO'] = PROD_REPO.split('/')[1]
            os.environ['GITHUB_AUTH_TOKEN'] = secrets.bot_token
            logger.info(
                f"Send notification to '{chart_owners}' about verification result of '{chart}'")
            create_verification_issue(chart_name, chart_owners, run_html_url, secrets.software_name,
                                      secrets.software_version, pass_verification, secrets.bot_token)

            if conclusion == 'success':
                logger.info(f"Workflow run for {chart} was 'success'")
            else:
                logger.warning(
                    f"Workflow for the submitted PR did not success, run id: {run_id}, chart: {chart}")
                continue

            r = github_api(
                'get', f'repos/{secrets.test_repo}/pulls/{pr_number}/merge', secrets.bot_token)
            if r.status_code == 204:
                logger.info(f"PR for {chart} merged sucessfully")
            else:
                logger.warning(
                    f"Workflow for submitted PR success but PR not merged, chart: {chart}")
                continue

            # Check index.yaml is updated
            repo = git.Repo(os.getcwd())
            old_branch = repo.active_branch.name
            repo.git.fetch(f'https://github.com/{secrets.test_repo}.git',
                           '{0}:{0}'.format(f'{base_branch}-gh-pages'), '-f')
            repo.git.checkout(f'{base_branch}-gh-pages')
            with open('index.yaml', 'r') as fd:
                try:
                    index = yaml.safe_load(fd)
                except yaml.YAMLError as err:
                    logger.warning(
                        f"error parsing index.yaml of {chart}: {err}")
                    continue

            entry = vendor_name + '-' + chart_name
            if entry not in index['entries']:
                logger.warning(
                    f"{chart} not added to index")
                continue

            version_list = [release['version']
                            for release in index['entries'][entry]]
            if chart_version not in version_list:
                logger.warning(
                    f"{chart} not added to index")
                continue

            logger.info(
                f"Index updated correctly for {chart}, cleaning up local branch")
            repo.git.checkout(old_branch)
            repo.git.branch('-D', f'{base_branch}-gh-pages')

            # Check release is published
            expected_tag = f'{vendor_name}-{chart_name}-{chart_version}'
            try:
                release = get_release_by_tag(secrets, expected_tag)

                logger.info(f"Released '{expected_tag}' successfully")
                chart_tar = f'{chart_name}-{chart_version}.tgz'
                expected_chart_asset = f'{vendor_name}-{chart_tar}'
                logger.info(
                    f"Check '{expected_chart_asset}' is in release assets")
                release_id = release['id']
                r = github_api(
                    'get', f'repos/{secrets.test_repo}/releases/{release_id}/assets', secrets.bot_token)
                asset_list = json.loads(r.text)
                asset_names = [asset['name'] for asset in asset_list]

                logger.info(f"Delete release '{expected_tag}'")
                github_api(
                    'delete', f'repos/{secrets.test_repo}/releases/{release_id}', secrets.bot_token)

                logger.info(f"Delete release tag '{expected_tag}'")
                github_api(
                    'delete', f'repos/{secrets.test_repo}/git/refs/tags/{expected_tag}', secrets.bot_token)

                if expected_chart_asset not in asset_names:
                    logger.warning(
                        f"Missing release asset: {expected_chart_asset}")
            except:
                logger.warning(f"'{expected_tag}' not in the release list")


@then("all results are reported back to the caller")
def all_results_report_back_to_caller():
    """all results are reported back to the caller."""
