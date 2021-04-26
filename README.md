# OpenShift Helm Charts Repository

OpenShift Helm Charts Repository is the source of all the certified helm charts
from partners and the community.  The chart submission process is automated
using pull requests and GitHub Actions.  The GitHub Actions workflows securely
process the incoming pull requests and merge them to the main branch and
generate a chart index.  The git repository contains GitHub Actions workflow
files, programs to process the PR, and the chart itself.  Ensuring the chart
submission PR is not modifying the workflow files or scripts is essential for
security.  A sanity check ensures the pull request only contains chart-related
content.  After the sanity check, the next step is to build and verify the chart
for certification. Finally, report the error, if any, otherwise comment the PR
with metadata.
