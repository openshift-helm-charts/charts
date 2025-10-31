from dataclasses import dataclass, field
import os
import re
import tarfile

import requests
import semver
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


from owners import owners_file
from tools import gitutils
from reporegex import matchers
from report import verifier_report

xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"
REQUEST_TIMEOUT = 10


class SubmissionError(Exception):
    """Root exception for handling any error with the submission"""


class DuplicateChartError(SubmissionError):
    """This exception is raised when the user attempts to submit a PR with more than one chart"""


class VersionError(SubmissionError):
    """This exception is raised when the version of the chart is not semver compatible"""


class WebCatalogOnlyError(SubmissionError):
    """This exception is raised when there is an error when determining the WebCatalogOnly attribute
    or if it is inconsistently set

    """


class HelmIndexError(SubmissionError):
    """This exception is raised when the chart is already present in the index, or if there was an error
    downloading or reading the helm index

    """


class ReleaseTagError(SubmissionError):
    """This exception is raised when the chart's release already exists"""


class ChartError(SubmissionError):
    """This exception is raised when the redhat prefix is incorrectly set"""


class TarballContentError(SubmissionError):
    """This exception is raised when checking the provided tarball content"""


@dataclass
class Chart:
    """Represents a Helm Chart

    Once set, the category, organization, name and version of the chart cannot be modified.

    """

    category: str = None
    organization: str = None
    name: str = None
    version: str = None

    def register_chart_info(
        self, category: str, organization: str, name: str, version: str = None
    ):
        """Initialize the chart's category, organization, name and version

        Providing a version is not mandatory. In case of a Submission that only contains an OWNERS
        file, a version is not present.

        This function ensures that once set, the chart's information are not modified, as a PR must
        only relate to a unique chart.

        Args:
            category (str): Type of profile (community, partners, or redhat)
            organization (str): Name of the organization (ex: hashicorp)
            chart (str): Name of the chart (ex: vault)
            version (str): The version of the chart (ex: 1.4.0)

        Raises:
            DuplicateChartError if the caller attempts to modify the chart's information
            ChartError if the redhat prefix is incorrectly set
            VersionError if the provided version is not semver compatible

        """
        if (
            (self.category and self.category != category)
            or (self.organization and self.organization != organization)
            or (self.name and self.name != name)
            or (self.version and self.version != version)
        ):
            msg = "[ERROR] A PR must contain only one chart. Current PR includes files for multiple charts."
            raise DuplicateChartError(msg)

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

        if version:
            if not semver.VersionInfo.is_valid(version):
                msg = f"[ERROR] Helm chart version is not a valid semantic version: {version}"
                raise VersionError(msg)

            self.version = version

    def get_owners_path(self) -> str:
        return f"charts/{self.category}/{self.organization}/{self.name}/OWNERS"

    def get_vendor_type(self) -> str:
        """Derive the vendor type from the chart's category."""
        if self.category == "partners":
            return "partner"
        return self.category

    def get_release_tag(self) -> str:
        return f"{self.organization}-{self.name}-{self.version}"

    def check_index(self, index: dict):
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
        r = requests.head(tag_api, headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            msg = f"[ERROR] Helm chart release already exists in the GitHub Release/Tag: {tag_name}"
            raise ReleaseTagError(msg)


@dataclass
class Report:
    """Contains metadata about the report.yaml"""

    # Whether the PR contains a report.yaml
    found: bool = False
    # Whether the report.yaml is signed (signaled by the presence or absence of report.yaml.asc)
    signed: bool = False
    # The path to the report.yaml, e.g. charts/parnters/hashicorp/vault/0.29.1/report.yaml
    path: str = None


@dataclass
class Source:
    """Contains metadata about the chart's source"""

    # Whether the PR contains the Helm chart's source
    found: bool = False
    # The path to the base directory containing the source, e.g. charts/parnters/hashicorp/vault/0.29.1/src
    path: str = None


@dataclass
class Tarball:
    """Contains metadata about the tarball"""

    # Whether the PR contains a tarball
    found: bool = False
    # The path to the tarball, e.g. charts/parnters/hashicorp/vault/0.29.1/vault-0.29.1.tgz
    path: str = None
    # The name of the provenance file, if provided
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
    chart: Chart = field(default_factory=Chart)
    report: Report = field(default_factory=Report)
    source: Source = field(default_factory=Source)
    tarball: Tarball = field(default_factory=Tarball)
    modified_owners: list[str] = field(default_factory=list)
    modified_unknown: list[str] = field(default_factory=list)
    is_web_catalog_only: bool = None

    def __post_init__(self):
        """Complete the initialization of the Submission object.

        Only retrieve PR information from the GitHub API if required, by checking for the presence
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
                raise SubmissionError(e) from e

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

    def parse_modified_files(self, repo_path: str = ""):
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

        Args:
            repo_path (str): Local directory where the repo is checked out

        Raises a SubmissionError if:
        * The PR doesn't contain any files
        * The Submission concerns more than one chart
        * The version of the chart is not SemVer compatible
        * The tarball file is named incorrectly
        * The tarball content is incorrect

        """
        if not self.modified_files:
            msg = "PR doesn't contain any files"
            raise SubmissionError(msg)

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
                self.set_tarball(file_path, match, repo_path)
            elif file_category == "owners":
                category, organization, name = match.groups()
                self.chart.register_chart_info(category, organization, name)
                self.modified_owners.append(file_path)
            elif file_category == "unknown":
                self.modified_unknown.append(file_path)

    def set_report(self, file_path: str):
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

    def set_source(self, file_path: str):
        """Action to take when a file related to the chart's source is found.

        Note that while the source of the Chart can be composed of many files, only the Chart.yaml
        is actually registered.

        """
        if os.path.basename(file_path) == "Chart.yaml":
            self.source.found = True
            self.source.path = os.path.dirname(file_path)

    def set_tarball(
        self, file_path: str, tarball_match: re.Match[str], repo_path: str = ""
    ):
        """Action to take when a file related to the tarball is found.

        This can either be the .tgz tarball itself, or the .prov provenance key.

        Args:
            file_path (str): File that has been potentially detected as the tarball or the provenance file.
            tarball_match (re.Match[str]): Matching regex, used to get the chart name and version and the tarball name.
            repo_path (str): Local directory where the repo is checked out

        Raises:
            SubmissionError: If the tarball is incorrectly named
            TarballContentError: If an error is found when checking the tarball content

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

            # Raise a TarballContentError if content check fails
            check_tarball_content(os.path.join(repo_path, file_path), chart_name)

        elif file_extension == ".prov":
            self.tarball.provenance = file_path
        else:
            self.modified_unknown.append(file_path)

    def is_valid_certification_submission(
        self, ignore_owners: bool = False
    ) -> tuple[bool, str]:
        """Check whether the files in this Submission are valid to attempt to certify a Chart

        We expect the user to provide either:
        * Only a report file
        * Only a chart - either as source or tarball
        * Both the report and the chart

        Note: While an OWNERS file should never be present in this type of submission, the case of
        an invalid Submission containing a mix of OWNERS and other files is handled in the
        is_valid_owners_submission method. The flag "ignore_owners" allows for skipping this
        specific check.

        Returns False if:
        * The user attempts to create the OWNERS file for its project.
        * The PR contains additional files, not related to the Chart being submitted

        Returns True in all other cases

        """
        if self.modified_owners and not ignore_owners:
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

    def is_valid_owners_submission(self) -> tuple[bool, str]:
        """Check whether the files in this Submission are valid for an OWNERS PR

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

    def parse_web_catalog_only(self, repo_path: str = ""):
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
        except owners_file.ConfigKeyMissing:
            print(
                f"[INFO] webCatalogOnly key not found in OWNERS data at {owners_path}. Assuming False"
            )
            owners_web_catalog_only = False
        else:
            print(
                f"[INFO] webCatalogOnly/providerDelivery from OWNERS : {owners_web_catalog_only}"
            )

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
                if owners_web_catalog_only:
                    raise WebCatalogOnlyError(
                        "[ERROR] The web catalog distribution method is set for the chart but is not set in the report."
                    )
                if report_web_catalog_only:
                    raise WebCatalogOnlyError(
                        "[ERROR] Report indicates web catalog only but the distribution method set for the chart is not web catalog only."
                    )

        self.is_web_catalog_only = owners_web_catalog_only

    def is_valid_web_catalog_only(self, repo_path: str = "") -> tuple[bool, str]:
        """Verify that the submission is coherent with being a WebCatalogOnly submission

        A valid web_catalog_only submission must:
        * contain only a report
        * the report must specify a package digest

        Args:
            repo_path (str): path under which the repo has been cloned on the local filesystem

        Returns:
            (bool, str): set to True if the submission is a valid WebCatalogOnly submission.
                         set to False otherwise, with the corresponding error message.

        Raise:
            WebCatalogOnlyError if the submitted report cannot be found or read at the expected path.

        """
        # (mgoerens) There are currently no end to end tests that checks for this scenario
        if not self.report.found:
            return (
                False,
                "[ERROR] The web catalog distribution method requires the pull request to contain a report.",
            )

        if len(self.modified_files) > 1:
            msg = "[ERROR] The web catalog distribution method requires the pull request to be report only."
            return False, msg

        report_path = os.path.join(repo_path, self.report.path)
        found, report_data = verifier_report.get_report_data(report_path)
        if not found:
            raise WebCatalogOnlyError(f"Failed to get report data at {report_path}")

        if verifier_report.get_package_digest(report_data) is None:
            return (
                False,
                "[ERROR] The web catalog distribution method requires a package digest in the report.",
            )

        return True, ""

    def get_pr_number(self):
        return self.api_url.split("/")[-1]


def get_file_type(file_path: str) -> tuple[str, re.Match[str]]:
    """Determine the category of a given file

    As part of a PR, a modified file can relate to one of 5 categories:
    - The chart-verifier report
    - The source of the chart
    - The tarball of the chart
    - OWNERS file
    - or another "unknown" category

    """
    pattern, reportpattern, tarballpattern = matchers.get_file_match_compiled_patterns()
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

    return "unknown", None


def download_index_data(
    repository: str, branch: str = "gh-pages", ignore_missing: bool = False
) -> dict:
    """Download the helm repository index

    Args:
        repository (str): Name of the GitHub repository to download the index file from.
                            (e.g. "openshift-helm-charts/charts")
        branch (str): GitHub branch to download the index file from. Defaults to "gh-pages".
        ignore_missing (bool): Set to True to return a valid empty index, in the case the
                            download of index.yaml fails.

    Returns:
        dict: The helm repository index

    Raise:
        HelmIndexError if the download fails. If not on the production repository, doesn't raise
            and returns an empty index file instead.
        HelmIndexError if the index file is not valid YAML.

    """
    index_url = f"https://raw.githubusercontent.com/{repository}/{branch}/index.yaml"
    r = requests.get(index_url, timeout=REQUEST_TIMEOUT)

    data = {"apiVersion": "v1", "entries": {}}
    if r.status_code != 200:
        if not ignore_missing:
            raise HelmIndexError(f"Error retrieving index file at {index_url}")
    else:
        try:
            data = yaml.load(r.text, Loader=Loader)
        except yaml.YAMLError as e:
            raise HelmIndexError(f"Error parsing index file at {index_url}") from e

    return data


def check_tarball_content(tarball_path: str, chart_name: str):
    """Check the tarball content for errors.

    Checks that the tarball contains a unique directory named after the chart. This directory must contain a Chart.yaml
    file. The directory may contain additional files or folders. No other files or folder should be placed at the root
    of the archive.

    Args:
        tarball_path (str): Location of the tarball to check on the local filesystem.
        chart_name (str): Name of the corresponding chart.

    Raise:
        TarballContentError: If an error is found when checking the tarball content

    """
    found_chart_directory = False
    found_chart_yaml = False
    found_file_out_of_dir = False
    expected_chart_file_path = os.path.join(chart_name, "Chart.yaml")
    with tarfile.open(tarball_path, "r:gz") as tar:
        tarinfo = tar.next()
        while tarinfo:
            if (
                tarinfo.isdir() and tarinfo.name == chart_name
            ) or tarinfo.name.startswith(chart_name + "/"):
                found_chart_directory = True
                if tarinfo.isfile() and tarinfo.name == expected_chart_file_path:
                    found_chart_yaml = True
            else:
                found_file_out_of_dir = True
            tarinfo = tar.next()

    if not found_chart_directory:
        msg = f"[ERROR] Incorrect tarball content: expected a {chart_name} directory"
        raise TarballContentError(msg)

    if found_file_out_of_dir:
        msg = f"[ERROR] Incorrect tarball content: found a file outside the {chart_name} directory"
        raise TarballContentError(msg)

    if not found_chart_yaml:
        msg = f"[ERROR] Incorrect tarball content: expected a {expected_chart_file_path} file"
        raise TarballContentError(msg)
