import os

import pytest

from chartprreview.chartprreview import (
    check_owners_file_against_directory_structure,
    verify_user,
    write_error_log,
)


def test_verify_user():
    with pytest.raises(SystemExit):
        verify_user("mbaiju", "partners", "test-org1", "test-chart")


owners_with_wrong_vendor_label = """\
---
chart:
  name: test-chart
  shortDescription: Lorem ipsum
publicPgpKey: |
 users:
  - githubUsername: baijum
  - githubUsername: someuserdoesnotexist1234
vendor:
  label: test-org-wrong
  name: Test Org
"""

owners_with_wrong_chart_name = """\
---
chart:
  name: test-chart-wrong
  shortDescription: Lorem ipsum
publicPgpKey: |
 users:
  - githubUsername: baijum
  - githubUsername: someuserdoesnotexist1234
vendor:
  label: test-org
  name: Test Org
"""

owners_with_correct_values = """\
---
chart:
  name: test-chart
  shortDescription: Lorem ipsum
publicPgpKey: |
 users:
  - githubUsername: baijum
  - githubUsername: someuserdoesnotexist1234
vendor:
  label: test-org
  name: Test Org
"""


def test_check_owners_file_against_directory_structure(tmpdir):
    p = (
        tmpdir.mkdir("charts")
        .mkdir("partners")
        .mkdir("test-org")
        .mkdir("test-chart")
        .join("OWNERS")
    )
    p.write(owners_with_wrong_vendor_label)
    os.chdir(tmpdir)
    new_cwd = os.getcwd()
    print("new_cwd", new_cwd)
    with pytest.raises(SystemExit):
        check_owners_file_against_directory_structure(
            "partners", "test-org", "test-chart"
        )
    p.write(owners_with_wrong_chart_name)
    with pytest.raises(SystemExit):
        check_owners_file_against_directory_structure(
            "partners", "test-org", "test-chart"
        )
    p.write(owners_with_correct_values)
    check_owners_file_against_directory_structure("partners", "test-org", "test-chart")


def test_write_error_log(tmpdir):
    write_error_log(tmpdir, "First message")
    msg = open(os.path.join(tmpdir, "errors")).read()
    assert msg == "First message\n"

    write_error_log(tmpdir, "First message", "Second message")
    msg = open(os.path.join(tmpdir, "errors")).read()
    assert msg == "First message\nSecond message\n"
