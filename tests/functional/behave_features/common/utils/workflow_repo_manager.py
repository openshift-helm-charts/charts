# -*- coding: utf-8 -*-
"""Utility class for managing local/remote git branches and worktrees"""

import os
import logging
import git

from tempfile import TemporaryDirectory

import common.utils.github as github


class RepoManagementError(Exception):
    pass


class WorkflowRepoManager:
    # Keep a log of things created so we can clean them up.
    __local_branches_created: [str] = []
    __local_worktrees_created: [TemporaryDirectory] = []
    # (remote, branch), e.g. ('openshift-helm-charts/charts, 'my-pr-branch')
    __remote_branches_created: [(str, str)] = []

    # The token to use for GitHub API operations.
    __authtoken: str = ""

    # The branch at repo initialization. On Cleanup, we return to this branch
    # before we remove locally generated branches.
    original_branch: str = None

    # Working directory at instantiation.
    old_cwd: str = os.getcwd()

    # The repository at working directory.
    repo: git.Repo = None

    def __init__(self):
        logging.debug(f"{self} --> __init__ called!")

        try:
            self.repo = git.Repo()
        except git.InvalidGitRepositoryError as e:
            raise RepoManagementError(
                "Unable to initialize git repository. Is the current directory a git repo?"
            ) from e

        self.original_branch = self.repo.active_branch.name

    def set_auth_token(self, token: str):
        """Sets the github API token."""
        self.__authtoken = token

    def push_branch(self, remote_name: str, branch_name: str, repo: git.Repo = None):
        """Pushes the input branch_name to remote_name.

        The branch must exist locally before this is called, as it is not
        created by this method.

        Args:
            remote_name: the name of the remote in organization/repository format.
            branch_name: the branch to push.
            repo: if set, overrides the use of the internal repo.

        Raises:
           RepoManagementError: When failing to push a branch.
        """
        r = repo if repo is not None else self.repo
        try:
            r.git.push(
                f"https://x-access-token:{self.__authtoken}@github.com/{remote_name}",
                f"HEAD:refs/heads/{branch_name}",
                "-f",
            )
        except (git.GitCommandError, ValueError) as e:
            raise RepoManagementError("Unable to push branch to remote") from e
        self.__remote_branches_created.append((remote_name, branch_name))

    def checkout_branch(self, branch_name: str):
        """Checks out a branch at branch_name and switches to it immediately.

        Branches created with this method are stored internally
        and cleaned up when cleanup() is called.

        Args:
            branch_name: The branch name to create.

        Raises:
           RepoManagementError: When creating a branch locally.
        """
        try:
            self.repo.git.checkout("-b", branch_name)
        except (git.GitCommandError, ValueError) as e:
            raise RepoManagementError("Unable to create branch") from e
        self.__local_branches_created.append(branch_name)

    def add_worktree(self) -> TemporaryDirectory:
        """Creates a worktree at a generated tempdir.

        Worktrees created with this method are stored internally
        and cleaned up when cleanup() is called.

        Returns:
            The TemporaryDirectory for the worktree that was requested.

        Raise:
            RepoManagementError: When creating a worktree locally.
        """
        worktree_dir = TemporaryDirectory(prefix="worktree-")

        try:
            self.repo.git.worktree("add", "--detach", worktree_dir.name, "HEAD")
        except (git.GitCommandError, ValueError) as e:
            raise RepoManagementError("Unable to create worktree") from e
        self.__local_worktrees_created.append(worktree_dir)

        return worktree_dir

    def cleanup_local_branches(self):
        """Cleans up branches created by this repo manager."""
        for br in self.__local_branches_created:
            try:
                logging.info(f'Cleaning up generated local branch: "{br}"')
                self.repo.git.branch("-D", br)
            except (git.GitCommandError, ValueError) as e:
                logging.warn(
                    f'local branch "{br}" could not be deleted, potentially because it did not exist. Error: {e}'
                )
        self.__local_branches_created = []

    def cleanup_worktrees(self):
        """Cleans up local worktrees created by this repo manager."""
        for wt in self.__local_worktrees_created:
            logging.info(f'Cleaning up generated local worktree: "{wt}"')
            try:
                self.repo.git.worktree("remove", wt.name)
            except (git.GitCommandError, ValueError) as e:
                logging.warn(
                    f'local worktree "{wt}" could not be deleted, potentially because it did not exist. Error: {e}'
                )
        self.__local_worktrees_created = []

    def cleanup_remote_branches(self):
        """Cleans up remote branches created by this repo manager."""
        for rbr in self.__remote_branches_created:
            remote = rbr[0]
            branch = rbr[1]
            logging.info(f'Cleaning up branch "{branch}" from remote "{remote}')
            try:
                self.repo.git.push(
                    f"https://x-access-token:{self.__authtoken}@github.com/{remote}",
                    "--delete", 
                    f"refs/heads/{branch}",
                )
            except (git.GitCommandError, ValueError) as e:
                logging.warn(
                    f'remote branch "{branch}" could not be deleted from {remote}, potentially because it did not exist. Error: {e}'
                )
        self.__remote_branches_created = []

    def cleanup(self):
        """Cleans up resources created using this instance.

        Locally created branches and worktrees are removed. Exceptions in removing
        these will emit a log line at the warn log level.
        """
        logging.debug(f"{self} --> cleanup called!")
        self.repo.git.checkout(self.original_branch)
        self.cleanup_local_branches()
        self.cleanup_worktrees()
        self.cleanup_remote_branches()
