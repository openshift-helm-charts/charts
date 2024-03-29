"""
Used by github actions,specifically as part of the charts auto release process defined in
.github/workflow/release.yml. Encapsulates the release_info.json file.

Provides get functions for all data in the release_info.json file.
"""

import json
import os

RELEASE_INFO_FILE = "release/release_info.json"

RELEASE_INFOS = {}


def _get_release_info(directory):
    global RELEASE_INFOS

    if not directory:
        directory = "./"

    root_dir = os.path.dirname(f"{os.getcwd()}/{directory}")

    if root_dir not in RELEASE_INFOS:
        print(f"Open release_info file: {root_dir}/{RELEASE_INFO_FILE}")

        with open(f"{root_dir}/{RELEASE_INFO_FILE}", "r") as json_file:
            RELEASE_INFOS[root_dir] = json.load(json_file)

    return RELEASE_INFOS[root_dir]


def get_version(directory):
    info = _get_release_info(directory)
    return info["version"]


def get_info(directory):
    info = _get_release_info(directory)
    return info["info"]


def get_replaces(from_repo, to_repo, directory):
    print(f"get replaces for {from_repo} to {to_repo} ")
    info = _get_release_info(directory)
    if from_repo in info:
        if "replace" in info[from_repo][to_repo]:
            print(f"replaces found: {info[from_repo][to_repo]['replace']}")
            return info[from_repo][to_repo]["replace"]
    print("no replaces found")
    return []


def get_merges(from_repo, to_repo, directory):
    print(f"get merges for {from_repo} to {to_repo}")
    info = _get_release_info(directory)
    if from_repo in info:
        if "merge" in info[from_repo][to_repo]:
            print(f"merges found: {info[from_repo][to_repo]['merge']}")
            return info[from_repo][to_repo]["merge"]
    print("no merges found")
    return []


def get_ignores(from_repo, to_repo, directory):
    print(f"get ignores for {from_repo} to {to_repo}")
    info = _get_release_info(directory)
    if from_repo in info:
        if "ignore" in info[from_repo][to_repo]:
            print(f"ignores found: {info[from_repo][to_repo]['ignore']}")
            return info[from_repo][to_repo]["ignore"]
    print("no ignores found")
    return []


def main():
    print(f"[INFO] Version : {get_version('.')}")

    # from development to charts
    print(
        f"[INFO] Dev to charts repo merges : {get_merges('development','charts','.')}"
    )

    print(
        f"[INFO] Dev to charts repo replace : {get_replaces('development','charts','.')}"
    )

    print(
        f"[INFO] Dev to charts repo ignore : {get_ignores('development','charts','.')}"
    )

    # from development to stage
    print(f"[INFO] Dev to stage repo merges : {get_merges('development','stage','.')}")

    print(
        f"[INFO] Dev to stage repo replace : {get_replaces('development','stage','.')}"
    )

    print(f"[INFO] Dev to stage repo ignore : {get_ignores('development','stage','.')}")

    # From charts to development
    print(f"[INFO] Chart to dev repo merges : {get_merges('charts','development','.')}")

    print(
        f"[INFO] Chart to dev repo replace : {get_replaces('charts','development','.')}"
    )

    print(
        f"[INFO] Chart to dev repo ignore : {get_ignores('charts','development','.')}"
    )


if __name__ == "__main__":
    main()
