# -*- coding: utf-8 -*-
"""Chart tgz only submission

Partners or redhat associates can publish their chart by submitting
error-free chart in tgz format without the report.
"""
import os
import tempfile
import json
import base64
import pathlib
import logging
import shutil
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

from functional.utils import get_name_and_version_from_chart_tar, github_api, get_run_id, get_run_result

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture
def secrets():
    @dataclass
    class Secret:
        test_repo: str
        fork_repo: str
        cluster_token: str
        bot_token: str
        bot_name: str
        pr_base_branch: str
        fork_branch: str

        pr_number: int = -1
        vendor_type: str = ''
        vendor: str = ''
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
        chart_name, chart_version = get_name_and_version_from_chart_tar(
            test_chart)

    test_repo = os.environ.get("TEST_REPO")
    if not test_repo:
        raise Exception("TEST_REPO environment variable not defined")
    fork_repo = os.environ.get("FORK_REPO")
    if not fork_repo:
        raise Exception("FORK_REPO environment variable not defined")
    bot_name = fork_repo.split("/")[0]
    cluster_token = os.environ.get("CLUSTER_TOKEN")
    if not cluster_token:
        raise Exception("CLUSTER_TOKEN environment variable not defined")
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        bot_name = "github-actions[bot]"
        bot_token = os.environ.get("GITHUB_TOKEN")
        if not bot_token:
            raise Exception("BOT_TOKEN environment variable not defined")

    pr_base_branch = 'test-charts'
    fork_branch = pr_base_branch + '-pr'
    test_repo = str(base64.b64decode(test_repo), encoding="utf-8")
    fork_repo = str(base64.b64decode(fork_repo), encoding="utf-8")
    yield Secret(test_repo, fork_repo, cluster_token, bot_token, bot_name, pr_base_branch, fork_branch)

    # Teardown step to cleanup branches
    logger.info(f"Delete '{test_repo}:{pr_base_branch}-gh-pages'")
    github_api(
        'delete', f'https://api.github.com/repos/{test_repo}/git/refs/heads/{pr_base_branch}-gh-pages', bot_token)
    logger.info(f"Delete '{fork_repo}:{fork_branch}'")
    github_api(
        'delete', f'https://api.github.com/repos/{fork_repo}/git/refs/heads/{fork_branch}', bot_token)


@scenario('features/chart_tar_without_report.feature', "The partner hashicorp submits a error-free chart tgz for vault")
def test_partner_chart_tgz_submission():
    """The partner hashicorp submits a error-free chart tgz for vault."""


@scenario('features/chart_tar_without_report.feature', "A redhat associate submits a error-free chart tgz for vault")
def test_redhat_chart_tgz_submission():
    """A redhat associate submits a error-free chart tgz for vault."""


@given("hashicorp is a valid partner")
def hashicorp_is_a_valid_partner(secrets):
    """hashicorp is a valid partner"""
    secrets.vendor_type = 'partners'
    secrets.vendor = 'hashicorp'


@given("a redhat associate has a valid identity")
def redhat_associate_is_valid(secrets):
    """a redhat associate has a valid identity"""
    secrets.vendor_type = 'redhat'
    secrets.vendor = 'redhat'


@given("hashicorp has created an error-free chart tgz for vault")
@given("the redhat associate has created an error-free chart tgz for vault")
def the_user_has_created_a_error_free_chart_tgz(secrets):
    """The user has created an error-free chart tgz."""

    repo = git.Repo(os.getcwd())
    if os.environ.get('WORKFLOW_DEVELOPMENT'):
        logger.info("Wokflow development enabled")
        repo.git.add(A=True)
        repo.git.commit('-m', 'Checkpoint')

    # Get SHA from 'dev-gh-pages' branch
    logger.info(
        f"Create '{secrets.test_repo}:{secrets.pr_base_branch}-gh-pages' from '{secrets.test_repo}:dev-gh-pages'")
    r = github_api(
        'get', f'https://api.github.com/repos/{secrets.test_repo}/git/ref/heads/dev-gh-pages', secrets.bot_token)
    j = json.loads(r.text)
    sha = j['object']['sha']

    # Create a new gh-pages branch for testing
    data = {'ref': f'refs/heads/{secrets.pr_base_branch}-gh-pages', 'sha': sha}
    r = github_api(
        'post', f'https://api.github.com/repos/{secrets.test_repo}/git/refs', secrets.bot_token, json=data)

    # Make PR's from a temporary directory
    old_cwd = os.getcwd()
    dr = tempfile.mkdtemp(prefix='tci-')
    logger.info(f'Worktree directory: {dr}')
    repo.git.worktree('add', '--detach', dr, f'HEAD')

    os.chdir(dr)
    repo = git.Repo(dr)
    chart_dir = f'charts/{secrets.vendor_type}/{secrets.vendor}/{secrets.chart_name}'
    pathlib.Path(
        f'{chart_dir}/{secrets.chart_version}').mkdir(parents=True, exist_ok=True)

    # Create the OWNERS file from the string template
    values = {'bot_name': secrets.bot_name,
              'vendor': secrets.vendor, 'chart_name': secrets.chart_name}
    content = Template(secrets.owners_file_content).substitute(values)
    with open(f'{chart_dir}/OWNERS', 'w') as fd:
        fd.write(content)

    # Push OWNERS file to the test_repo
    logger.info(
        f"Push OWNERS file to '{secrets.test_repo}:{secrets.pr_base_branch}'")
    repo.git.add('charts')
    repo.git.commit(
        '-m', f"Add {secrets.vendor} {secrets.chart_name} OWNERS file")
    repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
                  f'HEAD:refs/heads/{secrets.pr_base_branch}', '-f')

    # Copy the chart tgz into temporary directory for PR submission
    chart_tgz = secrets.test_chart.split('/')[-1]
    shutil.copyfile(f'{old_cwd}/{secrets.test_chart}',
                    f'{chart_dir}/{secrets.chart_version}/{chart_tgz}')

    # Push chart tgz file to fork_repo:fork_branch
    repo.git.add('charts')
    repo.git.commit(
        '-m', f"Add {secrets.vendor} {secrets.chart_name} {secrets.chart_version} chart tgz file")

    repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.fork_repo}',
                  f'HEAD:refs/heads/{secrets.fork_branch}', '-f')

    os.chdir(old_cwd)


