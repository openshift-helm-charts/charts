# coding=utf-8
"""Pull request with the report but without the chart feature tests."""

import os
import subprocess
from dataclasses import dataclass
from string import Template
import tempfile
import json
import base64

import requests
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

@pytest.fixture
def secrets():
    @dataclass
    class Secret:
        test_repo: str
        fork_repo: str
        cluster_token:  str
        bot_token: str
        bot_name: str
        pr_base_branch: str

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
    pr_number = os.environ.get("PR_NUMBER")
    if not pr_number:
        raise Exception("PR_NUMBER environment variable not defined")

    pr_base_branch = "test-pr-"+pr_number
    test_repo = str(base64.b64decode(test_repo), encoding="utf-8")
    fork_repo = str(base64.b64decode(fork_repo), encoding="utf-8")
    return Secret(test_repo, fork_repo, cluster_token, bot_token, bot_name, pr_base_branch)

@scenario('features/report_without_chart.feature', 'Partner submits report without any errors')
def test_partner_submits_report_without_any_errors():
    """Partner submits report without any errors."""

owners_file_content = """\
chart:
  name: psql-service
  shortDescription: null
publicPgpKey: null
users:
- githubUsername: ${bot_name}
vendor:
  label: acme
  name: ACME Inc.
"""

@given('the partner has created a report without any errors')
def the_partner_has_created_a_report_without_any_errors(secrets):
    """the partner has created a report without any errors."""

    if os.environ.get("WORKFLOW_DEVELOPMENT"):
        print("[INFO] wokflow development enabled")
        out = subprocess.run(["git", "add", "."], capture_output=True)
        print(out.stdout.decode("utf-8"))
        print(out.stderr.decode("utf-8"))

        out = subprocess.run(["git", "commit",  "-m", f"Checkpoint"], capture_output=True)
        print(out.stdout.decode("utf-8"))
        print(out.stderr.decode("utf-8"))

    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {secrets.bot_token}"}
    r = requests.get(f"https://api.github.com/repos/{secrets.test_repo}/git/ref/heads/gh-pages", headers=headers)
    print("[INFO] gh-pages branch", r.status_code, r.text, r.url)
    j = json.loads(r.text)
    sha = j["object"]["sha"]

    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {secrets.bot_token}"}
    data = {"ref": f"refs/heads/{secrets.pr_base_branch}-gh-pages", "sha": sha}
    r = requests.post(f"https://api.github.com/repos/{secrets.test_repo}/git/refs", headers=headers, json=data)

    old_cwd = os.getcwd()
    dr = tempfile.mkdtemp(prefix="tci-")
    print("[INFO] worktree directory:", dr)
    out = subprocess.run(["git", "worktree", "add", "--detach", dr, f"HEAD"], capture_output=True)

    os.chdir(dr)
    out = subprocess.run(["mkdir", "-p", "charts/partners/acme/psql-service/9.2.7"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    values = {"bot_name": secrets.bot_name}
    content = Template(owners_file_content).substitute(values)
    with open("charts/partners/acme/psql-service/OWNERS", "w") as fd:
        fd.write(content)

    out = subprocess.run(["git", "add", "charts"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    out = subprocess.run(["git", "commit",  "-m", f"Add acme psql-service OWNERS file"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    out = subprocess.run(["git", "push", f"https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}", f"HEAD:refs/heads/{secrets.pr_base_branch}", "-f"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    tmpl = open("tests/data/report.yaml").read()
    values = {"repository": secrets.test_repo, "branch": secrets.pr_base_branch}
    content = Template(tmpl).substitute(values)
    with open("charts/partners/acme/psql-service/9.2.7/report.yaml", "w") as fd:
        fd.write(content)

    out = subprocess.run(["git", "add", "charts"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    out = subprocess.run(["git", "commit",  "-m", f"Add acme psql-service 9.2.7 report.yaml"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    fork_branch = secrets.pr_base_branch + "-s1"
    out = subprocess.run(["git", "push", f"https://x-access-token:{secrets.bot_token}@github.com/{secrets.fork_repo}", f"HEAD:refs/heads/{fork_branch}", "-f"], capture_output=True)
    print(out.stdout.decode("utf-8"))
    print(out.stderr.decode("utf-8"))

    os.chdir(old_cwd)

@when('the partner sends the pull request with the report')
def the_partner_sends_the_pull_request_with_the_report(secrets):
    """the partner sends the pull request with the report."""

    fork_branch = secrets.pr_base_branch + "-s1"

    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {secrets.bot_token}"}
    actions_bot_name = "github-actions[bot]"
    if secrets.bot_name == actions_bot_name:
        head = fork_branch
    else:
        head = f"{secrets.bot_name}:{fork_branch}"
    data = {"head": head, "base": secrets.pr_base_branch, "title": fork_branch}
    r = requests.post(f"https://api.github.com/repos/{secrets.test_repo}/pulls", headers=headers, json=data)

@then('the index.yaml is updated with a new entry')
def the_indexyaml_is_updated_with_a_new_entry():
    """the index.yaml is updated with a new entry."""


@then('the partner should see the pull request getting merged')
def the_partner_should_see_the_pull_request_getting_merged():
    """the partner should see the pull request getting merged."""

