"""
Used within github actions, specifically as part of the charts auto release process defined in
.github/workflow/release.yml. Makes all of the changes required to both the chart and development repos.


parameters :
  --version : the Version of the the release being created.
  --pr_dir : the directory containing the PR contents. Used to get the release-info.jso file.
  --development_dir : the directory containing the latest version of the development repository.
  --charts_dir : the directory containing the latest version of the charts repository.

Performs these action.
- Gets a list of updates to perform from the pr_dir releases/release_info.json file. These updates are then made
to the charts and development repositories.
- Create a PR against the charts repo containing the workflow updates. This requires manual merge.
- Directly commits to the development main branch any new charts added to the charts repo since the last update.


"""

import argparse
import os
import shutil
import sys

from release import release_info

sys.path.append("../")
from tools import gitutils

BUILD_YAML_FILE = ".github/workflows/build.yml"
DEV_PR_BRANCH_BODY_PREFIX = "Charts workflow version"
DEV_PR_BRANCH_NAME_PREFIX = "Auto-Release-"
CHARTS_PR_BRANCH_BODY_PREFIX = "Workflow and script updates from development repository"
CHARTS_PR_BRANCH_NAME_PREFIX = "Release-"
STAGE_PR_BRANCH_BODY_PREFIX = "Workflow and script updates from development repository"
STAGE_PR_BRANCH_NAME_PREFIX = "Release-"


