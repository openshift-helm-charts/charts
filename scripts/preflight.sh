#!/usr/bin/env bash
# =============================================================================
# scripts/preflight.sh — Expanso Edge Helm Chart Full Preflight Test
# =============================================================================
#
# PURPOSE
#   Runs a complete end-to-end validation of the Helm chart against a real
#   Kubernetes cluster. Mirrors the Red Hat OpenShift CI pipeline (~5 min
#   timeout). Use this before pushing a chart version bump or opening a PR.
#
# PREREQUISITES
#   - helm   >= 3.x     (brew install helm)
#   - kind   >= 0.20    (brew install kind)
#   - kubectl           (brew install kubectl)
#   - docker / podman   (running daemon)
#
# USAGE
#   scripts/preflight.sh                   # full run (creates + tears down cluster)
#   scripts/preflight.sh --no-teardown     # keep cluster for debugging
#   scripts/preflight.sh --skip-cluster    # use existing kind cluster
#   scripts/preflight.sh --chart-version 2.1.7   # pin a specific chart version
#
# EXIT CODES
#   0  All checks passed
#   1  Preflight failure (logs captured to preflight-failure.log)
#
# =============================================================================
set -euo pipefail

# ─── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[preflight]${RESET} $*"; }
success() { echo -e "${GREEN}[preflight] ✅ $*${RESET}"; }
warn()    { echo -e "${YELLOW}[preflight] ⚠️  $*${RESET}"; }
fail()    { echo -e "${RED}[preflight] ❌ $*${RESET}" >&2; }

# ─── Defaults ─────────────────────────────────────────────────────────────────
CLUSTER_NAME="expanso-edge-preflight"
NAMESPACE="expanso-preflight"
RELEASE_NAME="expanso-edge-ci"
TIMEOUT_SECONDS=300          # 5 min — matches Red Hat CI
TEARDOWN=true
SKIP_CLUSTER=false
CHART_VERSION=""             # auto-detect if empty
FAILURE_LOG="${PWD}/preflight-failure.log"

# ─── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-teardown)   TEARDOWN=false; shift ;;
    --skip-cluster)  SKIP_CLUSTER=true; shift ;;
    --chart-version) CHART_VERSION="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | head -30 | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) fail "Unknown argument: $1"; exit 1 ;;
  esac
done

# ─── Locate chart ─────────────────────────────────────────────────────────────
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
CHART_BASE="${REPO_ROOT}/charts/partners/expanso/expanso-edge"

if [[ -z "${CHART_VERSION}" ]]; then
  CHART_VERSION=$(ls -v "${CHART_BASE}" | grep -E '^[0-9]' | tail -1)
fi

CHART_SRC="${CHART_BASE}/${CHART_VERSION}/src"
CI_VALUES="${CHART_SRC}/ci/ci-values.yaml"

if [[ ! -f "${CHART_SRC}/Chart.yaml" ]]; then
  fail "Chart not found at ${CHART_SRC}"
  exit 1
fi

info "Chart: expanso-edge ${CHART_VERSION} (${CHART_SRC})"

# ─── Preflight dependency check ───────────────────────────────────────────────
check_dep() {
  if ! command -v "$1" &>/dev/null; then
    fail "Required tool not found: $1"
    fail "Install with: $2"
    exit 1
  fi
}

info "Checking dependencies..."
check_dep helm   "brew install helm  OR  https://helm.sh/docs/intro/install/"
check_dep kind   "brew install kind  OR  https://kind.sigs.k8s.io/docs/user/quick-start/"
check_dep kubectl "brew install kubectl"
success "All dependencies present"

# ─── Helm lint/template (fast pre-check before spinning cluster) ───────────────
info "Running helm lint..."
helm lint "${CHART_SRC}" --strict
if [[ -f "${CI_VALUES}" ]]; then
  helm lint "${CHART_SRC}" -f "${CI_VALUES}" --strict
fi
success "helm lint passed"

