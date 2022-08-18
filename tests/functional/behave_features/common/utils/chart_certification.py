# -*- coding: utf-8 -*-
"""Utility class for setting up and manipulating certification workflow tests."""

import os
import json
import pathlib
import shutil
import logging
import time
import uuid
from tempfile import TemporaryDirectory
from dataclasses import dataclass
from string import Template
from pathlib import Path

import git
import yaml

from common.utils.notifier import *
from common.utils.index import *
from common.utils.github import *
from common.utils.secret import *
from common.utils.set_directory import SetDirectory
from common.utils.setttings import *
from common.utils.chart import *

@dataclass
class ChartCertificationE2ETest:
    owners_file_content: str = """\
chart:
  name: ${chart_name}
  shortDescription: Test chart for testing chart submission workflows.
publicPgpKey: null
providerDelivery: ${provider_delivery}
users:
- githubUsername: ${bot_name}
vendor:
  label: ${vendor}
  name: ${vendor}
"""
    secrets: E2ETestSecret = E2ETestSecret()

    old_cwd: str = os.getcwd()
    repo: git.Repo = git.Repo()
    temp_dir: TemporaryDirectory = None
    temp_repo: git.Repo = None
    github_actions: str = os.environ.get("GITHUB_ACTIONS")
    def set_git_username_email(self, repo, username, email):
        """
        Parameters:
        repo (git.Repo): git.Repo instance of the local directory
        username (str): git username to set
        email (str): git email to set
        """
        repo.config_writer().set_value("user", "name", username).release()
        repo.config_writer().set_value("user", "email", email).release()

    def get_bot_name_and_token(self):
        bot_name = os.environ.get("BOT_NAME")
        logging.debug(f"Enviroment variable value BOT_NAME: {bot_name}")
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_name and not bot_token:
            bot_name = "github-actions[bot]"
            bot_token = os.environ.get("GITHUB_TOKEN")
            if not bot_token:
                raise Exception("BOT_TOKEN environment variable not defined")
        elif not bot_name:
            raise Exception("BOT_TOKEN set but BOT_NAME not specified")
        elif not bot_token:
            raise Exception("BOT_NAME set but BOT_TOKEN not specified")
        return bot_name, bot_token

    def remove_chart(self, chart_directory, chart_version, remote_repo, base_branch, bot_token):
        # Remove chart files from base branch
        logging.info(
            f"Remove {chart_directory}/{chart_version} from {remote_repo}:{base_branch}")
        try:
            self.temp_repo.git.rm('-rf', '--cached', f'{chart_directory}/{chart_version}')
            self.temp_repo.git.commit(
                '-m', f'Remove {chart_directory}/{chart_version}')
            self.temp_repo.git.push(f'https://x-access-token:{bot_token}@github.com/{remote_repo}',
                            f'HEAD:refs/heads/{base_branch}')
        except git.exc.GitCommandError:
            logging.info(
                f"{chart_directory}/{chart_version} not exist on {remote_repo}:{base_branch}")

    def remove_owners_file(self, chart_directory, remote_repo, base_branch, bot_token):
        # Remove the OWNERS file from base branch
        logging.info(
            f"Remove {chart_directory}/OWNERS from {remote_repo}:{base_branch}")
        try:
            self.temp_repo.git.rm('-rf', '--cached', f'{chart_directory}/OWNERS')
            self.temp_repo.git.commit(
                '-m', f'Remove {chart_directory}/OWNERS')
            self.temp_repo.git.push(f'https://x-access-token:{bot_token}@github.com/{remote_repo}',
                            f'HEAD:refs/heads/{base_branch}')
        except git.exc.GitCommandError:
            logging.info(
                f"{chart_directory}/OWNERS not exist on {remote_repo}:{base_branch}")

    def create_test_gh_pages_branch(self, remote_repo, base_branch, bot_token):
        # Get SHA from 'dev-gh-pages' branch
        logging.info(
            f"Create '{remote_repo}:{base_branch}-gh-pages' from '{remote_repo}:dev-gh-pages'")
        r = github_api(
            'get', f'repos/{remote_repo}/git/ref/heads/dev-gh-pages', bot_token)
        j = json.loads(r.text)
        sha = j['object']['sha']

        # Create a new gh-pages branch for testing
        data = {'ref': f'refs/heads/{base_branch}-gh-pages', 'sha': sha}
        r = github_api(
            'post', f'repos/{remote_repo}/git/refs', bot_token, json=data)

        logging.info(f'gh-pages branch created: {base_branch}-gh-pages')

    def setup_git_context(self, repo: git.Repo):
        self.set_git_username_email(repo, self.secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
        if os.environ.get('WORKFLOW_DEVELOPMENT'):
            logging.info("Wokflow development enabled")
            repo.git.add(A=True)
            repo.git.commit('-m', 'Checkpoint')

    def send_pull_request(self, remote_repo, base_branch, pr_branch, bot_token):
        pr_body = os.environ.get('PR_BODY')
        data = {'head': pr_branch, 'base': base_branch,
                'title': base_branch, 'body': pr_body}
        logging.debug(f"PR_BODY Content: {pr_body}")
        logging.info(
            f"Create PR from '{remote_repo}:{pr_branch}'")
        r = github_api(
            'post', f'repos/{remote_repo}/pulls', bot_token, json=data)
        j = json.loads(r.text)
        if not 'number' in j:
            raise AssertionError(f"error sending pull request, response was: {r.text}")
        return j['number']

    def create_and_push_owners_file(self, chart_directory, base_branch, vendor_name, vendor_type, chart_name, provider_delivery=False):
        with SetDirectory(Path(self.temp_dir.name)):
            # Create the OWNERS file from the string template
            values = {'bot_name': self.secrets.bot_name,
                    'vendor': vendor_name, 'chart_name': chart_name,
                      "provider_delivery" : provider_delivery}
            content = Template(self.secrets.owners_file_content).substitute(values)
            logging.debug(f"OWNERS File Content: {content}")
            with open(f'{chart_directory}/OWNERS', 'w') as fd:
                fd.write(content)

            # Push OWNERS file to the test_repo
            logging.info(
                f"Push OWNERS file to '{self.secrets.test_repo}:{base_branch}'")
            self.temp_repo.git.add(f'{chart_directory}/OWNERS')
            self.temp_repo.git.commit(
                '-m', f"Add {vendor_type} {vendor_name} {chart_name} OWNERS file")
            self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                        f'HEAD:refs/heads/{base_branch}', '-f')

    def check_index_yaml(self,base_branch, vendor, chart_name, chart_version, index_file="index.yaml", check_provider_type=False, failure_type='error'):
        old_branch = self.repo.active_branch.name
        self.repo.git.fetch(f'https://github.com/{self.secrets.test_repo}.git',
                    '{0}:{0}'.format(f'{base_branch}-gh-pages'), '-f')

        self.repo.git.checkout(f'{base_branch}-gh-pages')

        with open(index_file, 'r') as fd:
            try:
                index = yaml.safe_load(fd)
            except yaml.YAMLError as err:
                if failure_type == 'error':
                    raise AssertionError(f"error parsing index.yaml: {err}")
                else:
                    logging.warning(f"error parsing index.yaml: {err}")
                    return False

        if index:
            entry = f"{vendor}-{chart_name}"
            if "entries" not in index or entry not in index['entries']:
                if failure_type == 'error':
                    raise AssertionError(f"{entry} not added in entries to {index_file} & Found index.yaml entries: {index['entries']}")
                else:
                    logging.warning(f"{chart_version} not added to {index_file}")
                    logging.warning(f"Index.yaml entry content: {index['entries'][entry]}")
                    return False

            version_list = [release['version'] for release in index['entries'][entry]]
            if chart_version not in version_list:
                raise AssertionError(f"{chart_version} not added to {index_file} & Found index.yaml entry content: {index['entries'][entry]}")

            #This check is applicable for charts submitted in redhat path when one of the chart-verifier check fails
            #Check whether providerType annotations is community in index.yaml when vendor_type is redhat
            if check_provider_type and self.secrets.vendor_type == 'redhat':
                provider_type_in_index_yaml = index['entries'][entry][0]['annotations']['charts.openshift.io/providerType']
                if provider_type_in_index_yaml != 'community':
                    if failure_type == 'error':
                        raise AssertionError(f"{provider_type_in_index_yaml} is not correct as providerType in index.yaml")
                    else:
                        logging.warning(f"{provider_type_in_index_yaml} is not correct as providerType in index.yaml")

            logging.info("Index updated correctly, cleaning up local branch")
            self.repo.git.checkout(old_branch)
            self.repo.git.branch('-D', f'{base_branch}-gh-pages')
            return True
        else:
            return False

    def check_release_result(self, vendor, chart_name, chart_version, chart_tgz, failure_type='error'):
        expected_tag = f'{vendor}-{chart_name}-{chart_version}'
        try:
            release = get_release_by_tag(self.secrets, expected_tag)
            logging.info(f"Released '{expected_tag}' successfully")

            expected_chart_asset = f'{vendor}-{chart_tgz}'
            required_assets = [expected_chart_asset]
            logging.info(f"Check '{required_assets}' is in release assets")
            release_id = release['id']
            get_release_assets(self.secrets, release_id, required_assets)
            return True
        except Exception as e:
            if failure_type == 'error':
                raise AssertionError(e)
            else:
                logging.warning(e)
                return False
        finally:
            logging.info(f"Delete release '{expected_tag}'")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/releases/{release_id}', self.secrets.bot_token)

            logging.info(f"Delete release tag '{expected_tag}'")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/git/refs/tags/{expected_tag}', self.secrets.bot_token)

    # expect_result: a string representation of expected result, e.g. 'success'
    def check_workflow_conclusion(self, pr_number, expect_result: str, failure_type='error'):
        try:
            # Check workflow conclusion
            run_id = get_run_id(self.secrets, pr_number)
            conclusion = get_run_result(self.secrets, run_id)
            if conclusion == expect_result:
                logging.info(f"PR{pr_number} Workflow run was '{expect_result}' which is expected")
            else:
                if failure_type == 'warning':
                    logging.warning(f"PR{pr_number if pr_number else self.secrets.pr_number} Workflow run was '{conclusion}' which is unexpected, run id: {run_id}")
                else:
                    raise AssertionError(
                        f"PR{pr_number if pr_number else self.secrets.pr_number} Workflow run was '{conclusion}' which is unexpected, run id: {run_id}")
                    
            return run_id, conclusion
        except Exception as e:
            if failure_type == 'error':
                raise AssertionError(e)
            else:
                logging.warning(e)
                return None, None

    # expect_merged: boolean representing whether the PR should be merged
    def check_pull_request_result(self, pr_number, expect_merged: bool, failure_type='error'):
        # Check if PR merged
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/pulls/{pr_number}/merge', self.secrets.bot_token)
        logging.info(f"PR{pr_number} result status_code : {r.status_code}")
        if r.status_code == 204 and expect_merged:
            logging.info(f"PR{pr_number} merged sucessfully as expected")
            return True
        elif r.status_code == 404 and not expect_merged:
            logging.info(f"PR{pr_number} not merged, which is expected")
            return True
        elif r.status_code == 204 and not expect_merged:
            if failure_type == 'error':
                raise AssertionError(f"PR{pr_number} Expecting not merged but PR was merged")
            else:
                logging.warning(f"PR{pr_number} Expecting not merged but PR was merged")
                return False
        elif r.status_code == 404 and expect_merged:
            if failure_type == 'error':
                raise AssertionError(f"PR{pr_number} Expecting PR merged but PR was not merged")
            else:
                logging.warning(f"PR{pr_number} Expecting PR merged but PR was not merged")
                return False
        else:
            if failure_type == 'error':
                raise AssertionError(f"PR{pr_number} Got unexpected status code from PR: {r.status_code}")
            else:
                logging.warning(f"PR{pr_number} Got unexpected status code from PR: {r.status_code}")
                return False

    def cleanup_release(self, expected_tag):
        """Cleanup the release and release tag.

        Releases might be left behind if check_index_yam() ran before check_release_result() and fails the test.
        """
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/releases', self.secrets.bot_token)
        releases = json.loads(r.text)
        logging.debug(f"List of releases: {releases}")
        for release in releases:
            if release['tag_name'] == expected_tag:
                release_id = release['id']
                logging.info(f"Delete release '{expected_tag}'")
                github_api(
                    'delete', f'repos/{self.secrets.test_repo}/releases/{release_id}', self.secrets.bot_token)

                logging.info(f"Delete release tag '{expected_tag}'")
                github_api(
                    'delete', f'repos/{self.secrets.test_repo}/git/refs/tags/{expected_tag}', self.secrets.bot_token)
    
    def check_pull_request_labels(self, pr_number):
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/issues/{pr_number}/labels', self.secrets.bot_token)
        labels = json.loads(r.text)
        authorized_request = False
        content_ok = False
        for label in labels:
            logging.info(f"PR{pr_number} found label {label['name']}")
            if label['name'] == "authorized-request":
                authorized_request = True
            if label['name'] == "content-ok":
                content_ok = True
        
        if authorized_request and content_ok:
            logging.info(f"PR{pr_number} authorized request and content-ok labels were found as expected")
            return True
        else:
            raise AssertionError(f"PR{pr_number} authorized request and/or content-ok labels were not found as expected")

