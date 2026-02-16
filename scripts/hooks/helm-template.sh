#!/usr/bin/env bash
# pre-commit hook: helm template render check on the Expanso Edge chart
# Catches Go template errors that helm lint won't always catch.
# Lightweight — no cluster, no network.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CHART_BASE="${REPO_ROOT}/charts/partners/expanso/expanso-edge"

# Auto-detect latest version directory
CHART_VERSION=$(ls -v "${CHART_BASE}" | grep -E '^[0-9]' | tail -1)
CHART_SRC="${CHART_BASE}/${CHART_VERSION}/src"

if [[ ! -f "${CHART_SRC}/Chart.yaml" ]]; then
  echo "❌  Could not find Chart.yaml at ${CHART_SRC}"
  exit 1
fi

echo "🏗️   helm template: expanso-edge ${CHART_VERSION} (default values)"
helm template expanso-edge-test "${CHART_SRC}" \
  --set expansoEdge.bootstrap.token="ci-placeholder" \
  --debug \
  > /dev/null 2>&1 || {
    echo "❌  helm template failed with default values. Re-running for details:"
    helm template expanso-edge-test "${CHART_SRC}" \
      --set expansoEdge.bootstrap.token="ci-placeholder"
    exit 1
  }

# Render with CI values (local mode — most likely to succeed in CI)
CI_VALUES="${CHART_SRC}/ci/ci-values.yaml"
if [[ -f "${CI_VALUES}" ]]; then
  echo "🏗️   helm template: expanso-edge ${CHART_VERSION} (ci-values.yaml)"
  helm template expanso-edge-ci "${CHART_SRC}" \
    -f "${CI_VALUES}" \
    --debug \
    > /dev/null 2>&1 || {
      echo "❌  helm template failed with ci-values.yaml. Re-running for details:"
      helm template expanso-edge-ci "${CHART_SRC}" -f "${CI_VALUES}"
      exit 1
    }
fi

echo "✅  helm template render passed"
