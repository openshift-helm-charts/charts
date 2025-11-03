"""Unit tests for the Submission Class

Each test is run against a list of "Scenarios":
- A dataclass named after the function under test and suffixed with "Scenario" is defined
- A list of scenarios to be run against the function under test is created
- The test function is called using the pytest.mark.parametrize decorator

"""

import contextlib
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import tarfile
import tempfile

import pytest
import responses

from reporegex import matchers
from submission import submission

# Define assets that are being reused accross tests
expected_category = "partners"
expected_organization = "acme"
expected_name = "awesome"
expected_version = "1.42.0"

expected_chart = submission.Chart(
    category=expected_category,
    organization=expected_organization,
    name=expected_name,
    version=expected_version,
)


def make_new_report_only_submission():
    """Return an initialized Submission that contains only an unsigned report file

    This is a relatively common use case that is used for many scenarios.
    """
    s = submission.Submission(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml"
        ],
        chart=expected_chart,
        report=submission.Report(
            found=True,
            signed=False,
            path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
        ),
    )

    return s


def make_new_tarball_only_submission():
    """Return an initialized Submission that contains only an unsigned tarball"""
    s = submission.Submission(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        chart=expected_chart,
        tarball=submission.Tarball(
            found=True,
            provenance=None,
            path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
        ),
    )
    return s


def get_tarball_from_modified_files(modified_files: list[str]) -> str:
    """Browse the modified files and return information on the first tarball found (.tgz)

    Args:
        modified_files (list[str]): List of files modified by the PR

    Returns:
        (str, str): basedir and filename of the tarball

    """
    _, _, tarballpattern = matchers.get_file_match_compiled_patterns()

    for file in modified_files:
        if tarballpattern.match(file):
            return os.path.split(file)
    return "", ""


def create_tarball(tarball_basedir: str, tarball_name: str, tarball_content: list[str]):
    """Create a tarball.

    Args:
        tarball_basedir (str): Directory in which to place the tarball. Will be created.
        tarball_name (str): Name of the tarball including .tgz extension.
        tarball_content (list[str]): List files to be included in the tarball. Files are empty as we don't perform any
            check based on the content of the files, only on theire presence or absence in the tarball.

    """
    with tempfile.TemporaryDirectory() as content_temp_dir:
        # Create tarball content in a temporary directory.
        for file in tarball_content:
            # Ensure base directory exists
            os.makedirs(
                os.path.join(content_temp_dir, os.path.dirname(file)), exist_ok=True
            )
            # Create an empty file - we don't check actual content of any files
            Path(os.path.join(content_temp_dir, file)).touch()

        # Create tarball base directory
        os.makedirs(tarball_basedir)

        # Create tarball
        with tarfile.open(
            os.path.join(tarball_basedir, tarball_name), mode="w:gz"
        ) as tarball:
            # os.listdir lists both files and directory
            for file in os.listdir(content_temp_dir):
                # Add the files and directories present in the root folder into the archive. Directory content is
                # automatically added recursively.
                # Use arcname option to rename the file/directory within the archive and make them relative paths.
                tarball.add(
                    os.path.join(content_temp_dir, file), arcname=os.path.basename(file)
                )


@dataclass
class SubmissionInitScenario:
    api_url: str
    modified_files: list[str]
    tarball_content: list[str] = field(default_factory=list)
    expected_submission: submission.Submission = None
    excepted_exception: contextlib.ContextDecorator = field(
        default_factory=contextlib.nullcontext
    )


