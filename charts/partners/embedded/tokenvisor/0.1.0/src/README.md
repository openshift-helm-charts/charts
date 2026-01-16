# TokenVisor Helm Chart

This chart deploys TokenVisor and its required data/observability stack. It **does not** install operators, CRDs, CNI, or storage providers. Follow the steps below in order.

## What Gets Installed

Enabled by default:

- EMU API, Starling worker, Studio UI
- ClickHouse (CRs), CNPG/Postgres (CRs), Dragonfly (CR)
- VictoriaMetrics (CRs), VictoriaLogs (subchart)

Optional (disabled by default):

- Grafana (CRs + datasources)
- VMAlert (alerts/rules)
- Fluent Bit (log shipping)

## Hard Requirements

- **At least 3 nodes**
- Operators installed (chart does NOT install them):
  - Victoria Metrics Operator (available via OpenShift OperatorHub)
  - ClickHouse Operator (Altinity)
  - CloudNativePG (available via OpenShift OperatorHub)
  - Dragonfly Operator
  - Grafana Operator (only if Grafana enabled)
  - Fluent Operator (only if Fluent Bit enabled)
- Storage provider installed with appropriate StorageClass configured
- ServiceMonitor/PodMonitor CRDs installed

See `docs/PREREQUISITES.md` for the full checklist.

## Quick Start (Minimal Sequence)

1. **Create namespaces**

```bash
kubectl create namespace tokenvisor
```

**Note:** Skypilot is disabled by default. Only create the skypilot namespace if you plan to enable it:
```bash
# Only if enabling skypilot
kubectl create namespace skypilot
```

2. **Install operators + CRDs** See `docs/OPERATORS.md`.

3. **Configure a storage provider** Ensure your cluster has a StorageClass configured. See `docs/STORAGE.md` for details.

4. **Create image pull secret for GHCR**

To pull images from GitHub Container Registry, you need to create a docker-registry secret:

```bash
kubectl create secret docker-registry github-registry-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<password> \
  --namespace=tokenvisor
```

Replace `<username>` with your GitHub username and `<password>` with a GitHub personal access token (PAT) that has `read:packages` scope.

5. **Create required secrets**

```bash
kubectl apply -f charts/tokenvisor-openshift/docs/SECRETS_TEMPLATE.yaml
```

If you are using a packaged chart:

```bash
helm pull <repo>/tokenvisor --version <ver> --untar
kubectl apply -f tokenvisor/docs/SECRETS_TEMPLATE.yaml
```

6. **Fetch chart dependencies (Victoria Logs)**

```bash
helm dependency update charts/tokenvisor-openshift
```

7. **Install TokenVisor**

```bash
helm upgrade --install tokenvisor charts/tokenvisor-openshift \
  -n tokenvisor \
  -f charts/tokenvisor-openshift/values.yaml
```

## Accessing TokenVisor APIs

TokenVisor provides a unified access point for both the web UI and API access.

### Studio Frontend (Web UI + API)

- **URL**: `https://studio-frontend-server-{hostPrefix}.{namespace}.{clusterDomain}`
- **Purpose**: Interactive web interface for managing models, projects, and organizations
- **Example**: `https://studio-frontend-server-tokenvisor.tokenvisor.apps.ellm-3.local.com`

#### Using Personal Access Tokens (PATs)

To access the API programmatically using Personal Access Tokens:

1. **Create a PAT** in the Studio UI under your project settings
2. **Use the Studio Frontend URL** for API requests

Example chat completion request:

```bash
# Set your credentials
PAT_TOKEN="tv-pat-xxxxxxxxxxxx"
PROJECT_ID="your-project-id"

# Make API request to Studio Frontend URL
curl -X POST "https://studio-frontend-server-tokenvisor.tokenvisor.apps.ellm-3.local.com/api/v1/chat/completions" \
  -H "Authorization: Bearer $PAT_TOKEN" \
  -H "X-PROJECT-ID: $PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-id",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

#### Available API Endpoints

All API endpoints are accessed through the Studio Frontend URL:

- `POST /api/v1/chat/completions` - Chat completions
- `POST /api/v1/embeddings` - Text embeddings
- `POST /api/v1/rerank` - Text reranking
- `GET /api/v1/models` - List available models
- `GET /api/v1/models/ids` - List model IDs
- `GET /api/health` - Health check

See the [API documentation](https://emu-api-server-tokenvisor.tokenvisor.apps.ellm-3.local.com/api/public/docs) for more details.

**Note:** For direct backend access (bypassing the Studio proxy), you can also use the EMU backend URL at `https://emu-api-server-{hostPrefix}.{namespace}.{clusterDomain}`.

## Additional Docs (Packaged With Chart)

When using a packaged chart, you can access detailed docs by untarring the chart:

```bash
helm pull <repo>/tokenvisor --version <ver> --untar
ls tokenvisor/docs
```

Docs included:

- `docs/PREREQUISITES.md`
- `docs/OPERATORS.md`
- `docs/K3D.md`
- `docs/STORAGE.md`
- `docs/SEAWEEDFS.md`
- `docs/SECRETS.md`
- `docs/CUSTOMIZATION.md`
- `docs/TROUBLESHOOTING.md`

## Image Pull Secrets (GHCR)

If GHCR images are private, create the registry secret:

