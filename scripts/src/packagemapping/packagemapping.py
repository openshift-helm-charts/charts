from glob import glob, escape
import sys
import yaml
import re
from datetime import datetime, timezone
from json import dumps as to_json


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
    """logWarn just prints the msg with an INFO caption to stderr unless otherwise defined"""
    print(f"[WARN] {msg}", file=file)


def main():
    packages = {}
    for filename in glob("charts/**/OWNERS", recursive=True):
        logInfo(f"processing file {filename}")
        pattern = ownerfile_regex()
        matched = pattern.match(filename)
        if matched == None:
            # TODO(komish): Consider if we need to have a flag that exits and otherwise make this a warning
            # For now, we fail here because it means we have a an invalid directory path and therefore can't determine our
            # category, org, or repo from the path.
            logError(
                f"did not successfully parse the input. Did you run this in the right place? filename: {filename}",
            )
            # continue
            sys.exit(1)

        category, organization, chart = matched.groups()
        if category == None or organization == None or chart == None:
            logError(
                f"did not successfully parse the input filename: {filename}",
                "expecting format charts/{category}/{organization}/{chartname}/OWNERS. Did you run this in the right place?",
            )
            sys.exit(1)

        with open(filename, "r") as f:
            d = yaml.load(f.read(), Loader=yaml.BaseLoader)
            owners_value_chart_name = d["chart"]["name"]
            owners_value_vendor_label = d["vendor"]["label"]

        if owners_value_chart_name != chart:
            logError(
                f"the chart name in the OWNERS file did not match the chart name directory structure. OWNERS_FILE_VALUE={owners_value_chart_name}, DIRECTORY_VALUE:{chart}"
            )

        if owners_value_vendor_label != organization:
            logError(
                f"the vendor label in the OWNERS file did not match the organization name directory structure. OWNERS_FILE_VALUE={owners_value_chart_name}, DIRECTORY_VALUE:{chart}"
            )

        new_entry = f"{category}/{organization}/{chart}"
        if packages.get(chart, None) != None:
            logError(
                f"Duplicate chart name detected. Unable to build unique package list. trying to add: {new_entry}, current_value: {packages[chart]}"
            )
            sys.exit(2)

        packages[chart] = new_entry

    if len(packages.keys()) == 0:
        logError("the package map contained no items!")
        sys.exit(3)

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
