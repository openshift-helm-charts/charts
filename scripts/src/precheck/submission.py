import os
import re
import requests
import semver
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dataclasses import dataclass, field

from checkprcontent import checkpr
from owners import owners_file
from tools import gitutils
from reporegex import matchers
from report import verifier_report

xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"


class SubmissionError(Exception):
    """Root Exception for handling any error with the submission"""

    pass


class DuplicateChartError(SubmissionError):
    """This Exception is to be raised when the user attempts to submit a PR with more than one chart"""

    pass


class VersionError(SubmissionError):
    """This Exception is to be raised when the version of the chart is not semver compatible"""

    pass


class WebCatalogOnlyError(SubmissionError):
    pass


class HelmIndexError(SubmissionError):
    pass


class ReleaseTagError(SubmissionError):
    pass


class ChartError(Exception):
    pass


@dataclass
class Chart:
    """Represents a Helm Chart

    Once set, the category, organization, name and version of the chart cannot be modified.

    """

    category: str = None
    organization: str = None
    name: str = None
    version: str = None

    def register_chart_info(self, category, organization, name, version):
        if (
            (self.category and self.category != category)
            or (self.organization and self.organization != organization)
            or (self.name and self.name != name)
            or (self.version and self.version != version)
        ):
            msg = "[ERROR] A PR must contain only one chart. Current PR includes files for multiple charts."
            raise DuplicateChartError(msg)

        if not semver.VersionInfo.is_valid(version):
            msg = (
                f"[ERROR] Helm chart version is not a valid semantic version: {version}"
            )
            raise VersionError(msg)

        # Red Hat charts must carry the Red Hat prefix.
        if organization == "redhat":
            if not name.startswith("redhat-"):
                msg = f"[ERROR] Charts provided by Red Hat must have their name begin with the redhat- prefix. I.e. redhat-{name}"
                raise ChartError(msg)

        # Non Red Hat charts must not carry the Red Hat prefix.
        if organization != "redhat" and name.startswith("redhat-"):
            msg = f"[ERROR] The redhat- prefix is reserved for charts provided by Red Hat. Your chart: {name}"
            raise ChartError(msg)

        self.category = category
        self.organization = organization
        self.name = name
        self.version = version

    def get_owners_path(self):
        return f"charts/{self.category}/{self.organization}/{self.name}/OWNERS"

    def get_release_tag(self):
        return f"{self.organization}-{self.name}-{self.version}"

    def check_index(self, index):
        """Check if the chart is present in the Helm index

        Args:
            index (dict): Content of the Helm repo index

        Raise:
            HelmIndexError if:
            * The provided index is malformed
            * The Chart is already present in the index

        """
        try:
            chart_entry = index["entries"].get(self.name, [])
        except KeyError as e:
            raise HelmIndexError(f"Malformed index {index}") from e

        for chart in chart_entry:
            if chart["version"] == self.version:
                msg = f"[ERROR] Helm chart release already exists in the index.yaml: {self.version}"
                raise HelmIndexError(msg)

    def check_release_tag(self, repository: str):
        """Check for the existence of the chart's release tag on the provided repository.

        Args:
            repository (str): Name of the GitHub repository to check for existing tag.
                              (e.g. "openshift-helm-charts/charts")

        Raise: ReleaseTagError if the tag already exists in the GitHub repo.

        """
        tag_name = self.get_release_tag()
        tag_api = f"https://api.github.com/repos/{repository}/git/ref/tags/{tag_name}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        print(f"[INFO] checking tag: {tag_api}")
        r = requests.head(tag_api, headers=headers)
        if r.status_code == 200:
            msg = f"[ERROR] Helm chart release already exists in the GitHub Release/Tag: {tag_name}"
            raise ReleaseTagError(msg)


@dataclass
class Report:
    found: bool = False
    signed: bool = False
    path: str = None


@dataclass
class Source:
    found: bool = False
    path: str = None  # Path to the Chart.yaml