@dataclass
class ChartCertificationE2ETestSingle(ChartCertificationE2ETest):
    test_name: str = '' # Meaningful test name for this test, displayed in PR title
    test_chart: str = ''
    test_report: str = ''
    chart_directory: str = ''
    secrets: E2ETestSecretOneShot = E2ETestSecretOneShot()

    def __post_init__(self) -> None:
        # unique string based on uuid.uuid4(), not using timestamp here because even
        # in nanoseconds there are chances of collisions among first test cases of
        # different processes.
        self.uuid = uuid.uuid4().hex

        bot_name, bot_token = self.get_bot_name_and_token()
        test_repo = TEST_REPO

        #Storing current branch to checkout after scenario execution
        if os.environ.get('LOCAL_RUN'):
            self.secrets.active_branch = self.repo.active_branch.name
            logging.debug(f"Active branch name : {self.secrets.active_branch}")

        # Create a new branch locally from detached HEAD
        head_sha = self.repo.git.rev_parse('--short', 'HEAD')
        unique_branch = f'{head_sha}-{self.uuid}'
        logging.debug(f"Unique branch name : {unique_branch}")
        local_branches = [h.name for h in self.repo.heads]
        logging.debug(f"Local branch names : {local_branches}")
        if unique_branch not in local_branches:
            self.repo.git.checkout('-b', f'{unique_branch}')

        current_branch = self.repo.active_branch.name
        logging.debug(f"Current active branch name : {current_branch}")
        
        r = github_api(
            'get', f'repos/{test_repo}/branches', bot_token)
        branches = json.loads(r.text)
        branch_names = [branch['name'] for branch in branches]
        logging.debug(f"Remote test repo branch names : {branch_names}")
        if current_branch not in branch_names:
            logging.info(
                f"{test_repo}:{current_branch} does not exists, creating with local branch")
        self.repo.git.push(f'https://x-access-token:{bot_token}@github.com/{test_repo}',
                    f'HEAD:refs/heads/{current_branch}', '-f')

        pretty_test_name = self.test_name.strip().lower().replace(' ', '-')
        base_branch = f'{self.uuid}-{pretty_test_name}-{current_branch}' if pretty_test_name else f'{self.uuid}-test-{current_branch}'
        logging.debug(f"Base branch name : {base_branch}")
        pr_branch = base_branch + '-pr-branch'

        self.secrets.owners_file_content = self.owners_file_content
        self.secrets.test_repo = test_repo
        self.secrets.bot_name = bot_name
        self.secrets.bot_token = bot_token
        self.secrets.base_branch = base_branch
        self.secrets.pr_branch = pr_branch
        self.secrets.index_file = "index.yaml"
        self.secrets.provider_delivery = False


    def cleanup (self):
        # Cleanup releases and release tags
        self.cleanup_release()
        # Teardown step to cleanup branches
        if self.temp_dir is not None:
            self.temp_dir.cleanup()
        self.repo.git.worktree('prune')

        head_sha = self.repo.git.rev_parse('--short', 'HEAD')
        current_branch = f'{head_sha}-{self.uuid}'
        logging.info(f"Delete remote '{current_branch}' branch")
        github_api(
            'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{current_branch}', self.secrets.bot_token)

        logging.info(f"Delete '{self.secrets.test_repo}:{self.secrets.base_branch}'")
        github_api(
            'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{self.secrets.base_branch}', self.secrets.bot_token)

        logging.info(f"Delete '{self.secrets.test_repo}:{self.secrets.base_branch}-gh-pages'")
        github_api(
            'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{self.secrets.base_branch}-gh-pages', self.secrets.bot_token)

        logging.info(f"Delete '{self.secrets.test_repo}:{self.secrets.pr_branch}'")
        github_api(
            'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{self.secrets.pr_branch}', self.secrets.bot_token)

        logging.info(f"Delete local '{self.secrets.base_branch}'")
        try:
            self.repo.git.branch('-D', self.secrets.base_branch)
        except git.exc.GitCommandError:
            logging.info(f"Local '{self.secrets.base_branch}' does not exist")

        logging.info(f"Delete local '{current_branch}'")
        try:
            if os.environ.get('LOCAL_RUN'):
                self.repo.git.checkout(f'{self.secrets.active_branch}')
            self.repo.git.branch('-D', current_branch)
        except git.exc.GitCommandError:
            logging.info(f"Local '{current_branch}' does not exist")
    
    def update_bot_name(self, bot_name):
        logging.debug(f"Updating bot name: {bot_name}")
        self.secrets.bot_name = bot_name
    
    def update_bad_version(self, bad_version):
        logging.debug(f"Updating bad version: {bad_version}")
        self.secrets.bad_version = bad_version

    def update_chart_directory(self):
        base_branch_without_uuid = "-".join(self.secrets.base_branch.split("-")[:-1])
        vendor_without_suffix = self.secrets.vendor.split("-")[0]
        self.secrets.base_branch = f'{base_branch_without_uuid}-{self.secrets.vendor_type}-{vendor_without_suffix}-{self.secrets.chart_name}-{self.secrets.chart_version}'
        self.secrets.pr_branch = f'{self.secrets.base_branch}-pr-branch'
        self.chart_directory = f'charts/{self.secrets.vendor_type}/{self.secrets.vendor}/{self.secrets.chart_name}'
        logging.debug(f"Updating chart_directory: {self.chart_directory}")

    def update_test_chart(self, test_chart):
        logging.debug(f"Updating test chart: {test_chart}")
        self.test_chart = test_chart
        chart_name, chart_version = self.get_chart_name_version()
        logging.debug(f"Got chart_name: {chart_name} and chart_version: {chart_version} from the chart")
        self.secrets.test_chart = self.test_chart
        self.secrets.chart_name = chart_name
        self.secrets.chart_version = chart_version
        self.update_chart_directory()

    def update_test_report(self, test_report):
        logging.debug(f"Updating test report: {test_report}")
        self.test_report = test_report
        chart_name, chart_version = self.get_chart_name_version()
        logging.debug(f"Got chart_name: {chart_name} and chart_version: {chart_version} from the report")
        self.secrets.test_report = self.test_report
        self.secrets.chart_name = chart_name
        self.secrets.chart_version = chart_version
        self.update_chart_directory()

    def get_unique_vendor(self, vendor):
        """Set unique vendor name.
        Note that release tag is generated with this vendor name.
        """
        # unique string based on uuid.uuid4()
        suffix = self.uuid
        if "PR_NUMBER" in os.environ:
            pr_num = os.environ["PR_NUMBER"]
            suffix = f"{suffix}-{pr_num}"
        return f"{vendor}-{suffix}"

    def get_chart_name_version(self):
        if not self.test_report and not self.test_chart:
            raise AssertionError("Provide at least one of test report or test chart.")
        if self.test_report:
            chart_name, chart_version = get_name_and_version_from_report(self.test_report)
        else:
            chart_name, chart_version = get_name_and_version_from_chart_tar(self.test_chart)
        return chart_name, chart_version

    def set_vendor(self, vendor, vendor_type):
        # use unique vendor id to avoid collision between tests
        logging.debug(f"Setting vendor: {vendor} vendor_type: {vendor_type}")
        self.secrets.vendor = self.get_unique_vendor(vendor)
        logging.debug(f"Unique vendor value: {self.secrets.vendor}")
        self.secrets.vendor_type = vendor_type

    def setup_git_context(self):
        super().setup_git_context(self.repo)

    def setup_gh_pages_branch(self):
        self.create_test_gh_pages_branch(self.secrets.test_repo, self.secrets.base_branch, self.secrets.bot_token)

    def setup_temp_dir(self):
        self.temp_dir = TemporaryDirectory(prefix='tci-')
        with SetDirectory(Path(self.temp_dir.name)):
            # Make PR's from a temporary directory
            logging.info(f'Worktree directory: {self.temp_dir.name}')
            self.repo.git.worktree('add', '--detach', self.temp_dir.name, f'HEAD')
            self.temp_repo = git.Repo(self.temp_dir.name)

            self.set_git_username_email(self.temp_repo, self.secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
            self.temp_repo.git.checkout('-b', self.secrets.base_branch)
            pathlib.Path(
                f'{self.chart_directory}/{self.secrets.chart_version}').mkdir(parents=True, exist_ok=True)

            self.remove_chart(self.chart_directory, self.secrets.chart_version, self.secrets.test_repo, self.secrets.base_branch, self.secrets.bot_token)
            self.remove_owners_file(self.chart_directory, self.secrets.test_repo, self.secrets.base_branch, self.secrets.bot_token)

    def update_chart_version_in_chart_yaml(self, new_version):
        with SetDirectory(Path(self.temp_dir.name)):
            path = f'{self.chart_directory}/{self.secrets.chart_version}/src/Chart.yaml'
            with open(path, 'r') as fd:
                try:
                    chart = yaml.safe_load(fd)
                except yaml.YAMLError as err:
                    raise AssertionError(f"error parsing '{path}': {err}")
            current_version = chart['version']

            if current_version != new_version:
                chart['version'] = new_version
                try:
                    with open(path, 'w') as fd:
                        fd.write(yaml.dump(chart))
                except Exception as e:
                    raise AssertionError("Failed to update version in yaml file")
    
    def remove_readme_file(self):
        with SetDirectory(Path(self.temp_dir.name)):
            path = f'{self.chart_directory}/{self.secrets.chart_version}/src/README.md'
            try:
                os.remove(path)
            except Exception as e:
                raise AssertionError(f"Failed to remove readme file : {e}")

    def process_owners_file(self):
        super().create_and_push_owners_file(self.chart_directory, self.secrets.base_branch, self.secrets.vendor, self.secrets.vendor_type, self.secrets.chart_name,self.secrets.provider_delivery)

    def process_chart(self, is_tarball: bool):
        with SetDirectory(Path(self.temp_dir.name)):
            if is_tarball:
                # Copy the chart tar into temporary directory for PR submission
                chart_tar = self.secrets.test_chart.split('/')[-1]
                shutil.copyfile(f'{self.old_cwd}/{self.secrets.test_chart}',
                                f'{self.chart_directory}/{self.secrets.chart_version}/{chart_tar}')
            else:
                # Unzip files into temporary directory for PR submission
                extract_chart_tgz(self.secrets.test_chart, f'{self.chart_directory}/{self.secrets.chart_version}', self.secrets, logging)


    def process_report(self, update_chart_sha=False, update_url=False, url=None,
                       update_versions=False,supported_versions=None,tested_version=None,kube_version=None,
                       update_provider_delivery=False, provider_delivery=False, missing_check=None,unset_package_digest=False):

        with SetDirectory(Path(self.temp_dir.name)):
            # Copy report to temporary location and push to test_repo:pr_branch
            logging.info(
                f"Push report to '{self.secrets.test_repo}:{self.secrets.pr_branch}'")
            
            if self.secrets.test_report.endswith('json'):
                logging.debug("Report type is json")
                report_path = f'{self.chart_directory}/{self.secrets.chart_version}/' + self.secrets.test_report.split('/')[-1]
                with open(self.secrets.test_report, 'r') as fd:
                    try:
                        report = json.load(fd)
                    except Exception as e:
                        raise AssertionError("Failed to read json file")

                with open(report_path, 'w') as fd:
                    try:
                        fd.write(json.dumps(report, indent=4))
                    except Exception as e:
                        raise AssertionError("Failed to write report in json format")

            elif self.secrets.test_report.endswith('yaml'):
                logging.debug("Report type is yaml")
                tmpl = open(self.secrets.test_report).read()
                values = {'repository': self.secrets.test_repo,
                        'branch': self.secrets.base_branch}
                content = Template(tmpl).substitute(values)

                report_path = f'{self.chart_directory}/{self.secrets.chart_version}/' + self.secrets.test_report.split('/')[-1]

                try:
                    report = yaml.safe_load(content)
                except yaml.YAMLError as err:
                    raise AssertionError(f"error parsing '{report_path}': {err}")

                if self.secrets.vendor_type != "partners":
                    report["metadata"]["tool"]["profile"]["VendorType"] = self.secrets.vendor_type
                    logging.info(f'VendorType set to {report["metadata"]["tool"]["profile"]["VendorType"]} in report.yaml')

                if update_chart_sha or update_url or update_versions or update_provider_delivery or unset_package_digest:
                    #For updating the report.yaml, for chart sha mismatch scenario
                    if update_chart_sha:
                        new_sha_value = 'sha256:5b85ae00b9ca2e61b2d70a59f98fd72136453b1a185676b29d4eb862981c1xyz'
                        logging.info(f"Current SHA Value in report: {report['metadata']['tool']['digests']['chart']}")
                        report['metadata']['tool']['digests']['chart'] = new_sha_value
                        logging.info(f"Updated sha value in report: {new_sha_value}")

                    #For updating the report.yaml, for invalid_url sceanrio
                    if update_url:
                        logging.info(f"Current chart-uri in report: {report['metadata']['tool']['chart-uri']}")
                        report['metadata']['tool']['chart-uri'] = url
                        logging.info(f"Updated chart-uri value in report: {url}")

                    if update_versions:
                        report['metadata']['tool']['testedOpenShiftVersion'] = tested_version
                        report['metadata']['tool']['supportedOpenShiftVersions'] = supported_versions
                        report['metadata']['chart']['kubeversion'] = kube_version
                        logging.info(f"Updated testedOpenShiftVersion value in report: {tested_version}")
                        logging.info(f"Updated supportedOpenShiftVersions value in report: {supported_versions}")
                        logging.info(f"Updated kubeversion value in report: {kube_version}")

                    if update_provider_delivery:
                        report['metadata']['tool']['providerControlledDelivery'] = provider_delivery

                    if unset_package_digest:
                        del report['metadata']['tool']['digests']['package']

                with open(report_path, 'w') as fd:
                    try:
                        fd.write(yaml.dump(report))
                        logging.info("Report updated with new values")
                    except Exception as e:
                        raise AssertionError("Failed to update report yaml with new values")

                #For removing the check for missing check scenario
                if missing_check:
                    logging.info(f"Updating report with {missing_check}")
                    with open(report_path, 'r+') as fd:
                        report_content = yaml.safe_load(fd)
                        results = report_content["results"]
                        new_results = filter(lambda x: x['check'] != missing_check, results)
                        report_content["results"] = list(new_results)
                        fd.seek(0)
                        yaml.dump(report_content, fd)
                        fd.truncate()
            else:
                raise AssertionError("Unknown report type")

        self.temp_repo.git.add(report_path)
        self.temp_repo.git.commit(
                '-m', f"Add {self.secrets.vendor} {self.secrets.chart_name} {self.secrets.chart_version} report")
        self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                f'HEAD:refs/heads/{self.secrets.pr_branch}', '-f')

    def add_non_chart_related_file(self):
        with SetDirectory(Path(self.temp_dir.name)):
            path = f'{self.chart_directory}/Notes.txt'
            with open(path, 'w') as fd:
                fd.write("This is a test file")

    def push_chart(self, is_tarball: bool, add_non_chart_file=False):
        # Push chart to test_repo:pr_branch
        if is_tarball:
            chart_tar = self.secrets.test_chart.split('/')[-1]
            self.temp_repo.git.add(f'{self.chart_directory}/{self.secrets.chart_version}/{chart_tar}')
        else:
            if add_non_chart_file:
                self.temp_repo.git.add(f'{self.chart_directory}/')
            else:
                self.temp_repo.git.add(f'{self.chart_directory}/{self.secrets.chart_version}/src')
        self.temp_repo.git.commit(
            '-m', f"Add {self.secrets.vendor} {self.secrets.chart_name} {self.secrets.chart_version} chart")

        self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                      f'HEAD:refs/heads/{self.secrets.pr_branch}', '-f')

    def send_pull_request(self):
        self.secrets.pr_number = super().send_pull_request(self.secrets.test_repo, self.secrets.base_branch, self.secrets.pr_branch, self.secrets.bot_token)
        logging.info(f"[INFO] PR number: {self.secrets.pr_number}")

    # expect_result: a string representation of expected result, e.g. 'success'
    def check_workflow_conclusion(self, expect_result: str):
        # Check workflow conclusion
        super().check_workflow_conclusion(None, expect_result)

    # expect_merged: boolean representing whether the PR should be merged
    def check_pull_request_result(self, expect_merged: bool):
        super().check_pull_request_result(self.secrets.pr_number, expect_merged)

    def check_pull_request_labels(self):
        super().check_pull_request_labels(self.secrets.pr_number)

    def check_pull_request_comments(self, expect_message: str):
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/issues/{self.secrets.pr_number}/comments', self.secrets.bot_token)
        logging.info(f'STATUS_CODE: {r.status_code}')

        response = json.loads(r.text)
        logging.debug(f"CHECK PULL_REQUEST COMMENT RESPONSE: {response}")
        if len(response) == 0:
            raise AssertionError("No comment found in the PR")
        complete_comment = response[0]['body']

        if expect_message in complete_comment:
            logging.info("Found the expected comment in the PR")
        else:
            raise AssertionError(f"Was expecting '{expect_message}' in the comment {complete_comment}")

    def check_index_yaml(self, check_provider_type=False):
        super().check_index_yaml(self.secrets.base_branch, self.secrets.vendor, self.secrets.chart_name, self.secrets.chart_version, self.secrets.index_file,check_provider_type)

    def check_release_result(self):
        chart_tgz = self.secrets.test_chart.split('/')[-1]
        super().check_release_result(self.secrets.vendor, self.secrets.chart_name, self.secrets.chart_version, chart_tgz)

    def cleanup_release(self):
        expected_tag = f'{self.secrets.vendor}-{self.secrets.chart_name}-{self.secrets.chart_version}'
        super().cleanup_release(expected_tag)