scenarios_submission_init = [
    # PR contains a unique and unsigned report.yaml
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml"
        ],
        expected_submission=make_new_report_only_submission(),
    ),
    # PR contains a signed report
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/2",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml.asc",
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/2",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml.asc",
            ],
            chart=expected_chart,
            report=submission.Report(
                found=True,
                signed=True,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            ),
        ),
    ),
    # PR contains the chart's source
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/3",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/Chart.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/buildconfig.yam"
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/deployment.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/imagestream.yam"
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/route.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/service.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.schema.json",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.yaml",
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/3",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/Chart.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/buildconfig.yam"
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/deployment.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/imagestream.yam"
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/route.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/service.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.schema.json",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.yaml",
            ],
            chart=expected_chart,
            source=submission.Source(
                found=True,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src",
            ),
        ),
    ),
    # PR contains an unsigned tarball
    # Tarball contains a Chart.yaml placed under the directory named after the chart
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        tarball_content=[os.path.join(expected_name, "Chart.yaml")],
        expected_submission=make_new_tarball_only_submission(),
    ),
    # PR contains a signed tarball
    # Tarball contains a Chart.yaml placed under the directory named after the chart
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/5",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz.prov",
        ],
        tarball_content=[os.path.join(expected_name, "Chart.yaml")],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/5",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz.prov",
            ],
            chart=expected_chart,
            tarball=submission.Tarball(
                found=True,
                provenance=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz.prov",
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
            ),
        ),
    ),
    # PR contains an unsigned tarball
    # Tarball contains a Chart.yaml and additional files, placed under the directory named after the chart
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        tarball_content=[
            os.path.join(expected_name, "Chart.yaml"),
            os.path.join(expected_name, "bar"),
            os.path.join(expected_name, "foo", "baz"),
        ],
        expected_submission=make_new_tarball_only_submission(),
    ),
    # PR contains an unsigned tarball
    # Tarball contains a Chart.yaml, placed under the directory that is not named after the chart
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        tarball_content=[os.path.join("not-awesome", "Chart.yaml")],
        excepted_exception=pytest.raises(
            submission.SubmissionError,
            match=re.escape(
                f"[ERROR] Incorrect tarball content: expected a {expected_name} directory"
            ),
        ),
    ),
    # PR contains an unsigned tarball
    # Tarball contains additional files placed at the root directory
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        tarball_content=[
            os.path.join(expected_name, "Chart.yaml"),
            os.path.join("bar"),
        ],
        excepted_exception=pytest.raises(
            submission.SubmissionError,
            match=re.escape(
                f"[ERROR] Incorrect tarball content: found a file outside the {expected_name} directory"
            ),
        ),
    ),
    # PR contains an unsigned tarball
    # Tarball does not contain a Chart.yaml under the directory named after the chart
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        tarball_content=[
            os.path.join(expected_name, "bar"),
        ],
        excepted_exception=pytest.raises(
            submission.SubmissionError,
            match=re.escape(
                f"[ERROR] Incorrect tarball content: expected a {expected_name}/Chart.yaml file"
            ),
        ),
    ),
    # PR contains an unsigned tarball
    # Tarball is empty
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        tarball_content=[],
        excepted_exception=pytest.raises(
            submission.SubmissionError,
            match=re.escape(
                f"[ERROR] Incorrect tarball content: expected a {expected_name} directory"
            ),
        ),
    ),
    # PR contains an OWNERS file
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/6",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/6",
            chart=submission.Chart(
                category=expected_chart.category,
                organization=expected_chart.organization,
                name=expected_chart.name,
                # OWNERS submissions do not contain version information.
            ),
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
        ),
    ),
    # PR contains additional files, not fitting into any expected category
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/7",
        modified_files=["charts/path/to/some/file"],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/7",
            modified_files=["charts/path/to/some/file"],
            modified_unknown=["charts/path/to/some/file"],
        ),
    ),
    # Invalid PR contains multiple reports, referencing multiple charts
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/101",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            f"charts/{expected_category}/{expected_organization}/other-chart/{expected_version}/report.yaml",
        ],
        excepted_exception=pytest.raises(submission.DuplicateChartError),
    ),
    # Invalid PR contains a tarball with an incorrect name
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/102",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/incorrectly-named.tgz"
        ],
        excepted_exception=pytest.raises(submission.SubmissionError),
    ),
    # Invalid PR references a Chart with a version that is not Semver compatible
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/103",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/0.1.2.3.4/report.yaml"
        ],
        excepted_exception=pytest.raises(submission.VersionError),
    ),
    # Invalid PR references a Chart from redhat without the "redhat-" prefix
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/103",
        modified_files=[
            f"charts/{expected_category}/redhat/{expected_name}/{expected_version}/report.yaml"
        ],
        excepted_exception=pytest.raises(submission.ChartError),
    ),
    # Invalid PR references a Chart with the "redhat-" prefix from another organization
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/103",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/redhat-{expected_name}/{expected_version}/report.yaml"
        ],
        excepted_exception=pytest.raises(submission.ChartError),
    ),
    # Invalid PR doesn't contain any files
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/103",
        modified_files=[],
        excepted_exception=pytest.raises(submission.SubmissionError),
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_submission_init)
@responses.activate
def test_submission_init(test_scenario):
    """Test the instantiation of a Submission in different scenarios"""

    # Mock GitHub API
    responses.get(
        f"{test_scenario.api_url}/files",
        json=[{"filename": file} for file in test_scenario.modified_files],
    )

    # Mock step checking out the PR locally - create tempdir with PR content
    with tempfile.TemporaryDirectory() as prbanch_temp_dir:
        # This step is only necessary if the PR contains a tarball, otherwise we don't perform any check of the content
        # of the PR files.
        tarball_path, tarball_name = get_tarball_from_modified_files(
            test_scenario.modified_files
        )
        if tarball_path:
            create_tarball(
                os.path.join(prbanch_temp_dir, tarball_path),
                tarball_name,
                test_scenario.tarball_content,
            )

        with test_scenario.excepted_exception:
            s = submission.Submission(api_url=test_scenario.api_url)
            s.parse_modified_files(repo_path=prbanch_temp_dir)
            assert s == test_scenario.expected_submission


