#!/usr/bin/env bash
# pre-commit hook: helm lint on the Expanso Edge chart
# Lightweight — runs in <5 seconds, no cluster needed.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CHART_BASE="${REPO_ROOT}/charts/partners/expanso/expanso-edge"

# Auto-detect latest version directory (supports multi-version repos)
CHART_VERSION=$(ls -v "${CHART_BASE}" | grep -E '^[0-9]' | tail -1)
CHART_SRC="${CHART_BASE}/${CHART_VERSION}/src"

if [[ ! -f "${CHART_SRC}/Chart.yaml" ]]; then
  echo "❌  Could not find Chart.yaml at ${CHART_SRC}"
  exit 1
fi

echo "🔍  helm lint: expanso-edge ${CHART_VERSION}"

# Lint with default values
helm lint "${CHART_SRC}" --strict 2>&1

# Also lint with CI values (local mode, probes disabled)
CI_VALUES="${CHART_SRC}/ci/ci-values.yaml"
if [[ -f "${CI_VALUES}" ]]; then
  echo "🔍  helm lint with ci-values.yaml"
  helm lint "${CHART_SRC}" -f "${CI_VALUES}" --strict 2>&1
fi

echo "✅  helm lint passed"
