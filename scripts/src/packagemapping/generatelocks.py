import re
import sys
from datetime import datetime, timezone
from glob import glob
from json import dumps as to_json

from owners import owners_file


def ownerfile_regex():
    """Return a regex statement that parses relative filepaths of an OWNERS file.

    The filepath is expected to be from the charts directory forward.

    Returns:
        The compiled regex that groups the category, organization, and chart name.

        E.g. category | organization | chartname
             partner  | hashicorp    | vault
    """

    pattern = re.compile(r"charts/(partners|redhat|community)/([\w-]+)/([\w-]+)/OWNERS")
    return pattern


def logError(msg, file=sys.stderr):
    """logError just prints the msg with an ERROR caption to stderr unless otherwise defined"""
    print(f"[ERROR] {msg}", file=file)


def logInfo(msg, file=sys.stderr):
    """logError just prints the msg with an INFO caption to stderr unless otherwise defined"""
    print(f"[INFO] {msg}", file=file)


def logWarn(msg, file=sys.stderr):
    """logWarn just prints the msg with an WARN caption to stderr unless otherwise defined"""
    print(f"[WARN] {msg}", file=file)


def main():
    """Generates a mapping of chart names to their associated paths.

    Prints the resulting output as a JSON blob.

    Return codes:
        0:  All is well.
        10: Parsing failure for the input path to a given OWNERS file.
        20: One of the expected directory values is empty.
        30: The OWNERS file at the provided path did not load correctly.
        35: The OWNERS file content and the directory structure are mismatched.
        40: A duplicate chart name entry has been found.
        50: The resulting data contained no entries, which
            is certainly unexpected.
    """
    packages = {}
    for filename in glob("charts/**/OWNERS", recursive=True):
        logInfo(f"processing file {filename}")
        pattern = ownerfile_regex()
        matched = pattern.match(filename)
        if matched is None:
            logError(
                f"did not successfully parse the input. Did you run this in the right place? filename: {filename}",
            )
            return 10

        category, organization, chart = matched.groups()
        if category is None or organization is None or chart is None:
            logError(
                f"did not successfully parse the input filename: {filename}",
                "expecting format charts/{category}/{organization}/{chartname}/OWNERS. Did you run this in the right place?",
            )
            return 20

        try:
            owners_content = owners_file.get_owner_data_from_file(filename)
        except owners_file.OwnersFileError as of_err:
            logError(
                f"Failed to load OWNERS file content. filename: {filename} with error {of_err}"
            )
            return 30

        owners_value_chart_name = owners_file.get_chart(owners_content)
        owners_value_vendor_label = owners_file.get_vendor_label(owners_content)

        if owners_value_chart_name != chart:
            logError(
                f"the chart name in the OWNERS file did not match the chart name directory structure. OWNERS_FILE_VALUE={owners_value_chart_name}, DIRECTORY_VALUE:{chart}"
            )
            return 35

        if owners_value_vendor_label != organization:
            logError(
                f"the vendor label in the OWNERS file did not match the organization name directory structure. OWNERS_FILE_VALUE={owners_value_chart_name}, DIRECTORY_VALUE:{chart}"
            )
            return 35

        new_entry = f"{category}/{organization}/{chart}"
        if packages.get(chart) is not None:
            logError(
                f"Duplicate chart name detected. Unable to build unique package list. trying to add: {new_entry}, current_value: {packages[chart]}"
            )
            return 40

        packages[chart] = new_entry

    if len(packages.keys()) == 0:
        logError("the package map contained no items!")
        return 50

    now = datetime.now(timezone.utc).astimezone().isoformat()

    print(
        to_json(
            {
                "generated": now,
                "packages": packages,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