@responses.activate
def test_submission_not_exist():
    """Test creating a Submission for an unexisting PR"""

    api_url_doesnt_exist = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/9999"
    )

    responses.get(
        f"{api_url_doesnt_exist}/files",
        json={
            "message": "Not Found",
            "documentation_url": "https://docs.github.com/rest/pulls/pulls#list-pull-requests-files",
        },
    )

    with pytest.raises(submission.SubmissionError):
        submission.Submission(api_url=api_url_doesnt_exist)


@dataclass
class CertificationScenario:
    input_submission: submission.Submission
    expected_is_valid_certification: bool
    expected_reason: str = ""
    ignore_owners: bool = False


scenarios_certification_submission = [
    # Valid certification Submission contains only a report
    CertificationScenario(
        input_submission=make_new_report_only_submission(),
        expected_is_valid_certification=True,
    ),
    # Invalid certification Submission contains OWNERS file
    CertificationScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
        ),
        expected_is_valid_certification=False,
        expected_reason="[ERROR] Send OWNERS file by itself in a separate PR.",
    ),
    # Valid certification Submission contains OWNERS and report file, but ignore_owners is set to True
    CertificationScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml"
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            report=submission.Report(
                found=True,
                signed=False,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            ),
        ),
        expected_is_valid_certification=True,
        ignore_owners=True,
    ),
    # Invalid certification Submission contains unknown files
    CertificationScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=["charts/path/to/some/file"],
            modified_unknown=["charts/path/to/some/file"],
        ),
        expected_is_valid_certification=False,
        expected_reason="[ERROR] PR includes one or more files not related to charts:",
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_certification_submission)
def test_is_valid_certification(test_scenario):
    is_valid_certification, reason = (
        test_scenario.input_submission.is_valid_certification_submission(
            test_scenario.ignore_owners
        )
    )
    assert test_scenario.expected_is_valid_certification == is_valid_certification
    assert test_scenario.expected_reason in reason


@dataclass
class OwnersScenario:
    input_submission: submission.Submission
    expected_is_valid_owners: bool
    expected_reason: str = ""


scenarios_owners_submission = [
    # Valid submission contains only one OWNERS file
    OwnersScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
        ),
        expected_is_valid_owners=True,
    ),
    # Invalid submission contains multiple OWNERS file
    OwnersScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS",
                f"charts/{expected_category}/{expected_organization}/another_chart/OWNERS",
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS",
                f"charts/{expected_category}/{expected_organization}/another_chart/OWNERS",
            ],
        ),
        expected_is_valid_owners=False,
        expected_reason="[ERROR] Send OWNERS file by itself in a separate PR.",
    ),
    # Invalid submission contains unknown files
    OwnersScenario(
        input_submission=make_new_report_only_submission(),
        expected_is_valid_owners=False,
        expected_reason="No OWNERS file provided",
    ),
    # Invalid submission doesn't contain an OWNER file
]