@dataclass
class Tarball:
    found: bool = False
    path: str = None
    provenance: str = None


@dataclass
class Submission:
    """Represents a GitHub PR, opened to either certify a new Helm chart or add / modify an OWNERS file.

    A Submission can be instantiated either:
    * by solely providing the URL of a given PR (represented by the api_url attribute). Upon
    initialization (see __post_init__ method), the rest of the information is retrieved from the
    GitHub API. This should typically occur once per pipeline run, at the start.
    * by providing all class attributes. This is typically done by loading a JSON representation of
    a Submission from a file, and should be done several times per pipeline runs, in later jobs.

    """

    api_url: str
    modified_files: list[str] = None
    chart: Chart = field(default_factory=lambda: Chart())
    report: Report = field(default_factory=lambda: Report())
    source: Source = field(default_factory=lambda: Source())
    tarball: Tarball = field(default_factory=lambda: Tarball())
    modified_owners: list[str] = field(default_factory=list)
    modified_unknown: list[str] = field(default_factory=list)
    is_web_catalog_only: bool = None

    def __post_init__(self):
        """Complete the initialization of the Submission object.

        Only retrieve PR information from the GitHub API if requiered, by checking for the presence
        of a value for the modified_files attributes. This check allows to make the distinction
        between the two aforementioned cases of initialization of a Submission object:
        * If modified_files is not set, we're in the case of initializing a brand new Submission
        and need to retrieve the rest of the information from the GitHub API.
        * If a value is set for modified_files, that means we are loading an existing Submission
        object from a file.

        """
        if not self.modified_files:
            self.modified_files = []
            self._get_modified_files()
            self._parse_modified_files()

    def _get_modified_files(self):
        """Query the GitHub API in order to retrieve the list of files that are added / modified by
        this PR"""
        page_number = 1
        max_page_size, page_size = 100, 100
        files_api_url = re.sub(r"^https://api\.github\.com/", "", self.api_url)

        while page_size == max_page_size:
            files_api_query = (
                f"{files_api_url}/files?per_page={page_size}&page={page_number}"
            )
            print(f"[INFO] Query files : {files_api_query}")

            try:
                r = gitutils.github_api(
                    "get", files_api_query, os.environ.get("BOT_TOKEN")
                )
            except SystemExit as e:
                raise SubmissionError(e)

            files = r.json()
            page_size = len(files)
            page_number += 1

            if xRateLimit in r.headers:
                print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
            if xRateRemain in r.headers:
                print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

            if "message" in files:
                msg = f'[ERROR] getting pr files: {files["message"]}'
                raise SubmissionError(msg)
            else:
                for file in files:
                    if "filename" in file:
                        self.modified_files.append(file["filename"])

    def _parse_modified_files(self):
        """Classify the list of modified files.

        Modified files are categorized into 5 groups, mapping to 5 class attributes:
        - The `report` attribute has information about files related to the chart-verifier report:
        the report.yaml itself and, if signed, its signature report.yaml.asc.
        - The `source` attribute has information about files related to the chart's source: all
        files, if any, under the src/ directory.
        - The `tarball` attribute has information about files related to the chart's source as
        tarball: the .tgz tarball itself and, if signed, the .prov provenance file.
        - A list of added / modified OWNERS files is recorded in the `modified_owners` attribute.
        - The rest of the files are classified in the `modified_unknown` attribute.

        Raises a SubmissionError if:
        * The Submission concerns more than one chart
        * The version of the chart is not SemVer compatible
        * The tarball file is named incorrectly

        """
        for file_path in self.modified_files:
            file_category, match = get_file_type(file_path)
            if file_category == "report":
                self.chart.register_chart_info(*match.groups())
                self.set_report(file_path)
            elif file_category == "source":
                self.chart.register_chart_info(*match.groups())
                self.set_source(file_path)
            elif file_category == "tarball":
                category, organization, name, version, _ = match.groups()
                self.chart.register_chart_info(category, organization, name, version)
                self.set_tarball(file_path, match)
            elif file_category == "owners":
                self.modified_owners.append(file_path)
            elif file_category == "unknwown":
                self.modified_unknown.append(file_path)

    def set_report(self, file_path):
        """Action to take when a file related to the chart-verifier is found.

        This can either be the report.yaml itself, or the signing key report.yaml.asc

        """
        if os.path.basename(file_path) == "report.yaml":
            print(f"[INFO] Report found: {file_path}")
            self.report.found = True
            self.report.path = file_path
        elif os.path.basename(file_path) == "report.yaml.asc":
            self.report.signed = True
        else:
            self.modified_unknown.append(file_path)

    def set_source(self, file_path):
        """Action to take when a file related to the chart's source is found.

        Note that while the source of the Chart can be composed of many files, only the Chart.yaml
        is actually registered.

        """
        if os.path.basename(file_path) == "Chart.yaml":
            self.source.found = True
            self.source.path = file_path

    def set_tarball(self, file_path, tarball_match):
        """Action to take when a file related to the tarball is found.

        This can either be the .tgz tarball itself, or the .prov provenance key.

        """
        _, file_extension = os.path.splitext(file_path)
        if file_extension == ".tgz":
            print(f"[INFO] tarball found: {file_path}")
            self.tarball.found = True
            self.tarball.path = file_path

            _, _, chart_name, chart_version, tar_name = tarball_match.groups()
            expected_tar_name = f"{chart_name}-{chart_version}.tgz"
            if tar_name != expected_tar_name:
                msg = f"[ERROR] the tgz file is named incorrectly. Expected: {expected_tar_name}. Got: {tar_name}"
                raise SubmissionError(msg)
        elif file_extension == ".prov":
            self.tarball.provenance = file_path
        else:
            self.modified_unknown.append(file_path)

    def is_valid_certification_submission(self):
        """Check wether the files in this Submission are valid to attempt to certify a Chart

        We expect the user to provide either:
        * Only a report file
        * Only a chart - either as source or tarball
        * Both the report and the chart

        Returns False if:
        * The user attempts to create the OWNERS file for its project.
        * The PR contains additional files, not related to the Chart being submitted

        Returns True in all other cases

        """
        if self.modified_owners:
            return False, "[ERROR] Send OWNERS file by itself in a separate PR."

        if self.modified_unknown:
            msg = (
                "[ERROR] PR includes one or more files not related to charts: "
                + ", ".join(self.modified_unknown)
            )
            return False, msg

        if self.report.found or self.source.found or self.tarball.found:
            return True, ""

        return False, ""

    def is_valid_owners_submission(self):
        """Check wether the file in this Submission are valid for an OWNERS PR

        Returns True if the PR only modified files is an OWNERS file.

        Returns False in all other cases.
        """
        if len(self.modified_owners) == 1 and len(self.modified_files) == 1:
            return True, ""

        msg = ""
        if self.modified_owners:
            msg = "[ERROR] Send OWNERS file by itself in a separate PR."
        else:
            msg = "No OWNERS file provided"

        return False, msg

    def parse_web_catalog_only(self, repo_path=""):
        """Set the web_catalog_only attribute

        This is achieved by:
        - Parsing the associated OWNERS file and check the value of the WebCatalogOnly key
        - Parsing report file (if submitted) and check the value of the WebCatalogOnly key

        Args:
            repo_path (str): path under which the repo has been cloned on the local filesystem

        Returns:
            bool: True if WebCatalog is set to True in both the OWNERS and in the report file.
                  False if WebCatalogOnly is set to False in the OWNERS file

        Raise:
            WebCatalogOnlyError in one of the following cases:
            * The OWNERS file doesn't exist at the expected path
            * The OWNERS file doesn't contain WebCatalogOnly
            * The submitted report cannot be found or read at the expected path (although
              report.found is set to True)
            * The submitted report doesn't contain WebCatalogOnly
            * The WebCatalogOnly key don't match between the OWNERS and the report files

        """
        owners_path = os.path.join(repo_path, self.chart.get_owners_path())

        try:
            owners_data = owners_file.get_owner_data_from_file(owners_path)
        except owners_file.OwnersFileError as e:
            raise WebCatalogOnlyError(
                f"Failed to get OWNERS data at {owners_path}"
            ) from e

        try:
            owners_web_catalog_only = owners_file.get_web_catalog_only(
                owners_data, raise_if_missing=True
            )
        except owners_file.ConfigKeyMissing as e:
            raise WebCatalogOnlyError(
                f"Failed to find webCatalogOnly key in OWNERS data at {owners_path}"
            ) from e

        if self.report.found:
            report_path = os.path.join(repo_path, self.report.path)

            found, report_data = verifier_report.get_report_data(report_path)
            if not found:
                raise WebCatalogOnlyError(f"Failed to get report data at {report_path}")

            try:
                report_web_catalog_only = verifier_report.get_web_catalog_only(
                    report_data, raise_if_missing=True
                )
            except verifier_report.ConfigKeyMissing as e:
                raise WebCatalogOnlyError(
                    f"Failed to find webCatalogOnly key in report data at {owners_path}"
                ) from e
            print(
                f"[INFO] webCatalogOnly/providerDelivery from report : {report_web_catalog_only}"
            )

            if not owners_web_catalog_only == report_web_catalog_only:
                raise WebCatalogOnlyError(
                    f"Value of web_catalog_only in OWNERS ({owners_web_catalog_only}) doesn't match the value in report ({report_web_catalog_only})"
                )

        self.is_web_catalog_only = owners_web_catalog_only

    def is_valid_web_catalog_only(self, repo_path=""):
        """Verify that the submission is coherent with being a WebCatalogOnly submission

        A valid web_catalog_only submission must:
        * contain only a report
        * the report must specify a package digest

        Args:
            repo_path (str): path under which the repo has been cloned on the local filesystem

        Returns:
            bool: set to True if the submission is a valid WebCatalogOnly submission.

        Raise:
            WebCatalogOnlyError if the submitted report cannot be found or read at the expected path.

        """
        if not self.report.found:
            return False

        if len(self.modified_files) > 1:
            return False

        report_path = os.path.join(repo_path, self.report.path)
        found, report_data = verifier_report.get_report_data(report_path)
        if not found:
            raise WebCatalogOnlyError(f"Failed to get report data at {report_path}")

        return verifier_report.get_package_digest(report_data) is not None