```bash
kubectl -n tokenvisor create secret docker-registry github-registry-secret \
  --docker-server=ghcr.io \
  --docker-username="<github-username>" \
  --docker-password="<github-token>" \
  --docker-email="<email>"
```

If you enable skypilot, create the same secret in the skypilot namespace:

```bash
# Only if enabling skypilot
kubectl -n skypilot create secret docker-registry github-registry-secret \
  --docker-server=ghcr.io \
  --docker-username="<github-username>" \
  --docker-password="<github-token>" \
  --docker-email="<email>"
```

If you use a different secret name, update:

```yaml
global:
  imagePullSecrets:
    - name: github-registry-secret
skypilot:
  imagePullSecrets:
    - name: github-registry-secret
```

## Model Storage (RWX Volume)

EMU and Starling mount a RWX volume at `/hf_repo`. If the PVC is missing, pods will remain `Pending`.

By default the chart **fails fast** if the PVC does not exist. You can disable this check:

```yaml
validation:
  failOnMissingModelPVC: false
```

The PVC name is **hardcoded in the EMU backend** as `nfs-model-storage-pvc`. Do not change it unless you also change the backend code.

If you use SeaweedFS, create PV/PVC manually (see `docs/STORAGE.md` for a template) and set:

```yaml
emu:
  modelStorage:
    existingClaim: nfs-model-storage-pvc
storage:
  modelPvc:
    create: false
```

If multiple namespaces need RWX access (e.g., `skypilot`), create a PVC in each namespace.

For a step-by-step SeaweedFS install, see `docs/SEAWEEDFS.md`.

## Studio Theme + Logos

Studio ships with the **default theme** (from the original manifests). Logos are optional and only needed if you want custom branding. Studio assets are driven by ConfigMaps:

```yaml
studio:
  themeCss: |
    :root { --primary: 192 67% 32%; }
  logos:
    favicon.svg: "<svg ...>"
  logosBinaryData:
    favicon.svg: "<base64>"
    favicon.svg.gz: "<base64>"
    favicon.svg.br: "<base64>"
```

## Victoria Logs (Dependency)

This chart includes Victoria Logs as a dependency:

- Chart version: **0.11.19**
- App tag: **v1.41.1**

The values are under `victoria-logs-single:` in `values.yaml`.

## Common Customizations

Images:

```yaml
emu:
  image: ghcr.io/embeddedllm/tokenvisor-emu:<tag>
starling:
  image: ghcr.io/embeddedllm/tokenvisor-emu:<tag>
studio:
  image: ghcr.io/embeddedllm/tokenvisor-studio:<tag>
```

Studio hostnames:

```yaml
studio:
  config:
    HOST: "studio.example.com"
    ORIGIN: "https://studio.example.com"
```

OpenShift Routes configuration:

See `docs/CUSTOMIZATION.md` for details on configuring OpenShift Routes.

Enable optional components:

```yaml
grafana:
  enabled: true
vmalert:
  enabled: true
  tokenvisorWebhookUrl: "https://discord.com/api/webhooks/..."
  tokenvisorLogWebhookUrl: "https://discord.com/api/webhooks/..."
  enableLogRules: true
fluentbit:
  enabled: true
```

When Grafana is enabled, the chart installs:

- TokenVisor dashboards (EMU, Model Status, Traces)
- Operator dashboards (ClickHouse/CNPG/Dragonfly/Grafana Operator)
- VM/VLogs dashboards
- VMAlert dashboard (only if `vmalert.enabled=true`)

## Startup Dependency Waiters

EMU/Starling wait for ClickHouse schema + Postgres + VictoriaMetrics. Studio waits for EMU `/api/health`.

```yaml
emu:
  initWaiter:
    enabled: true
    timeoutSeconds: 600
    postgres:
      host: tokenvisor-pgbouncer.tokenvisor.svc.cluster.local
      port: 5432
    clickhouse:
      host: clickhouse-tokenvisor.tokenvisor.svc.cluster.local
      requiredTables:
        - llm_usage
        - embed_usage
        - rerank_usage
        - deployment_usage
        - emu_traces
    victoriametrics:
      host: vmauth-vmauth.tokenvisor.svc.cluster.local
      port: 8427

studio:
  initWaiter:
    enabled: true
    emuHealthUrl: "http://emu-api-server.tokenvisor.svc.cluster.local:5969/api/health"
```

Note: If you manage ClickHouse schema yourself, either keep the required tables list in sync or disable the waiter.

## ClickHouse Init Job

Schema initialization is a Job that waits for ClickHouse readiness. It is **not** a Helm hook by default to avoid Helm timeouts.

```yaml
clickhouse:
  initJob:
    enabled: true
    useHelmHook: false
```

If you want Helm to wait for schema init, set `useHelmHook: true` and increase Helm timeout (example `--timeout 20m`).

## Validation Checklist

Before install:

- `kubectl get nodes` shows **>= 3** nodes
- Operators installed and running
- Required secrets exist in `tokenvisor` (chart fails fast if missing)
- Storage classes match your values

After install:

- `kubectl get pods -n tokenvisor` shows EMU/Starling/Studio and operator-managed pods
- `kubectl get routes -n tokenvisor` shows OpenShift Routes for exposed services

## Layout

```
charts/tokenvisor-openshift/
  Chart.yaml
  values.yaml
  templates/
```