@when("hashicorp sends a pull request with the vault tgz chart")
@when("the redhat associate sends a pull request with the vault tgz chart")
def the_user_sends_the_pull_request_with_the_chart_tgz(secrets):
    """The user sends the pull request with the chart tgz file."""

    actions_bot_name = 'github-actions[bot]'
    if secrets.bot_name == actions_bot_name:
        head = secrets.fork_branch
    else:
        head = f'{secrets.bot_name}:{secrets.fork_branch}'
    data = {'head': head, 'base': secrets.pr_base_branch,
            'title': secrets.fork_branch}

    logger.info(
        f"Create PR with chart tgz file from '{secrets.fork_repo}:{secrets.fork_branch}'")
    r = github_api(
        'post', f'https://api.github.com/repos/{secrets.test_repo}/pulls', secrets.bot_token, json=data)
    j = json.loads(r.text)
    secrets.pr_number = j['number']


@then("hashicorp sees the pull request is merged")
@then("the redhat associate sees the pull request is merged")
def the_user_should_see_the_pull_request_getting_merged(secrets):
    """The user should see the pull request getting merged."""

    run_id = get_run_id(secrets)
    conclusion = get_run_result(secrets, run_id)
    if conclusion == 'success':
        logger.info("Workflow run was 'success'")
    else:
        pytest.fail(
            f"Workflow for the submitted PR did not success, run id: {run_id}")

    r = github_api(
        'get', f'https://api.github.com/repos/{secrets.test_repo}/pulls/{secrets.pr_number}/merge', secrets.bot_token)
    if r.status_code == 204:
        logger.info("PR merged sucessfully")
    else:
        pytest.fail("Workflow for submitted PR success but PR not merged")


@then("the index.yaml file is updated with an entry for the submitted chart")
def the_index_yaml_is_updated_with_a_new_entry(secrets):
    """The index.yaml file is updated with a new entry."""

    repo = git.Repo(os.getcwd())
    old_branch = repo.active_branch.name
    repo.git.fetch(f'https://github.com/{secrets.test_repo}.git',
                   '{0}:{0}'.format(f'{secrets.pr_base_branch}-gh-pages'), '-f')
    repo.git.checkout(f'{secrets.pr_base_branch}-gh-pages')
    with open('index.yaml', 'r') as fd:
        try:
            index = yaml.safe_load(fd)
        except yaml.YAMLError as err:
            pytest.fail(f"error parsing index.yaml: {err}")

    entry = secrets.vendor + '-' + secrets.chart_name
    if entry not in index['entries']:
        pytest.fail(
            f"{secrets.chart_name} {secrets.chart_version} not added to index")

    version_list = [release['version'] for release in index['entries'][entry]]
    if secrets.chart_version not in version_list:
        pytest.fail(
            f"{secrets.chart_name} {secrets.chart_version} not added to index")

    logger.info("Index updated correctly, cleaning up local branch")
    repo.git.checkout(old_branch)
    repo.git.branch('-D', f'{secrets.pr_base_branch}-gh-pages')


@then("a release for the vault chart is published with corresponding report and chart tarball")
def the_release_is_published(secrets):
    """a release is published with the chart"""

    r = github_api(
        'get', f'https://api.github.com/repos/{secrets.test_repo}/releases', secrets.bot_token)
    j = json.loads(r.text)

    for release in j:
        expected_tag = f'{secrets.vendor}-{secrets.chart_name}-{secrets.chart_version}'
        if release['tag_name'] == expected_tag:
            logger.info(f"Released '{expected_tag}' successfully")

            chart_tgz = secrets.test_chart.split('/')[-1]
            expected_chart_asset = f'{secrets.vendor}-{chart_tgz}'
            logger.info(f"Check '{expected_chart_asset}' is in release assets")
            release_id = release['id']
            r = github_api(
                'get', f'https://api.github.com/repos/{secrets.test_repo}/releases/{release_id}/assets', secrets.bot_token)
            asset_list = json.loads(r.text)
            asset_names = [asset['name'] for asset in asset_list]
            if expected_chart_asset not in asset_names:
                pytest.fail(f"Missing release asset: {expected_chart_asset}")

            expected_report_asset = 'report.yaml'
            logger.info(
                f"Check '{expected_report_asset}' is in release assets")
            if expected_report_asset not in asset_names:
                pytest.fail(f"Missing release asset: {expected_report_asset}")

            logger.info(f"Delete release '{expected_tag}'")
            r = github_api(
                'delete', f'https://api.github.com/repos/{secrets.test_repo}/releases/{release_id}', secrets.bot_token)
            if r.status_code != 204:
                pytest.fail(f"Unable to delete the release '{expected_tag}'")

            logger.info(f"Delete release tag '{expected_tag}'")
            r = github_api(
                'delete', f'https://api.github.com/repos/{secrets.test_repo}/git/refs/tags/{expected_tag}', secrets.bot_token)
            if r.status_code != 204:
                pytest.fail(
                    f"Unable to delete the release tag '{expected_tag}'")
            return
    else:
        pytest.fail(f"'{expected_tag}' not in the release list")