@pytest.mark.parametrize("test_scenario", scenarios_owners_submission)
def test_is_valid_owners(test_scenario):
    is_valid_owners, reason = (
        test_scenario.input_submission.is_valid_owners_submission()
    )
    assert test_scenario.expected_is_valid_owners == is_valid_owners
    assert test_scenario.expected_reason in reason


@dataclass
class WebCatalogOnlyScenario:
    input_submission: submission.Submission
    create_owners: bool = True
    create_report: bool = True
    owners_web_catalog_only: str = None  # Set to None to skip key creation in OWNERS
    report_web_catalog_only: str = None  # Set to None to skip key creation in report
    expected_output: bool = None
    excepted_exception: contextlib.ContextDecorator = field(
        default_factory=contextlib.nullcontext
    )


scenarios_web_catalog_only = [
    # Submission contains a report file with WebCatalogOnly set to True, matching the content of OWNERS
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="true",
        report_web_catalog_only="true",
        expected_output=True,
    ),
    # Submission contains a report file with WebCatalogOnly set to False, matching the content of OWNERS
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="false",
        report_web_catalog_only="false",
        expected_output=False,
    ),
    # Submission contains a report file with WebCatalogOnly set to True, not matching the content of OWNERS
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="true",
        report_web_catalog_only="false",
        excepted_exception=pytest.raises(
            submission.WebCatalogOnlyError,
            match="The web catalog distribution method is set for the chart but is not set in the report.",
        ),
    ),
    # Submission contains a report file with WebCatalogOnly set to False, not matching the content of OWNERS
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="false",
        report_web_catalog_only="true",
        excepted_exception=pytest.raises(
            submission.WebCatalogOnlyError,
            match="Report indicates web catalog only but the distribution method set for the chart is not web catalog only.",
        ),
    ),
    # Submission doesn't relate to an existing OWNERS
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        create_owners=False,
        report_web_catalog_only="true",
        excepted_exception=pytest.raises(
            submission.WebCatalogOnlyError, match="Failed to get OWNERS data"
        ),
    ),
    # Submission contains a report, but it can't be found
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="true",
        create_report=False,
        excepted_exception=pytest.raises(
            submission.WebCatalogOnlyError, match="Failed to get report data"
        ),
    ),
    # The OWNERS file for this chart doesn't contain the WebCatalogOnly key, defaulting to False, and matching the report value
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="false",
        report_web_catalog_only="false",
        expected_output=False,
    ),
    # The OWNERS file for this chart doesn't contain the WebCatalogOnly key, defaulting to False, and not matching the report value
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="false",
        report_web_catalog_only="true",
        excepted_exception=pytest.raises(submission.WebCatalogOnlyError),
    ),
    # Submission contains a report, that doesn't contain the WebCatalogOnly key
    WebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        owners_web_catalog_only="false",
        report_web_catalog_only=None,
        excepted_exception=pytest.raises(submission.WebCatalogOnlyError),
    ),
    # Submission doesn't contain a report, OWNERS file has WebCatalogOnly set to True
    # Note that this is not a valid scenario: if webCatalogOnly is set to True in the OWNERS file,
    # all chart submissions should contain only a report. This check is part of the
    # is_valid_web_catalog_only method.
    WebCatalogOnlyScenario(
        input_submission=make_new_tarball_only_submission(),
        owners_web_catalog_only="true",
        report_web_catalog_only=None,
        expected_output=True,
    ),
    # Submission doesn't contain a report, OWNERS file has WebCatalogOnly set to False
    WebCatalogOnlyScenario(
        input_submission=make_new_tarball_only_submission(),
        owners_web_catalog_only="false",
        report_web_catalog_only=None,
        expected_output=False,
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_web_catalog_only)
def test_parse_web_catalog_only(test_scenario):
    """Use a temporary directory, which content mimic the certification repository

    A OWNERS file and a report.yaml are placed at the correct location, containing the minimum
    information required for this test to function (a webCatalogOnly value).

    """
    with tempfile.TemporaryDirectory(dir=".") as temp_dir:
        # Create directory structure
        owners_base_path = os.path.join(
            temp_dir,
            "charts",
            expected_category,
            expected_organization,
            expected_name,
        )
        chart_base_path = os.path.join(
            owners_base_path,
            expected_version,
        )
        os.makedirs(chart_base_path)

        # Populate OWNERS file
        if test_scenario.create_owners:
            with open(
                os.path.join(owners_base_path, "OWNERS"), "w", encoding="utf-8"
            ) as owners_file:
                owners_file.write(
                    "publicPgpKey: unknown"
                )  # Make sure OWNERS is not an empty file
                if test_scenario.owners_web_catalog_only:
                    owners_file.write(
                        f"\nproviderDelivery: {test_scenario.owners_web_catalog_only}"
                    )

        # Populate report.yaml file
        if test_scenario.create_report:
            with open(
                os.path.join(chart_base_path, "report.yaml"), "w", encoding="utf-8"
            ) as report_file:
                report_file.writelines(
                    [
                        "apiversion: v1",
                        "\nkind: verify-report",
                    ]
                )
                if test_scenario.report_web_catalog_only:
                    report_file.writelines(
                        [
                            "\nmetadata:",
                            "\n    tool:",
                            f"\n        webCatalogOnly: {test_scenario.report_web_catalog_only}",
                        ]
                    )

        with test_scenario.excepted_exception:
            test_scenario.input_submission.parse_web_catalog_only(repo_path=temp_dir)

        assert (
            test_scenario.input_submission.is_web_catalog_only
            == test_scenario.expected_output
        )


