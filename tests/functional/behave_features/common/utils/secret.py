# -*- coding: utf-8 -*-
"""Utility class for storing test specific settings."""

from dataclasses import dataclass

@dataclass
class E2ETestSecret:
    # common secrets between one-shot and recursive tests
    test_repo: str = ''
    bot_name: str = ''
    bot_token: str = ''
    pr_number: int = -1
    vendor_type: str = ''
    owners_file_content: str = ''

@dataclass
class E2ETestSecretOneShot(E2ETestSecret):
    # one-shot testing
    active_branch: str = ''
    base_branch: str = ''
    pr_branch: str = ''
    pr_number: int = -1
    vendor: str = ''
    bad_version: str = ''
    provider_delivery: bool = False
    index_file: str = "index.yaml"

@dataclass
class E2ETestSecretRecursive(E2ETestSecret):
    # recursive testing
    software_name: str = ''
    software_version: str = ''
    pr_base_branch: str = ''
    base_branches: list = None
    pr_branches: list = None
    dry_run: bool = True
    notify_id: list = None
    submitted_charts: list = None
    release_tags: list = None
