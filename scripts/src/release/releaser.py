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
- Adds the cron job to .github/worklfows/schedule.yml and changes the verifier image used in .github/worklfows/schedule.yml
  to latest, as required. The charts repo is updated from development repo which necessitates these update.
- Create a PR against the charts repo containing the workflow updates. This requires manual merge.
- Directly commits to the development main branch any new charts added to the charts repo since the last update.


"""
import yaml
import os
import argparse
import sys
import shutil
from release import release_info

sys.path.append('../')
from github import gitutils

SCHEDULE_YAML_FILE=".github/workflows/schedule.yml"
BUILD_YAML_FILE=".github/workflows/build.yml"

SCHEDULE_INSERT = [
    '  # Daily trigger to check updates',
    '  schedule:',
    '    - cron: "0 0 * * *"'
]

def update_workflow():

    lines=[]
    with open(SCHEDULE_YAML_FILE,'r') as schedule_file:

        lines = schedule_file.readlines()

        for line in lines:
            if line.strip() == "on:":
                insert_location = lines.index(line)+1
                if SCHEDULE_INSERT[0] not in lines[insert_location].rstrip():
                    print("[INFO] add cron job to schedule.yaml")
                    lines.insert(insert_location,f"{SCHEDULE_INSERT[0]}\n")
                    lines.insert(insert_location+1,f"{SCHEDULE_INSERT[1]}\n")
                    lines.insert(insert_location+2,f"{SCHEDULE_INSERT[2]}\n")
                    break

    with open(SCHEDULE_YAML_FILE,'w') as schedule_file:
        schedule_file.write("".join(lines))


    with open(BUILD_YAML_FILE,'r') as build_file:

        lines = build_file.readlines()

        for line in lines:
            if "VERIFIER_IMAGE:" in line:
                if "chart-verifier:main" in line:
                    line_index = lines.index(line)
                    print(f"replace: {lines[line_index].rstrip()}")
                    lines[line_index] = lines[line_index].replace('chart-verifier:main','chart-verifier:latest')
                    print(f"with   : {lines[line_index].rstrip()}")

    with open(BUILD_YAML_FILE,'w') as build_file:
        build_file.write("".join(lines))


def make_required_changes(release_info_dir,origin,destination):

    print(f"Make required changes from {origin} to {destination}")

    repository = "development"
    if "charts" in origin or "development" in destination:
        repository = "charts"

    replaces = release_info.get_replaces(repository,release_info_dir)

    for replace in replaces:
        replace_this=f"{destination}/{replace}"
        with_this = f"{origin}/{replace}"
        if os.path.isdir(with_this) or os.path.isdir(replace_this):
            print(f"Replace directory {replace_this} with {with_this}")
            if os.path.isdir(replace_this):
                shutil.rmtree(replace_this)
            shutil.copytree(with_this,replace_this)
        else:
            print(f"Replace file {replace_this} with {with_this}")
            shutil.copy2(with_this,replace_this)

    merges =  release_info.get_merges(repository,release_info_dir)

    for merge in merges:
        merge_this = f"{origin}/{merge}"
        into_this = f"{destination}/{merge}"

        if os.path.isdir(merge_this) or os.path.isdir(into_this):
            print(f"Merge directory {merge_this} with {into_this}")
            shutil.copytree(merge_this,into_this,dirs_exist_ok=True)
        else:
            print(f"Merge file {merge_this} with {into_this}")
            shutil.copy2(merge_this,into_this)


    ignores = release_info.get_ignores(repository,release_info_dir)
    for ignore in ignores:
        ignore_this = f"{destination}/{ignore}"
        if os.path.isdir(ignore_this):
            print(f"Ignore/delete directory {ignore_this}")
            shutil.rmtree(ignore_this)
        else:
            print(f"Ignore/delete file {ignore_this}")
            os.remove(ignore_this)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--version", dest="version", type=str, required=True,
                        help="Version to compare")
    parser.add_argument("-d", "--development_dir", dest="dev_dir", type=str, required=True,
                       help="Directory of development code with latest release info.")
    parser.add_argument("-c", "--charts_dir", dest="charts_dir", type=str, required=True,
                        help="Directory of charts code.")
    parser.add_argument("-p", "--pr_dir", dest="pr_dir", type=str, required=True,
                        help="Directory of pull request code.")
    args = parser.parse_args()

    start_directory = os.getcwd()
    print(f"working directory: {start_directory}")

    print(f"make changes to charts from development")
    make_required_changes(args.pr_dir,args.dev_dir,args.charts_dir)

    print(f"edit files in charts")
    os.chdir(args.charts_dir)
    update_workflow()

    print(f"create charts pull request")
    gitutils.create_charts_pr(args.version)

    os.chdir(start_directory)

    print(f"make changes to development from charts")
    make_required_changes(args.pr_dir,args.charts_dir,args.dev_dir)

    os.chdir(args.dev_dir)
    print(f"commit development changes")
    gitutils.commit_development_updates(args.version,release_info.RELEASE_INFO_FILE)

    os.chdir(start_directory)

if __name__ == "__main__":
    main()