info "Running helm template render..."
helm template "${RELEASE_NAME}" "${CHART_SRC}" \
  -f "${CI_VALUES}" \
  --set expansoEdge.bootstrap.token="preflight-placeholder" \
  > /dev/null
success "helm template render passed"

# ─── Teardown helper (called on EXIT) ─────────────────────────────────────────
cleanup() {
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    warn "Preflight FAILED (exit ${exit_code}). Capturing diagnostics..."
    {
      echo "=== PREFLIGHT FAILURE LOG ==="
      echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "Chart: expanso-edge ${CHART_VERSION}"
      echo ""
      echo "=== Pod status ==="
      kubectl get pods -n "${NAMESPACE}" 2>/dev/null || echo "(namespace gone)"
      echo ""
      echo "=== Pod describe ==="
      kubectl describe pods -n "${NAMESPACE}" 2>/dev/null || echo "(namespace gone)"
      echo ""
      echo "=== Pod logs ==="
      kubectl logs -n "${NAMESPACE}" -l "app.kubernetes.io/name=expanso-edge" \
        --tail=200 2>/dev/null || echo "(no logs)"
      echo ""
      echo "=== Events ==="
      kubectl get events -n "${NAMESPACE}" --sort-by='.lastTimestamp' 2>/dev/null || echo "(no events)"
    } > "${FAILURE_LOG}"
    fail "Diagnostics saved to: ${FAILURE_LOG}"
  fi

  if [[ "${TEARDOWN}" == "true" ]]; then
    info "Tearing down kind cluster: ${CLUSTER_NAME}"
    kind delete cluster --name "${CLUSTER_NAME}" 2>/dev/null || true
  else
    warn "Cluster kept (--no-teardown). To clean up: kind delete cluster --name ${CLUSTER_NAME}"
  fi
}
trap cleanup EXIT

# ─── Kind cluster setup ───────────────────────────────────────────────────────
if [[ "${SKIP_CLUSTER}" == "true" ]]; then
  info "Skipping cluster creation (--skip-cluster)"
  if ! kind get clusters 2>/dev/null | grep -q "${CLUSTER_NAME}"; then
    fail "No kind cluster named '${CLUSTER_NAME}' found. Remove --skip-cluster to create one."
    exit 1
  fi
else
  if kind get clusters 2>/dev/null | grep -q "${CLUSTER_NAME}"; then
    warn "Kind cluster '${CLUSTER_NAME}' already exists — reusing it."
    warn "Pass --skip-cluster to skip creation, or delete it first:"
    warn "  kind delete cluster --name ${CLUSTER_NAME}"
  else
    info "Creating kind cluster: ${CLUSTER_NAME}"
    kind create cluster --name "${CLUSTER_NAME}" --wait 60s
    success "Kind cluster created"
  fi
fi

# Set kubectl context
kubectl config use-context "kind-${CLUSTER_NAME}"

# ─── Namespace ────────────────────────────────────────────────────────────────
info "Creating namespace: ${NAMESPACE}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# ─── Helm install ─────────────────────────────────────────────────────────────
info "Installing Helm chart with CI values (localMode=true, probes disabled)..."

# Use a quay-hosted image that's accessible without Red Hat auth in CI
# Fallback to the values.yaml default (registry.connect.redhat.com) if quay not set
QUAY_IMAGE="${QUAY_IMAGE:-quay.io/expanso/expanso-edge}"

helm upgrade --install "${RELEASE_NAME}" "${CHART_SRC}" \
  --namespace "${NAMESPACE}" \
  -f "${CI_VALUES}" \
  --set "image.repository=${QUAY_IMAGE}" \
  --set "image.tag=${CHART_VERSION}-ubi9" \
  --set "expansoEdge.bootstrap.token=preflight-ci-token" \
  --timeout 120s \
  --wait=false \
  --debug

success "Helm install submitted"

# ─── Wait for pod Running ─────────────────────────────────────────────────────
info "Waiting for pod to reach Running state (timeout: ${TIMEOUT_SECONDS}s)..."

