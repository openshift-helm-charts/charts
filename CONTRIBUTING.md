# Contributing to Expanso Edge OpenShift Charts

Thank you for contributing! This guide covers the local development workflow for the
`charts/partners/expanso/expanso-edge` Helm chart, including the pre-commit hooks
and full preflight test script.

---

## Quick Start

```bash
git clone git@github.com:aronchick/charts.git
cd charts

# Install Python pre-commit framework (once per machine)
pip install pre-commit
# OR: brew install pre-commit

# Install the git hooks into your local clone (once per clone)
pre-commit install

# Verify hooks are working
pre-commit run --all-files
```

> **Why `pre-commit install`?**
> Without it the hooks exist in `scripts/hooks/` but won't run automatically.
> `pre-commit install` wires them into `.git/hooks/pre-commit` so they fire on every `git commit`.

---

## What Runs on Every Commit (lightweight, <10s)

| Hook | What it checks |
|------|----------------|
| `helm-lint` | `helm lint --strict` with default values AND `ci/ci-values.yaml` |
| `helm-template` | Full template render — catches Go template errors lint misses |
| Standard hooks | Trailing whitespace, YAML validity, merge conflicts |

These hooks **only trigger** when files under `charts/partners/expanso/expanso-edge/` change.
They require no cluster, no network, and typically finish in 2–5 seconds.

---

## Full Preflight Test (before pushing a chart bump or opening a PR)

The `scripts/preflight.sh` script mirrors the Red Hat OpenShift CI pipeline:

```bash
# Full run: spins up a kind cluster, installs the chart, validates, tears down
scripts/preflight.sh

# Keep the cluster alive for debugging
scripts/preflight.sh --no-teardown

# Reuse an existing preflight cluster
scripts/preflight.sh --skip-cluster

# Test a specific chart version
scripts/preflight.sh --chart-version 2.1.7
```

**What it does:**

1. `helm lint` + `helm template` (fast pre-check)
2. Creates a `kind` cluster (`expanso-edge-preflight`)
3. Installs the chart with `ci/ci-values.yaml` (localMode=true, probes disabled)
4. Waits up to **5 minutes** for the pod to reach `Running` (matches Red Hat CI timeout)
5. Port-forwards and validates `/api/v1/health` responds HTTP 200
6. On failure: captures pod logs, describe, and events → `preflight-failure.log`
7. Tears down the kind cluster (unless `--no-teardown`)

**Prerequisites:**

```bash
brew install helm kind kubectl
# Docker Desktop or Rancher Desktop must be running
```

---

## Chart Structure

```
charts/partners/expanso/expanso-edge/<version>/src/
├── Chart.yaml
├── values.yaml          # Default values (Red Hat registry image, probes enabled)
├── values.schema.json   # JSON Schema validation
├── ci/
│   └── ci-values.yaml   # CI overrides: localMode=true, probes disabled
├── templates/
│   ├── deployment.yaml
│   ├── configmap.yaml
│   ├── service.yaml
│   ├── serviceaccount.yaml
│   └── tests/
│       └── test-connection.yaml
└── README.md
```

### Key CI Values (`ci/ci-values.yaml`)

```yaml
expansoEdge:
  localMode: true      # Runs without a live control plane connection

livenessProbe:
  enabled: false       # Disabled so pod starts without a bootstrap token

readinessProbe:
  enabled: false
```

---

## Making Chart Changes

1. Edit files under `charts/partners/expanso/expanso-edge/<version>/src/`
2. `git commit` — pre-commit hooks run automatically
3. If you bump the chart version, update `Chart.yaml` **and** move the `src/` directory:
   ```bash
   cp -r charts/partners/expanso/expanso-edge/2.1.7 charts/partners/expanso/expanso-edge/2.1.8
   # edit Chart.yaml version inside the new dir
   ```
4. Run `scripts/preflight.sh` before pushing
5. Open a PR — Red Hat CI will run the full certification pipeline

---

## Skipping Hooks (emergency escape hatch)

```bash
git commit --no-verify -m "wip: skip hooks"
```

Use sparingly. The hooks exist to catch issues before Red Hat CI does.

---

## Troubleshooting

**`helm: command not found`**
```bash
brew install helm
# or https://helm.sh/docs/intro/install/
```

**`pre-commit: command not found`**
```bash
pip install pre-commit
# or: brew install pre-commit
```

**Hook fails on `yamllint`**
```bash
# Show full yamllint output
yamllint -c .yamllint.yaml charts/partners/expanso/expanso-edge/
```

**Preflight pod stuck in `ImagePullBackOff`**

The default image (`registry.connect.redhat.com/expanso/expanso-edge`) requires Red Hat credentials.
Set `QUAY_IMAGE` to use the public Quay mirror:
```bash
QUAY_IMAGE=quay.io/expanso/expanso-edge scripts/preflight.sh
```
