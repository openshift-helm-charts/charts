# -*- coding: utf-8 -*-
"""Utility class for setting up and manipulating owner file submissions"""

import os
import logging
import pathlib
import uuid
import git
import json

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory
from string import Template
from pathlib import Path

from common.utils.workflow_repo_manager import WorkflowRepoManager
from common.utils.secret import E2ETestSecretOneShot
from common.utils.set_directory import SetDirectory
from common.utils.e2e_templates import base_owners_file
import common.utils.github as github
import common.utils.env as env
import common.utils.setttings as settings


@dataclass
class OwnersFileSubmissionsE2ETest:
    # Generated at initialization. Identifies each instance uniquely.
    # Used for PRs titles, branch names, etc.
    uuid: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)
    head_sha: str = ""
    # Meaningful test name for this test, displayed in PR title
    test_name: str = ""  
    secrets: E2ETestSecretOneShot = field(default_factory=lambda: E2ETestSecretOneShot(), init=False)
    old_cwd: str = os.getcwd()
    # This is the worktree for this test run. To be used for context management where applicable.
    temp_dir: TemporaryDirectory = None
    # Whether this is being executed in GitHub Actions.
    github_actions: str = os.environ.get("GITHUB_ACTIONS")
    # The name of the chart as supplied by the user.
    chart_base_name = ""
    # The name of the chart as supplied by the user appended with a unique identifier.
    chart_name = ""
    # The vendor name, e.g. 'redhat'
    vendor_label = ""
    # The vendor category, e.g. 'partners'
    vendor_category = ""
    # The vendor's pretty name, e.g. 'Red Hat'
    vendor_name = ""
    # The PR number in string format for this test run.
    pull_request: str = ""

    # Manages the local repository, branches, worktress, etc.
    # and facilitates pushes to remotes.
    repo_manager: WorkflowRepoManager = field(default_factory=lambda: WorkflowRepoManager(), init=False)

    # Combines this instance's unique ID + the repository base branch hash
    branch_base_id: str = None

    def __post_init__(self) -> None:
        """Generates identifiers for an instance to use."""
        logging.debug("RedHatOwnersFileSubmissionE2ETest --> __post_init__ called!")
        # Credentials and paths
        bot_name, bot_token = env.get_bot_name_and_token()
        test_repo = settings.TEST_REPO
        self.repo_manager.set_auth_token(bot_token)

        # Create a new branch locally from detached HEAD
        self.head_sha = self.repo_manager.repo.git.rev_parse("--short", "HEAD")
        self.branch_base_id = f"{self.head_sha}-{self.uuid}"

        logging.info(f"base branch identifer: {self.unique_branch()}")
        # Create the base branch for this workflow run.
        self.repo_manager.checkout_branch(self.unique_branch())
        logging.debug(
            f"Active branch name: {self.repo_manager.repo.active_branch.name}"
        )

        # Create the branch on the remote if it doesn't exist.
        try:
            r = github.github_api("get", f"repos/{test_repo}/branches", bot_token)
        except Exception as e:
            raise AssertionError(
                " ".join(
                    [
                        "Failed to Inintialize Test",
                        "Unable to get branches from the GitHub API.",
                        "Is GitHub having an outage?",
                        f"Error: {e}",
                    ]
                )
            )

        branches = json.loads(r.text)
        branch_names = [branch["name"] for branch in branches]
        logging.debug(f"Remote test repo branch names : {branch_names}")
        if self.unique_branch() not in branch_names:
            logging.info(
                f"{test_repo}:{self.unique_branch()} does not exists, creating with local branch"
            )
            self.repo_manager.push_branch(test_repo, self.unique_branch())

        # Create base branch and pr branch.
        base_branch, pr_branch = self.workflow_branches(self.test_name)
        logging.debug(f"base branch is set to: {base_branch}")
        logging.debug(f"pr branch is set to: {pr_branch}")

        # Set "secrets"
        #
        # NOTE(komish): This is a carry-over from the chart certification CI.
        # Not all items are secrets, but it's unclear why these are designated
        # as such. Prioritizing consistency for now.
        self.secrets.test_repo = test_repo
        self.secrets.bot_name = bot_name
        self.secrets.bot_token = bot_token
        self.secrets.base_branch = base_branch
        self.secrets.pr_branch = pr_branch
        self.secrets.index_file = "index.yaml"

        self.set_git_username_email(bot_name, settings.GITHUB_ACTIONS_BOT_EMAIL)
        self.temp_dir = self.repo_manager.add_worktree()

    def unique_branch(self) -> str:
        """Returns this instance's unique branch name."""
        return f"e2e-owners-{self.branch_base_id}"

    def workflow_branches(self, test_name: str) -> (str, str):
        """Returns the base_branch and pr_branch names for a given test_name."""
        pretty_test_name = self.test_name.strip().lower().replace(" ", "-")
        base_branch = (
            f"{self.unique_branch()}-{pretty_test_name}"
            if pretty_test_name
            else f"{self.unique_branch()}-test"
        )
        return base_branch, f"{base_branch}-pr-branch"

    def cleanup(self):
        """Cleans up all artifacts that are created locally and remotely."""
        logging.debug("RedHatOwnersFileSubmissionE2ETest --> cleanup called!")
        if self.repo_manager:
            try:
                self.repo_manager.cleanup()
            except Exception as e:
                logging.error(
                    f"failed to execute cleanup of the repo_manager with error: {e}"
                )

        # Teardown step to cleanup branches
        if self.temp_dir is not None:
            self.temp_dir.cleanup()

        if self.repo_manager:
            self.repo_manager.repo.git.worktree("prune")

    def submission_path(self) -> str:  # charts/partners/mycompany/mychartname
        """Composes the submission path based on the vendor_type, vendor, and chart_name values."""
        return os.path.join(
            "charts", self.vendor_category, self.vendor_label, self.chart_name
        )

    def set_git_username_email(self, username: str, email: str):
        """Writes the username and email to the repo's .git/config.

        Note that calling this will overwrite repository-local values, which
        will supercede global values.

        Args:
            username: git username to set
            email: git email to set
        """
        self.repo_manager.repo.config_writer().set_value(
            "user", "name", username
        ).release()
        self.repo_manager.repo.config_writer().set_value(
            "user", "email", email
        ).release()

    def create_and_commit_owners_file(self):
        self.repo_manager.checkout_branch(self.secrets.base_branch)
        self.repo_manager.push_branch(self.secrets.test_repo, self.secrets.base_branch)
        self.repo_manager.checkout_branch(self.secrets.pr_branch)
        return self._create_and_commit_owners_file(
            self.submission_path(),
            self.secrets.pr_branch,
            self.chart_name,
            self.vendor_label,
            self.vendor_name,
        )

    def _create_and_commit_owners_file(
        self,
        chart_directory: str,
        pr_branch: str,
        chart_name: str,
        vendor_label: str,
        vendor_name: str,
    ):
        """Creates an OWNERS file in the PR branch."""
        with SetDirectory(Path(self.temp_dir.name)):
            # Create the OWNERS file from the string template
            values = {
                "bot_name": self.secrets.bot_name,
                "vendor": vendor_label,
                "vendor_pretty": vendor_name,
                "chart_name": chart_name,
                "public_key": "null",
                "provider_delivery": "false",
            }
            content = Template(base_owners_file).substitute(values)
            logging.debug(f"OWNERS File Content:\n{content}")
            pathlib.Path(chart_directory).mkdir(parents=True, exist_ok=True)
            with open(f"{chart_directory}/OWNERS", "w+") as fd:
                fd.write(content)

            logging.info(f"Push OWNERS file to '{self.secrets.test_repo}:{pr_branch}'")
            worktree_repo = git.Repo()
            worktree_repo.git.add(f"{chart_directory}/OWNERS")
            worktree_repo.git.commit("-m", f"Add {chart_name} OWNERS file")
            self.repo_manager.push_branch(
                self.secrets.test_repo, pr_branch, repo=worktree_repo
            )

    def send_pull_request(self):
        """Sends a pull request to be evaluated for CI."""
        self.pull_request = self._send_pull_request(
            self.secrets.test_repo,
            self.secrets.base_branch,
            self.secrets.pr_branch,
            self.secrets.bot_token,
            os.environ.get("PR_BODY"),
        )
        return self.pull_request

    def _send_pull_request(
        self,
        remote_repo: str,
        base_branch: str,
        pr_branch: str,
        gh_token: str,
        pr_body: str,
    ):
        """Sends a pull request using the GitHub API.

        The branches should already exist in the remotes. This only sends the
        pull request API call referring to two pre-existing branches in
        remote_repo.

        Pull requests created with this method are not tracked for cleanup.
        When related branches are deleted, GitHub will automatically close the PR.

        Args:
            remote_repo: the org/repo string where the PR should be pushed.
            base_branch: the branch receiving the PR.
            pr_branch: the modified content to send to base_branch.
            pr_body: the text to send in the PR body.

        Raises:
            AssertionError in cases where the pull requests could not be sent.

        Returns:
            The PR number for the generated PR.
        """
        data = {
            "head": pr_branch,
            "base": base_branch,
            "title": base_branch,
            "body": pr_body,
        }
        logging.debug(f"Pull Request Body Text: {pr_body}")
        logging.info(
            f"Create PR from '{remote_repo}:{pr_branch}' to '{remote_repo}:{base_branch}'"
        )
        try:
            r = github.github_api(
                "post", f"repos/{remote_repo}/pulls", gh_token, json=data
            )
        except Exception as e:
            raise AssertionError(
                " ".join(
                    [
                        "Failed to send pull request.",
                        "Is GitHub having an outage?",
                        f"Error: {e}",
                    ]
                )
            )
        j = json.loads(r.text)
        if "number" not in j:
            raise AssertionError(f"error sending pull request, response was: {r.text}")
        return j["number"]

    def check_workflow_conclusion(
        self,
        expected_result: str,
    ):
        """Checks the input workflow and reports back if expected_result doesn't match reality."""

        # TODO(komish): When this testing is extended to partner/community files,
        # setting workflow_name should be more dynamic. For now, this always looks
        # for the Red Hat workflow because those are the only checks that exist.
        workflow_name = settings.WORKFLOW_REDHAT_OWNERS_CHECK

        return self._check_workflow_conclusion(
            self.pull_request,
            workflow_name,
            expected_result,
        )

    def _check_workflow_conclusion(
        self,
        pr_number: str,
        workflow_name: str,
        expected_result: str,
        failure_type="error",
    ):
        """Checks the conclusion of workflow_name for expected_result via the GitHub API.

        Args:
            pr_number: The pull request for which a worfklow should have executed, e.g. '1'.
            workflow_name: The name of the workflow whose outcome is relevant
            expected_result: The expected conclusion of the workflow. E.g. 'success'
            failure_type: Determines how this function treats conclusion mismatches.
              Raises if set to 'error'.

        Raises:
            AssertionError if the conclusion does not match the expected_result.

        Returns:
            run_id: The ID of the workflow
            conclusion: The actual conclusion of the workflow.
        """
        try:
            run_id = github.get_run_id(self.secrets, workflow_name, pr_number)
            conclusion = github.get_run_result(self.secrets, run_id)
        except Exception as e:
            if failure_type == "error":
                raise AssertionError(e)
            else:
                logging.warning(e)
                return None, None

        if conclusion == expected_result:
            logging.info(
                f"PR{pr_number} Workflow run was '{expected_result}' which is expected"
            )
        else:
            if failure_type == "error":
                raise AssertionError(
                    f"PR{pr_number if pr_number else self.secrets.pr_number} Workflow run was '{conclusion}' which is unexpected, run id: {run_id}"
                )
            else:
                logging.warning(
                    f"PR{pr_number if pr_number else self.secrets.pr_number} Workflow run was '{conclusion}' which is unexpected, run id: {run_id}"
                )

        return run_id, conclusion

    def set_chart_name(self, basename):
        """Generates a unique chart name from basename and stores both in self.

        Generated values are appended to the basename.

        Returns:
            The generated chart name value.
        """
        self.chart_base_name = basename
        self.chart_name = self.append_unique_id(basename)
        logging.debug(
            f'Caller provided chart name "{self.chart_base_name}", generated unique identifier: "{self.chart_name}"'
        )
        return self.chart_name

    def append_unique_id(self, base) -> str:
        """Appends this class' unique identifier, and optionally, the pr number."""
        # unique string based on uuid.uuid4()
        suffix = self.uuid
        if "PR_NUMBER" in os.environ:
            pr_num = os.environ["PR_NUMBER"]
            suffix = f"{suffix}-{pr_num}"
        return f"{base}-{suffix}"
