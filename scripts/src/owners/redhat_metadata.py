from argparse import ArgumentParser

from owners import owners_file

REQUIRED_VENDOR_LABEL = "redhat"
REQUIRED_VENDOR_NAME = "Red Hat"
REQUIRED_CHART_PREFIX = "redhat-"


class RedHatOwnersFileInvalidContentsError(Exception):
    message = "The OWNERS does not contain criteria required for Red Hatters"

    def __init__(self, message):
        if len(message) > 0:
            self.message = message

        super().__init__(self.message)


def assert_redhat_metadata(contents):
    """Ensures contents of owners file for Red Hat submissions

    Red Hat submissions are expected to have certain metadata.

    - The owner label must be "redhat"
    - The owner organizaton name must be "Red Hat"
    - The chart's name must be prefixed with "redhat-"

    This raises an exception if the metadata is incorrect.

    Args:
        contents: The contents of the owners
          file to be evaluated. This should have already
          been read from disk and yaml.loaded

    Raises:
        RedHatOwnersFileInvalidContentsError: In cases where the
          content is not as expected.

    Returns:
        Nothing.
    """

    if not owners_file.get_chart(contents).startswith(REQUIRED_CHART_PREFIX):
        raise RedHatOwnersFileInvalidContentsError(
            f"The chart name must be prefixed with '{REQUIRED_CHART_PREFIX}'."
        )

    if owners_file.get_vendor_label(contents) != REQUIRED_VENDOR_LABEL:
        raise RedHatOwnersFileInvalidContentsError(
            f"OWNERS file did not have expected vendor label: '{REQUIRED_VENDOR_LABEL}'"
        )

    if owners_file.get_vendor(contents) != REQUIRED_VENDOR_NAME:
        raise RedHatOwnersFileInvalidContentsError(
            f"OWNERS file did not have expected vendor name: '{REQUIRED_VENDOR_NAME}'"
        )


def main():
    """The CLI entrypoint.

    Return codes:
        0:  everything has gone well.
        10: The OWNERS file was not found.
        20: The OWNERS file has invalid content.
    """
    parser = ArgumentParser()
    parser.add_argument("category")
    parser.add_argument("organization")
    parser.add_argument("chartname")
    args = parser.parse_args()
    print(
        f"[Info] Checking OWNERS file content for {args.category}/{args.organization}/{args.chartname}"
    )

    ownerDataFound, ownerdata = owners_file.get_owner_data(
        args.category, args.organization, args.chartname
    )
    if not ownerDataFound:
        print("[Error] OWNERS file not found")
        return 10

    try:
        assert_redhat_metadata(ownerdata)
    except RedHatOwnersFileInvalidContentsError as e:
        print(f"[Error] Invalid contents, {e}")
        return 20

    print("[Info] LGTM!")
    return 0


if __name__ == "__main__":
    main()