def get_file_type(file_path):
    """Determine the category of a given file

    As part of a PR, a modified file can relate to one of 5 categories:
    - The chart-verifier report
    - The source of the chart
    - The tarball of the chart
    - OWNERS file
    - or another "unknown" category

    """
    pattern, reportpattern, tarballpattern = checkpr.get_file_match_compiled_patterns()
    owners_pattern = re.compile(
        matchers.submission_path_matcher(include_version_matcher=False) + r"/OWNERS"
    )
    src_pattern = re.compile(matchers.submission_path_matcher() + r"/src/")

    # Match all files under charts/<category>/<organization>/<name>/<version>
    match = pattern.match(file_path)
    if match:
        report_match = reportpattern.match(file_path)
        if report_match:
            return "report", report_match

        src_match = src_pattern.match(file_path)
        if src_match:
            return "source", src_match

        tar_match = tarballpattern.match(file_path)
        if tar_match:
            return "tarball", tar_match
    else:
        owners_match = owners_pattern.match(file_path)
        if owners_match:
            return "owners", owners_match

    return "unknwown", None


def download_index_data(repository, branch="gh_pages"):
    """Download the helm repository index"""
    r = requests.get(
        f"https://raw.githubusercontent.com/{repository}/{branch}/index.yaml"
    )

    if r.status_code == 200:
        data = yaml.load(r.text, Loader=Loader)
    else:
        data = {}

    return data