@dataclass
class IsWebCatalogOnlyScenario:
    input_submission: submission.Submission
    create_report: bool = True
    report_has_digest: bool = None
    expected_is_valid_web_catalog_only: bool = None
    expected_reason: str = ""


scenarios_is_web_catalog_only = [
    # Submission contains only a report, and report contains a digest
    IsWebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        report_has_digest=True,
        expected_is_valid_web_catalog_only=True,
    ),
    # Submission contains only a report, but report contains no digest
    IsWebCatalogOnlyScenario(
        input_submission=make_new_report_only_submission(),
        report_has_digest=False,
        expected_is_valid_web_catalog_only=False,
        expected_reason="The web catalog distribution method requires a package digest in the report.",
    ),
    # Submission contains no report
    IsWebCatalogOnlyScenario(
        input_submission=make_new_tarball_only_submission(),
        create_report=False,
        expected_is_valid_web_catalog_only=False,
        expected_reason="The web catalog distribution method requires the pull request to contain a report.",
    ),
    # Submission contains a report and other files
    IsWebCatalogOnlyScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
            ],
            chart=expected_chart,
            report=submission.Report(
                found=True,
                signed=False,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            ),
            tarball=submission.Tarball(
                found=True,
                provenance=None,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
            ),
        ),
        report_has_digest=True,
        expected_is_valid_web_catalog_only=False,
        expected_reason="The web catalog distribution method requires the pull request to be report only.",
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_is_web_catalog_only)
def test_is_valid_web_catalog_only(test_scenario):

    with tempfile.TemporaryDirectory(dir=".") as temp_dir:
        # Create directory structure
        chart_base_path = os.path.join(
            temp_dir,
            "charts",
            expected_category,
            expected_organization,
            expected_name,
            expected_version,
        )
        os.makedirs(chart_base_path)

        # Populate report.yaml file
        if test_scenario.create_report:
            with open(
                os.path.join(chart_base_path, "report.yaml"), "w", encoding="utf-8"
            ) as report_file:
                report_file.writelines(
                    [
                        "apiversion: v1",
                        "\nkind: verify-report",
                    ]
                )
                if test_scenario.report_has_digest:
                    report_file.writelines(
                        [
                            "\nmetadata:",
                            "\n    tool:",
                            "\n        digests:",
                            "\n            package: 7755e7cf43e55bbf2edafd9788b773b844fb15626c5ff8ff7a30a6d9034f3a33",
                        ]
                    )

        is_valid_web_catalog_only, reason = (
            test_scenario.input_submission.is_valid_web_catalog_only(repo_path=temp_dir)
        )
        assert (
            test_scenario.expected_is_valid_web_catalog_only
            == is_valid_web_catalog_only
        )
        assert test_scenario.expected_reason in reason


