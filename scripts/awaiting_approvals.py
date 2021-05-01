import sys
import subprocess
import json

def get_open_pull_request_commits(repository):
    out = subprocess.run(["curl", "-H", "Accept: application/vnd.github.v3+json", "-s", f"https://api.github.com/repos/{repository}/pulls?state=open"], capture_output=True)
    stdout = out.stdout.decode("utf-8")
    err = out.stderr.decode("utf-8")
    if err.strip():
        print("Error: ", err)
        sys.exit(1)

    commits = []
    for pr in json.loads(stdout):
        if not pr["draft"]:
            commits.append((pr["number"], pr["head"]["sha"]))

    return commits

def get_pull_requests_awaiting_approval(repository, commits):
    pull_requests = []
    for pr, commit in commits:
        out = subprocess.run(["curl", "-H", "Accept: application/vnd.github.v3+json", "-s", f"https://api.github.com/repos/{repository}/commits/{commit}/check-suites"], capture_output=True)
        stdout = out.stdout.decode("utf-8")
        err = out.stderr.decode("utf-8")
        if err.strip():
            print("Error: ", err)
            sys.exit(1)

        for check_suite in json.loads(stdout)["check_suites"]:
            if check_suite["conclusion"] == "action_required":
                pull_requests.append(str(pr))
                break

    return pull_requests

def create_mail_content(repository, pull_requests):
    content = "The following pull requests awaiting manual approval:\n\n"
    pr_msg = []
    for pr in pull_requests:
        pr_msg.append(f"  - https://github.com/{repository}/pull/{pr}")

    content += "\n".join(pr_msg)
    content += "\n"
    return content

def main():
    repository = sys.argv[1]
    commits = get_open_pull_request_commits(repository)
    pull_requests = get_pull_requests_awaiting_approval(repository, commits)
    if len(pull_requests) > 0:
        content = create_mail_content(repository, pull_requests)
        with open("mail-content.md", "w") as fd:
            fd.write(content)
        print(f"::set-output name=mail::true")
        prs = ",".join(pull_requests)
        print(f"::set-output name=pull_requests::{prs}")
    else:
        print(f"::set-output name=mail::false")

if __name__ == "__main__":
    main()