def make_required_changes(release_info_dir, origin, destination):
    print(f"Make required changes from {origin} to {destination}")

    if "charts" in origin and "dev" in destination:
        from_repository = "charts"
        to_repository = "development"
    elif "dev" in origin and "charts" in destination:
        from_repository = "development"
        to_repository = "charts"
    elif "dev" in origin and "stage" in destination:
        from_repository = "development"
        to_repository = "stage"
    else:
        sys.exit("Wrong arguments while calling make_required_changes")

    replaces = release_info.get_replaces(
        from_repository, to_repository, release_info_dir
    )

    for replace in replaces:
        replace_this = f"{destination}/{replace}"
        with_this = f"{origin}/{replace}"
        if os.path.isdir(with_this) or os.path.isdir(replace_this):
            print(f"Replace directory {replace_this} with {with_this}")
            if os.path.isdir(replace_this):
                shutil.rmtree(replace_this)
            shutil.copytree(with_this, replace_this)
        else:
            print(f"Replace file {replace_this} with {with_this}")
            shutil.copy2(with_this, replace_this)

    merges = release_info.get_merges(from_repository, to_repository, release_info_dir)

    for merge in merges:
        merge_this = f"{origin}/{merge}"
        into_this = f"{destination}/{merge}"

        if os.path.isdir(merge_this) or os.path.isdir(into_this):
            print(f"Merge directory {merge_this} with {into_this}")
            shutil.copytree(merge_this, into_this, dirs_exist_ok=True)
        else:
            print(f"Merge file {merge_this} with {into_this}")
            shutil.copy2(merge_this, into_this)

    ignores = release_info.get_ignores(from_repository, to_repository, release_info_dir)
    for ignore in ignores:
        ignore_this = f"{destination}/{ignore}"
        try:
            if os.path.isdir(ignore_this):
                print(f"Ignore/delete directory {ignore_this}")
                shutil.rmtree(ignore_this)
            else:
                print(f"Ignore/delete file {ignore_this}")
                os.remove(ignore_this)
        except FileNotFoundError as e:
            print(
                f"[INFO] path {ignore_this} is explicitly ignored but was not found when syncing {from_repository} to {to_repository}."
                + "This file can be removed from the ignore section of release_info.json"
            )
            continue


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        type=str,
        required=True,
        help="Version to compare",
    )
    parser.add_argument(
        "-d",
        "--development_dir",
        dest="dev_dir",
        type=str,
        required=True,
        help="Directory of development code with latest release info.",
    )
    parser.add_argument(
        "-c",
        "--charts_dir",
        dest="charts_dir",
        type=str,
        required=True,
        help="Directory of charts code.",
    )
    parser.add_argument(
        "-s",
        "--stage_dir",
        dest="stage_dir",
        type=str,
        required=True,
        help="Directory of stage code.",
    )
    parser.add_argument(
        "-p",
        "--pr_dir",
        dest="pr_dir",
        type=str,
        required=True,
        help="Directory of pull request code.",
    )
    parser.add_argument(
        "-b",
        "--dev_pr_body",
        dest="dev_pr_body",
        type=str,
        required=True,
        help="Body to use for the dev PR",
    )
    parser.add_argument(
        "-t",
        "--target_branch",
        dest="target_branch",
        type=str,
        required=True,
        help="Target branch of the Pull Request",
    )
    parser.add_argument(
        "-r",
        "--target_repository",
        dest="target_repository",
        type=str,
        required=True,
        help="Repository which is the target of the pull request",
    )

    args = parser.parse_args()

    print("[INFO] releaser inputs:")
    print(f"[INFO] arg version : {args.version}")
    print(f"[INFO] arg dev_dir : {args.dev_dir}")
    print(f"[INFO] arg charts_dir : {args.charts_dir}")
    print(f"[INFO] arg stage_dir : {args.stage_dir}")
    print(f"[INFO] arg pr_dir : {args.pr_dir}")
    print(f"[INFO] arg dev_pr_body : {args.dev_pr_body}")
    print(f"[INFO] arg target_branch :  {args.target_branch}")
    print(f"[INFO] arg target_repository :  {args.target_repository}")

    start_directory = os.getcwd()
    print(f"working directory: {start_directory}")

    print("make changes to charts from development")
    make_required_changes(args.pr_dir, args.dev_dir, args.charts_dir)

    print("edit files in charts")
    os.chdir(args.charts_dir)

    organization = args.target_repository.split("/")[0]
    charts_repository = f"{organization}{gitutils.CHARTS_REPO}"
    print(
        f"create charts pull request, repository: {charts_repository}, branch: {args.target_branch} "
    )
    branch_name = f"{CHARTS_PR_BRANCH_NAME_PREFIX}{args.version}"
    message = f"{CHARTS_PR_BRANCH_BODY_PREFIX} {branch_name}"
    outcome = gitutils.create_pr(
        branch_name, [], charts_repository, message, args.target_branch
    )
    if outcome == gitutils.PR_CREATED:
        gitutils.add_output("charts_pr_created", "true")
    elif outcome == gitutils.PR_NOT_NEEDED:
        gitutils.add_output("charts_pr_not_needed", "true")
    else:
        print("[ERROR] error creating charts PR")
        gitutils.add_output("charts_pr_error", "true")
        os.chdir(start_directory)
        return

    os.chdir(start_directory)

    print("make changes to development from charts")
    make_required_changes(args.pr_dir, args.charts_dir, args.dev_dir)

    os.chdir(args.dev_dir)
    print("create development pull request")
    branch_name = f"{DEV_PR_BRANCH_NAME_PREFIX}{args.version}"
    outcome = gitutils.create_pr(
        branch_name,
        [release_info.RELEASE_INFO_FILE],
        args.target_repository,
        args.dev_pr_body,
        args.target_branch,
    )
    if outcome == gitutils.PR_CREATED:
        print("Dev PR successfully created.")
        gitutils.add_output("dev_pr_created", "true")
    elif outcome == gitutils.PR_NOT_NEEDED:
        print("Dev PR not needed.")
        gitutils.add_output("dev_pr_not_needed", "true")
    else:
        print("[ERROR] error creating development PR.")
        gitutils.add_output("dev_pr_error", "true")

    os.chdir(start_directory)

    print("make changes to stage from development")
    make_required_changes(args.pr_dir, args.dev_dir, args.stage_dir)
    os.chdir(args.stage_dir)
    stage_repository = f"{organization}{gitutils.STAGE_REPO}"
    print(
        f"create stage pull request, repository: {stage_repository}, branch: {args.target_branch} "
    )
    branch_name = f"{STAGE_PR_BRANCH_NAME_PREFIX}{args.version}"
    message = f"{STAGE_PR_BRANCH_BODY_PREFIX} {branch_name}"
    outcome = gitutils.create_pr(
        branch_name, [], stage_repository, message, args.target_branch
    )
    if outcome == gitutils.PR_CREATED:
        gitutils.add_output("stage_pr_created", "true")
    elif outcome == gitutils.PR_NOT_NEEDED:
        gitutils.add_output("stage_pr_not_needed", "true")
    else:
        print("[ERROR] error creating stage PR")
        gitutils.add_output("stage_pr_error", "true")
        os.chdir(start_directory)
        return

    os.chdir(start_directory)


if __name__ == "__main__":
    main()
