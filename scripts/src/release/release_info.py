"""
Used by github actions,specifically as part of the charts auto release process defined in
.github/workflow/release.yml. Encapsulates the release_info.json file.

Provides get functions for all data in the release_info.json file.
"""
import json
import os


RELEASE_INFO_FILE="release/release_info.json"

RELEASE_INFOS = {}

def _get_release_info(directory):

    global RELEASE_INFOS

    if not directory:
        directory = "./"

    root_dir = os.path.dirname(f"{os.getcwd()}/{directory}")

    if not root_dir in RELEASE_INFOS:

        print(f"Open release_info file: {root_dir}/{RELEASE_INFO_FILE}")

        with open(f"{root_dir}/{RELEASE_INFO_FILE}",'r') as json_file:
            RELEASE_INFOS[root_dir] = json.load(json_file)

    return RELEASE_INFOS[root_dir]

def get_version(directory):
    info = _get_release_info(directory)
    return info["version"]

def get_info(directory):
    info = _get_release_info(directory)
    return info["info"]


def get_replaces(repo,directory):
    print(f"get replaces for {repo}")
    info = _get_release_info(directory)
    if repo in info:
        if "replace" in info[repo]:
            print(f"replaces found: {info[repo]['replace']}")
            return info[repo]["replace"]
    print("no replaces found")
    return []

def get_merges(repo,directory):
    print(f"get merges for {repo}")
    info = _get_release_info(directory)
    if repo in info:
        if "merge" in info[repo]:
            print(f"merges found: {info[repo]['merge']}")
            return info[repo]["merge"]
    print("no merges found")
    return []


def get_ignores(repo,directory):
    print(f"get ignores for {repo}")
    info = _get_release_info(directory)
    if repo in info:
        if "ignore" in info[repo]:
            print(f"ignores found: {info[repo]['ignore']}")
            return info[repo]["ignore"]
    print("no ignores found")
    return []


def main():

    print(f"[INFO] Version : {get_version('.')}")

    print(f"[INFO] Dev repo merges : {get_merges('development','.')}")

    print(f"[INFO] Dev repo replace : {get_replaces('development','.')}")

    print(f"[INFO] Dev repo ignore : {get_ignores('development','.')}")

    print(f"[INFO] Chart repo merges : {get_merges('charts','.')}")

    print(f"[INFO] Chart repo replace : {get_replaces('charts','.')}")

    print(f"[INFO] Chart repo ignore : {get_ignores('charts','.')}")


if __name__ == "__main__":
    main()
