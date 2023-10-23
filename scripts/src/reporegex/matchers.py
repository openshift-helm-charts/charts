def submission_path_matcher(
    base_dir="charts", strict_categories=True, include_version_matcher=True
):
    """Returns a regex string with various submission-related groupings.

    The groupings returned (in order) are: category, organization, chart name,
    and optionally, version.

    Callers should append any relevant path matching to the end of the string
    returned from this function. E.g. "/.*"

    Args:
        base_dir: The base path of the expression statement. Should
          not be empty.
        strict_categories: Whether the category matcher should match only the
          relevant categories, or any word at all.
        include_version_matcher: Whether or not the version matcher should be
          appended. In some cases, the caller of this regex doesn't care about the
          versioning detail.

    Returns:
        A regular expression-compatible string with the mentioned groupings.
    """

    relaxedCategoryMatcher = "\w+"
    strictCategoryMatcher = "partners|redhat|community"

    categoryMatcher = (
        strictCategoryMatcher if strict_categories else relaxedCategoryMatcher
    )
    organizationMatcher = "[\w-]+"
    chartMatcher = "[\w-]+"
    versionMatcher = "[\w\.\-+]+"

    matcher = (
        rf"{base_dir}/({categoryMatcher})/({organizationMatcher})/({chartMatcher})"
    )
    if include_version_matcher:
        matcher += rf"/({versionMatcher})"

    return matcher
