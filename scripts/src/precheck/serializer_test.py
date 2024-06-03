import json

from precheck import serializer
from precheck import submission

submission_json = """
{
    "api_url": "https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
    "modified_files": ["charts/partners/acme/awesome/1.42.0/report.yaml"],
    "chart": {
        "category": "partners",
        "organization": "acme",
        "name": "awesome",
        "version": "1.42.0"
    },
    "report": {
        "found": true,
        "signed": false,
        "path": "charts/partners/acme/awesome/1.42.0/report.yaml"
    },
    "source": {
        "found": false,
        "path": null
    },
    "tarball": {
        "found": false,
        "path": null,
        "provenance": null
    },
    "modified_owners": [],
    "modified_unknown": [],
    "is_web_catalog_only": true
}
"""


def sanitize_json_string(json_string: str):
    """Remove the newlines from the JSON string. This is done by
    loading and dumping the string representation of the JSON object.
    Goal is to allow comparison with other JSON string.
    """
    json_dict = json.loads(json_string)
    return json.dumps(json_dict)


def test_submission_serializer():
    s = json.loads(submission_json, cls=serializer.SubmissionDecoder)

    assert isinstance(s, submission.Submission)
    assert (
        s.api_url == "https://api.github.com/repos/openshift-helm-charts/charts/pulls/1"
    )
    assert "charts/partners/acme/awesome/1.42.0/report.yaml" in s.modified_files
    assert s.chart.category == "partners"
    assert s.chart.organization == "acme"
    assert s.chart.name == "awesome"
    assert s.chart.version == "1.42.0"
    assert s.report.found
    assert not s.report.signed
    assert s.report.path == "charts/partners/acme/awesome/1.42.0/report.yaml"
    assert not s.source.found
    assert not s.source.path
    assert not s.tarball.found
    assert not s.tarball.path
    assert not s.tarball.provenance
    assert s.is_web_catalog_only


def test_submission_deserializer():
    s = submission.Submission(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
        modified_files=["charts/partners/acme/awesome/1.42.0/report.yaml"],
        chart=submission.Chart(
            category="partners",
            organization="acme",
            name="awesome",
            version="1.42.0",
        ),
        report=submission.Report(
            found=True,
            signed=False,
            path="charts/partners/acme/awesome/1.42.0/report.yaml",
        ),
        source=submission.Source(
            found=False,
            path=None,
        ),
        tarball=submission.Tarball(
            found=False,
            path=None,
            provenance=None,
        ),
        is_web_catalog_only=True,
    )

    assert serializer.SubmissionEncoder().encode(s) == sanitize_json_string(
        submission_json
    )