@dataclass
class ChartCertificationE2ETestMultiple(ChartCertificationE2ETest):
    secrets: E2ETestSecretRecursive = E2ETestSecretRecursive()

    def __post_init__(self) -> None:
        bot_name, bot_token = self.get_bot_name_and_token()
        dry_run = self.get_dry_run()
        notify_id = self.get_notify_id()
        software_name, software_version = self.get_software_name_version()
        vendor_type = self.get_vendor_type()

        test_repo = TEST_REPO
        base_branches = []
        pr_branches = []

        pr_base_branch = self.repo.active_branch.name
        r = github_api(
            'get', f'repos/{test_repo}/branches', bot_token)
        branches = json.loads(r.text)
        branch_names = [branch['name'] for branch in branches]
        if pr_base_branch not in branch_names:
            logging.info(
                f"{test_repo}:{pr_base_branch} does not exists, creating with local branch")
        self.repo.git.push(f'https://x-access-token:{bot_token}@github.com/{test_repo}',
                    f'HEAD:refs/heads/{pr_base_branch}', '-f')

        self.secrets = E2ETestSecretRecursive()
        self.secrets.software_name = software_name
        self.secrets.software_version = software_version
        self.secrets.test_repo = test_repo
        self.secrets.bot_name = bot_name
        self.secrets.bot_token = bot_token
        self.secrets.vendor_type = vendor_type
        self.secrets.pr_base_branch = pr_base_branch
        self.secrets.base_branches = base_branches
        self.secrets.pr_branches = pr_branches
        self.secrets.dry_run = dry_run
        self.secrets.notify_id = notify_id
        self.secrets.owners_file_content = self.owners_file_content
        self.secrets.release_tags = list()

    def cleanup (self):
        # Teardown step to cleanup releases and branches
        for release_tag in self.secrets.release_tags:
            self.cleanup_release(release_tag)

        self.repo.git.worktree('prune')
        for base_branch in self.secrets.base_branches:
            logging.info(f"Delete '{self.secrets.test_repo}:{base_branch}'")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{base_branch}', self.secrets.bot_token)

            logging.info(f"Delete '{self.secrets.test_repo}:{base_branch}-gh-pages'")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{base_branch}-gh-pages', self.secrets.bot_token)

            logging.info(f"Delete local '{base_branch}'")
            try:
                self.repo.git.branch('-D', base_branch)
            except git.exc.GitCommandError:
                logging.info(f"Local '{base_branch}' does not exist")

        for pr_branch in self.secrets.pr_branches:
            logging.info(f"Delete '{self.secrets.test_repo}:{pr_branch}'")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{pr_branch}', self.secrets.bot_token)

        try:
            logging.info("Delete local 'tmp' branch")
            self.temp_repo.git.branch('-D', 'tmp')
        except git.exc.GitCommandError:
            logging.info(f"Local 'tmp' branch does not exist")

    def get_dry_run(self):
        # Accepts 'true' or 'false', depending on whether we want to notify
        # Don't notify on dry runs, default to True
        dry_run = False if os.environ.get("DRY_RUN") == 'false' else True
        # Don't notify if not triggerd on PROD_REPO and PROD_BRANCH
        if not dry_run:
            triggered_branch = os.environ.get("GITHUB_REF").split('/')[-1]
            triggered_repo = os.environ.get("GITHUB_REPOSITORY")
            if triggered_repo != PROD_REPO or triggered_branch != PROD_BRANCH:
                dry_run = True
        return dry_run

    def get_notify_id(self):
        # Accepts comma separated Github IDs or empty strings to override people to tag in notifications
        notify_id = os.environ.get("NOTIFY_ID")
        if notify_id:
            notify_id = [vt.strip() for vt in notify_id.split(',')]
        else:
            notify_id = ["dperaza","mmulholla"]
        return notify_id

    def get_software_name_version(self):
        software_name = os.environ.get("SOFTWARE_NAME")
        if not software_name:
            raise Exception("SOFTWARE_NAME environment variable not defined")

        software_version = os.environ.get("SOFTWARE_VERSION").strip('\"')
        if not software_version:
            raise Exception("SOFTWARE_VERSION environment variable not defined")
        elif software_version.startswith("sha256"):
            software_version = software_version[-8:]

        return software_name, software_version

    def get_vendor_type(self):
        vendor_type = os.environ.get("VENDOR_TYPE")
        if not vendor_type:
            logging.info(
                f"VENDOR_TYPE environment variable not defined, default to `all`")
            vendor_type = 'all'
        return vendor_type

    def setup_temp_dir(self):
        self.temp_dir = TemporaryDirectory(prefix='tci-')
        with SetDirectory(Path(self.temp_dir.name)):
            # Make PR's from a temporary directory
            logging.info(f'Worktree directory: {self.temp_dir.name}')
            self.repo.git.worktree('add', '--detach', self.temp_dir.name, f'HEAD')
            self.temp_repo = git.Repo(self.temp_dir.name)

            # Run submission flow test with charts in PROD_REPO:PROD_BRANCH
            self.set_git_username_email(self.temp_repo, self.secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
            self.temp_repo.git.checkout(PROD_BRANCH, 'charts')
            self.temp_repo.git.restore('--staged', 'charts')
            self.secrets.submitted_charts = get_all_charts(
                'charts', self.secrets.vendor_type)
            logging.info(
                f"Found charts for {self.secrets.vendor_type}: {self.secrets.submitted_charts}")
            self.temp_repo.git.checkout('-b', 'tmp')

    def get_owner_ids(self, chart_directory, owners_table):

        with open(f'{chart_directory}/OWNERS', 'r') as fd:
            try:
                owners = yaml.safe_load(fd)
                # Pick owner ids for notification
                owners_table[chart_directory] = [
                    owner.get('githubUsername', '') for owner in owners['users']]
            except yaml.YAMLError as err:
                logging.warning(
                    f"Error parsing OWNERS of {chart_directory}: {err}")

    def push_chart(self, chart_directory, chart_name, chart_version, vendor_name, vendor_type, pr_branch):
        # Push chart files to test_repo:pr_branch
        self.temp_repo.git.add(f'{chart_directory}/{chart_version}')
        self.temp_repo.git.commit(
            '-m', f"Add {vendor_type} {vendor_name} {chart_name} {chart_version} chart files")
        self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                    f'HEAD:refs/heads/{pr_branch}', '-f')

    def report_failure(self,chart,chart_owners,failure_type,pr_html_url=None,run_html_url=None):

        os.environ['GITHUB_REPO'] = PROD_REPO.split('/')[1]
        os.environ['GITHUB_AUTH_TOKEN'] = self.secrets.bot_token
        if not self.secrets.dry_run:
            os.environ['GITHUB_REPO'] = PROD_REPO.split('/')[1]
            os.environ['GITHUB_AUTH_TOKEN'] = self.secrets.bot_token
            os.environ['GITHUB_ORGANIZATION'] = PROD_REPO.split('/')[0]
            logging.info(f"Send notification to '{self.secrets.notify_id}' about verification result of '{chart}'")
            create_verification_issue(chart,  chart_owners, failure_type,self.secrets.notify_id, pr_html_url, run_html_url, self.secrets.software_name,
                                      self.secrets.software_version, self.secrets.bot_token, self.secrets.dry_run)
        else:
            os.environ['GITHUB_ORGANIZATION'] = PROD_REPO.split('/')[0]
            os.environ['GITHUB_REPO'] = "sandbox"
            os.environ['GITHUB_AUTH_TOKEN'] = self.secrets.bot_token
            logging.info(f"Send notification to '{self.secrets.notify_id}' about dry run verification result of '{chart}'")
            create_verification_issue(chart, chart_owners, failure_type,self.secrets.notify_id, pr_html_url, run_html_url, self.secrets.software_name,
                                      self.secrets.software_version, self.secrets.bot_token, self.secrets.dry_run)
            logging.info(f"Dry Run - send sandbox notification to '{chart_owners}' about verification result of '{chart}'")


    def check_single_chart_result(self, vendor_type, vendor_name, chart_name, chart_version, pr_number, owners_table):
        base_branch = f'{self.secrets.software_name}-{self.secrets.software_version}-{self.secrets.pr_base_branch}-{vendor_type}-{vendor_name}-{chart_name}-{chart_version}'

        # Check workflow conclusion
        chart = f'{vendor_name} {chart_name} {chart_version}'
        run_id, conclusion = super().check_workflow_conclusion(pr_number, 'success', failure_type='warning')

        if conclusion and run_id:
            if conclusion != 'success':
                # Send notification to owner through GitHub issues
                r = github_api(
                    'get', f'repos/{self.secrets.test_repo}/actions/runs/{run_id}', self.secrets.bot_token)
                run = r.json()
                run_html_url = run['html_url']

                pr = get_pr(self.secrets,pr_number)
                pr_html_url = pr["html_url"]
                chart_directory = f'charts/{vendor_type}/{vendor_name}/{chart_name}'
                chart_owners = owners_table[chart_directory]

                self.report_failure(chart,chart_owners,CHECKS_FAILED,pr_html_url,run_html_url)

                logging.warning(f"PR{pr_number} workflow failed: {vendor_name}, {chart_name}, {chart_version}")
                return
            else:
                logging.info(f"PR{pr_number} workflow passed: {vendor_name}, {chart_name}, {chart_version}")
        else:
            logging.warning(f"PR{pr_number} workflow did not complete: {vendor_name}, {chart_name}, {chart_version}")
            return


        # Check PRs are merged
        if not super().check_pull_request_result(pr_number, True, failure_type='warning'):
            logging.warning(f"PR{pr_number} pull request was not merged: {vendor_name}, {chart_name}, {chart_version}")
            return
        logging.info(f"PR{pr_number} pull request was merged: {vendor_name}, {chart_name}, {chart_version}")

        # Check index.yaml is updated
        if not super().check_index_yaml(base_branch, vendor_name, chart_name, chart_version, check_provider_type=False, failure_type='warning'):
            logging.warning(f"PR{pr_number} - Chart was not found in Index file: {vendor_name}, {chart_name}, {chart_version}")
        logging.info(f"PR{pr_number} - Chart was found in Index file: {vendor_name}, {chart_name}, {chart_version}")

        # Check release is published
        chart_tgz = f'{chart_name}-{chart_version}.tgz'
        if not super().check_release_result(vendor_name, chart_name, chart_version, chart_tgz, failure_type='warning'):
            logging.warning(f"PR{pr_number} - Release was not created: {vendor_name}, {chart_name}, {chart_version}")
        logging.info(f"PR{pr_number} - Release was created: {vendor_name}, {chart_name}, {chart_version}")

    def process_single_chart(self, vendor_type, vendor_name, chart_name, chart_version, pr_number_list, owners_table):
        # Get SHA from 'pr_base_branch' branch
        logging.info(f"Process chart: {vendor_type}/{vendor_name}/{chart_name}/{chart_version}")
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/git/ref/heads/{self.secrets.pr_base_branch}', self.secrets.bot_token)
        j = json.loads(r.text)
        pr_base_branch_sha = j['object']['sha']

        chart_directory = f'charts/{vendor_type}/{vendor_name}/{chart_name}'
        base_branch = f'{self.secrets.software_name}-{self.secrets.software_version}-{self.secrets.pr_base_branch}-{vendor_type}-{vendor_name}-{chart_name}-{chart_version}'
        base_branch = base_branch.replace(":","-")
        pr_branch = f'{base_branch}-pr-branch'

        self.secrets.base_branches.append(base_branch)
        self.secrets.pr_branches.append(pr_branch)
        self.temp_repo.git.checkout('tmp')
        self.temp_repo.git.checkout('-b', base_branch)

        # Create test gh-pages branch for checking index.yaml
        self.create_test_gh_pages_branch(self.secrets.test_repo, base_branch, self.secrets.bot_token)

        # Create a new base branch for testing current chart
        logging.info(
            f"Create {self.secrets.test_repo}:{base_branch} for testing")
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/branches', self.secrets.bot_token)
        branches = json.loads(r.text)
        branch_names = [branch['name'] for branch in branches]
        if base_branch in branch_names:
            logging.warning(
                f"{self.secrets.test_repo}:{base_branch} already exists")
            return
        data = {'ref': f'refs/heads/{base_branch}',
                'sha': pr_base_branch_sha}
        r = github_api(
            'post', f'repos/{self.secrets.test_repo}/git/refs', self.secrets.bot_token, json=data)

        # Remove chart and owners file from git
        self.remove_chart(chart_directory, chart_version, self.secrets.test_repo, base_branch, self.secrets.bot_token)
        self.remove_owners_file(chart_directory, self.secrets.test_repo, base_branch, self.secrets.bot_token)

        # Get owners id for notifications
        self.get_owner_ids(chart_directory, owners_table)

        # Create and push test owners file
        super().create_and_push_owners_file(chart_directory, base_branch, vendor_name, vendor_type, chart_name)

        # Push test chart to pr_branch
        self.push_chart(chart_directory, chart_name, chart_version, vendor_name, vendor_type, pr_branch)

        # Create PR from pr_branch to base_branch
        logging.info("sleep for 5 seconds to avoid secondary api limit")
        time.sleep(5)
        pr_number = super().send_pull_request(self.secrets.test_repo, base_branch, pr_branch, self.secrets.bot_token)
        pr_number_list.append((vendor_type, vendor_name, chart_name, chart_version, pr_number))
        logging.info(f"PR{pr_number} created in {self.secrets.test_repo} into {base_branch} from {pr_branch}")

        # Record expected release tags
        self.secrets.release_tags.append(f'{vendor_name}-{chart_name}-{chart_version}')

    def process_all_charts(self):
        self.setup_git_context(self.repo)
        self.setup_temp_dir()

        owners_table = dict()
        pr_number_list = list()

        skip_charts = list()

        logging.info(f"Running tests for : {self.secrets.software_name} {self.secrets.software_version} :")
        # First look for charts in index.yaml to see if kubeVersion is good:
        if self.secrets.software_name == "OpenShift":
            logging.info("check index file for invalid kubeVersions")
            failed_charts = check_index_entries(self.secrets.software_version)
            if failed_charts:
                for chart in failed_charts:
                    providerDir = chart["providerType"].replace("partner","partners")
                    chart_directory = f'charts/{providerDir}/{chart["provider"]}/{chart["name"]}'
                    self.get_owner_ids(chart_directory,owners_table)
                    chart_owners = owners_table[chart_directory]
                    chart_id = f'{chart["provider"]} {chart["name"]} {chart["version"]}'
                    self.report_failure(chart_id,chart_owners,chart["message"],"","")
                    skip_charts.append(f'{chart["name"]}-{chart["version"]}')


        # Process test charts and send PRs from temporary directory
        with SetDirectory(Path(self.temp_dir.name)):
            for vendor_type, vendor_name, chart_name, chart_version in self.secrets.submitted_charts:
                if f'{chart_name}-{chart_version}' in skip_charts:
                    logging.info(f"Skip already failed chart: {vendor_type}, {vendor_name}, {chart_name}, {chart_version}")
                else:
                    logging.info(f"Process chart: {vendor_type}, {vendor_name}, {chart_name}, {chart_version}")
                    self.process_single_chart(vendor_type, vendor_name, chart_name, chart_version, pr_number_list, owners_table)
                    logging.info("sleep for 5 seconds  to avoid secondary api limit")
                    time.sleep(5)

        for vendor_type, vendor_name, chart_name, chart_version, pr_number in pr_number_list:
            logging.info(f"PR{pr_number} Check result: {vendor_type}, {vendor_name}, {chart_name}, {chart_version}")
            self.check_single_chart_result(vendor_type, vendor_name, chart_name, chart_version, pr_number, owners_table)