LABEL_SELECTOR="app.kubernetes.io/instance=${RELEASE_NAME}"
START_TIME=$(date +%s)
POD_RUNNING=false

while true; do
  NOW=$(date +%s)
  ELAPSED=$(( NOW - START_TIME ))

  if [[ ${ELAPSED} -ge ${TIMEOUT_SECONDS} ]]; then
    fail "Pod did not reach Running within ${TIMEOUT_SECONDS}s"
    exit 1
  fi

  # Check pod phase
  POD_PHASE=$(kubectl get pods -n "${NAMESPACE}" \
    -l "${LABEL_SELECTOR}" \
    -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "Pending")

  POD_NAME=$(kubectl get pods -n "${NAMESPACE}" \
    -l "${LABEL_SELECTOR}" \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

  info "  [${ELAPSED}s/${TIMEOUT_SECONDS}s] Pod phase: ${POD_PHASE} (${POD_NAME:-none})"

  if [[ "${POD_PHASE}" == "Running" ]]; then
    POD_RUNNING=true
    break
  fi

  # Check for crash / image pull errors early
  POD_REASON=$(kubectl get pods -n "${NAMESPACE}" \
    -l "${LABEL_SELECTOR}" \
    -o jsonpath='{.items[0].status.containerStatuses[0].state.waiting.reason}' 2>/dev/null || echo "")

  if [[ "${POD_REASON}" == "CrashLoopBackOff" || "${POD_REASON}" == "ErrImagePull" || "${POD_REASON}" == "ImagePullBackOff" ]]; then
    fail "Pod stuck in ${POD_REASON} — bailing early"
    exit 1
  fi

  sleep 5
done

if [[ "${POD_RUNNING}" != "true" ]]; then
  fail "Pod never reached Running state"
  exit 1
fi

success "Pod is Running: ${POD_NAME}"

# ─── Health probe validation ───────────────────────────────────────────────────
# In localMode the API still binds — we port-forward and hit /api/v1/health
info "Validating health probes via port-forward..."

LOCAL_PORT=18234
kubectl port-forward -n "${NAMESPACE}" "pod/${POD_NAME}" "${LOCAL_PORT}:1234" &
PF_PID=$!

# Give port-forward a moment to establish
sleep 3

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  --connect-timeout 5 --max-time 10 \
  "http://localhost:${LOCAL_PORT}/api/v1/health" || echo "000")

kill "${PF_PID}" 2>/dev/null || true

if [[ "${HTTP_STATUS}" == "200" ]]; then
  success "Health probe responded HTTP 200"
elif [[ "${HTTP_STATUS}" == "000" ]]; then
  # In localMode the API may not be fully up if bootstrap fails — soft warn
  warn "Health probe not reachable (HTTP ${HTTP_STATUS}). This may be expected in localMode without a live bootstrap."
  warn "Chart installation and pod Running state are the primary CI gate."
else
  fail "Health probe returned unexpected status: HTTP ${HTTP_STATUS}"
  exit 1
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
success "Preflight complete! Chart deploys cleanly with CI values."
echo ""
echo -e "${BOLD}Summary:${RESET}"
echo "  Chart:      expanso-edge ${CHART_VERSION}"
echo "  Cluster:    kind-${CLUSTER_NAME}"
echo "  Namespace:  ${NAMESPACE}"
echo "  Release:    ${RELEASE_NAME}"
echo "  Pod:        ${POD_NAME}"
echo "  Health:     HTTP ${HTTP_STATUS}"
echo ""

if [[ "${TEARDOWN}" == "true" ]]; then
  info "Cluster teardown initiated..."
else
  echo -e "${YELLOW}Cluster kept. Inspect with:${RESET}"
  echo "  kubectl config use-context kind-${CLUSTER_NAME}"
  echo "  kubectl get all -n ${NAMESPACE}"
  echo "  kind delete cluster --name ${CLUSTER_NAME}   # when done"
fi
