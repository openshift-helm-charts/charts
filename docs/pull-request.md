# Pull Request

## Content of PR

When users submit pull requests, the PR content should be either chart related
or non-chart related.  Combining changes related to both chart and non-chart in
the same PR is not allowed.  (TBD: Need clarity about OWNERS file) A PR making
changes to a chart may contain a chart and/or report.  The chart could be either
a tarball or extracted form.

## Authorized Pull Request

When a pull request passes all checks, the PR will get `authorized-request` as a
label.  Along with this, the bot will add a comment with a few generic
information.  The comment also includes a particular metadata line with the
vendor label and chart name.  The metadata line will start with `/metadata` as a
prefix to avoid ambiguity when parsing the comment. Here is an example metadata
line:

```
/metadata {"vendor_label": "label", "chart_name": "name"}
```

The metadata line should meet the following requirements:

1. The whole metadata content will be in a single line
2. The line starts with `/metadata` (space character is allowed before `/metadata`)
3. After the JSON content, only space is allowed before the line end
4. There will take at least one space immediately after `/metadata`

## Testing in a Fork

If you're making changes to workflows/scripts and want to test them before
submitting a PR, you'll need to prepare a few prerequisites.

1) A second account to use as your "Bot".
    - This account is what does your "approvals" and interacts with GitHub on behalf of the GitHub Actions workflows. In some cases, the GitHub Actions Bot may be used, but generally, you will need a secondary account to interact with, approve, and merge your PRs (because you "can't approve your own" PRs).
2) An OpenShift cluster (SNO works fine for most cases)
    - Specifically for cases where your development requires you to run `chart-verifier` within the Pipeline. In order to do this successfully, you'll need a cluster for the pipeline to manipulate.

With those in hand, follow the process below to configure your infrastructure.

### Prepare GitHub

1) Fork the repository to your own namespace/organization
2) Ensure that the gh-pages branch exists in your fork, or otherwise pull the
   branch from the origin and push it to your repository
3) [Enable GitHub
   Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site#creating-your-site)
   for your repository. We do not use Custom Workflows for GitHub Pages as of
   the time of this writing.
4) Grant your "Bot" account access to your forked repository as a
   [collaborator](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/inviting-collaborators-to-a-personal-repository).
5) [Generate a Personal Access
   Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
   for your "Bot" that can write to the repository, update comments, approve
   PRs, etc. (TODO: identify exact PAT perms necessary for both legacy and
   fine-grained cases). Store this as `BOT_TOKEN` within your [repository
   secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions).
6) [Configure GitHub
   Actions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#managing-github-actions-permissions-for-your-repository)
   to run in your fork if they're not already allowed to do so.
7) Create a new project directory within the
   **charts/(community,partners,redhat)** directory for your chart submission,
   with an appropriate OWNERS file that allows your GitHub Username to submit
   PRs. If you don't, the pipeline will reject your PRs because "this user
   cannot submit PRs to this project".
    - Creating a partner project is the easiest, unless you're explicitly
      testing Community or Red Hat workflows. The latter two have modified
      submission workflows. that can get in the way of your testing.

### Prepare your cluster

A cluster is used to test the helm chart via "chart testing", which installs and
runs certain tests against a given chart. Each PR gets its own namespace where
the pipeline works during a PR's workflow execution. For that reason, we need
to:

1) Create the service account that's used to provision cluster namespaces and
   tooling within your test cluster using [our
   script](../scripts/src/saforcertadmin/create_sa.sh).
2) Store the token in your [repository
   secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
   as `CLUSTER_TOKEN`.
3) Extract the cluster's API server address, base64 encode it, and store it in
   your repository secrets as `API_SERVER`. E.g.

```
    yq .clusters[0].cluster.server /path/to/your/kubeconfig | base64
```

### Make your changes and tests

At this point, you should be ready to make any workflow changes you want, submit
a PR with an arbitrary chart, watch the pipelines, and then iterate as you need.