def create_new_index(charts: list[submission.Chart] = None):
    """Create the JSON representation of a Helm chart index containing the provided list of charts

    The resulting index only contains the required information for the check_index to work.

    """
    if charts is None:
        charts = []

    index = {"apiVersion": "v1", "entries": {}}

    for chart in charts:
        chart_entries = index["entries"].get(chart.name, [])
        chart_entries.append(
            {
                "name": f"{chart.name}",
                "version": f"{chart.version}",
            }
        )

        index["entries"][chart.name] = chart_entries

    return index


@dataclass
class CheckIndexScenario:
    chart: submission.Chart = field(
        default_factory=lambda: submission.Chart(
            category=expected_category,
            organization=expected_organization,
            name=expected_name,
            version=expected_version,
        )
    )
    index: dict = field(default_factory=create_new_index)
    excepted_exception: contextlib.ContextDecorator = field(
        default_factory=contextlib.nullcontext
    )


scenarios_check_index = [
    # Chart is not present in the index
    CheckIndexScenario(
        index=create_new_index([submission.Chart(name="not-awesome", version="0.42")])
    ),
    # Chart is present but does not contain submitted version
    CheckIndexScenario(
        index=create_new_index([submission.Chart(name=expected_name, version="0.42")])
    ),
    # Submitted version is present in index
    CheckIndexScenario(
        index=create_new_index(
            [submission.Chart(name=expected_name, version=expected_version)]
        ),
        excepted_exception=pytest.raises(
            submission.HelmIndexError,
            match="Helm chart release already exists in the index.yaml",
        ),
    ),
    # Index is empty
    CheckIndexScenario(),
    # Index is an empty dict
    CheckIndexScenario(
        index={},
        excepted_exception=pytest.raises(
            submission.HelmIndexError, match="Malformed index"
        ),
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_check_index)
def test_check_index(test_scenario):
    with test_scenario.excepted_exception:
        test_scenario.chart.check_index(test_scenario.index)


@dataclass
class CheckReleaseTagScenario:
    chart: submission.Chart = field(
        default_factory=lambda: submission.Chart(
            category=expected_category,
            organization=expected_organization,
            name=expected_name,
            version=expected_version,
        )
    )
    exising_tags: list[str] = field(default_factory=list)
    excepted_exception: contextlib.ContextDecorator = field(
        default_factory=contextlib.nullcontext
    )


scenarios_check_release_tag = [
    # A release doesn't exist for this org
    CheckReleaseTagScenario(exising_tags=["notacme-notawesome-0.42"]),
    # A release exist for this org, but not for this chart
    CheckReleaseTagScenario(exising_tags=[f"{expected_organization}-notawesome-0.42"]),
    # A release exist for this Chart but not in this version
    CheckReleaseTagScenario(
        exising_tags=[f"{expected_organization}-{expected_name}-0.42"],
    ),
    # A release exist for this Chart in this version
    CheckReleaseTagScenario(
        exising_tags=[f"{expected_organization}-{expected_name}-{expected_version}"],
        excepted_exception=pytest.raises(
            submission.ReleaseTagError,
            match="Helm chart release already exists in the GitHub Release/Tag",
        ),
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_check_release_tag)
@responses.activate
def test_check_release_tag(test_scenario):
    chart_release_tag = test_scenario.chart.get_release_tag()

    if chart_release_tag not in test_scenario.exising_tags:
        responses.head(
            f"https://api.github.com/repos/my-fake-org/my-fake-repo/git/ref/tags/{chart_release_tag}",
            status=404,
        )

    for tag in test_scenario.exising_tags:
        # Mock GitHub API
        responses.head(
            f"https://api.github.com/repos/my-fake-org/my-fake-repo/git/ref/tags/{tag}",
        )

    with test_scenario.excepted_exception:
        test_scenario.chart.check_release_tag(repository="my-fake-org/my-fake-repo")
