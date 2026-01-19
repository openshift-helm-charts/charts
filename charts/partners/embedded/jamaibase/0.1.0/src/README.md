# Jamaibase Helm Chart

Complete Jamaibase AI platform deployment with all dependencies including storage, databases, caching, and monitoring.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Components](#components)
- [Upgrading](#upgrading)
- [Uninstallation](#uninstallation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🏗️ Overview

This Helm chart deploys the complete Jamaibase AI platform including:

### Application Components
- **OWL Backend** - Python-based API server with Celery workers
- **Jambu Frontend** - Node.js-based web interface
- **V8-Kopi** - Secure code execution system with isolated workers
- **Docling** - GPU-enabled document processing and OCR service

### Third-Party Dependencies
**NOTE:** The operators for these components must be installed cluster-wide BEFORE deploying Jamaibase. See [Prerequisites](#-prerequisites) for installation instructions.

- **CloudNativePG** - PostgreSQL operator for relational data (cluster-wide operator required)
- **ClickHouse** - Analytical database for logs and metrics (cluster-wide operator required)
- **Dragonfly** - High-performance Redis-compatible cache (cluster-wide operator required)
- **VictoriaMetrics** - Time-series database for monitoring (cluster-wide operator required)
- **SeaweedFS** - S3-compatible object storage (cluster-wide operator required)

### OpenShift Features
- **Security Context Constraints** - Proper security policies
- **Routes** - OpenShift-native HTTP routing
- **Network Policies** - Traffic management and security
- **Resource Quotas** - Resource usage limits
- **Operator Management** - Certified operators from marketplace

## 🔧 Prerequisites

### Operator Requirements

**IMPORTANT:** The following operators must be installed **cluster-wide** BEFORE deploying this Helm chart. The chart only creates the custom resources (instances, clusters) that these operators manage.

#### 1. Prometheus Operator
Required for monitoring and metrics collection. **Must be installed before Victoria Metrics Operator.**

```bash
# Install via OpenShift Subscription (cluster-wide)
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.80.1/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml

kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.80.1/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
# Verify installation
oc get pods -n openshift-operators | grep prometheus
```

**Documentation:** https://prometheus-operator.dev/

---

#### 2. Victoria Metrics Operator
Required for monitoring and metrics storage.

**IMPORTANT:** Prometheus Operator CRDs must be installed before Victoria Metrics Operator (see step 1 above).

**Installation via Red Hat Certified Operators (OpenShift):**

The Victoria Metrics Operator is available from the Red Hat ecosystem as a certified operator. Install it via OpenShift Subscription (cluster-wide):

```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: vm-global-operator-group
  namespace: openshift-operators
spec:
  targetNamespaces:
  - "*"  # All namespaces
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: victoria-metrics-operator
  namespace: openshift-operators
spec:
  channel: stable
  installPlanApproval: Automatic
  name: victoria-metrics-operator
  source: certified-operators
  sourceNamespace: openshift-marketplace
  startingCSV: victoria-metrics-operator.v0.47.0
EOF
```

**Verify Installation:**
```bash
# Check operator pod is running
oc get pods -n openshift-operators | grep victoria-metrics

# Verify CRDs are registered
oc get crd | grep victoriametrics

# Expected CRDs:
# vmagentoperator.victoriametrics.com
# vmalertmanagerconfig.victoriametrics.com
# vmalert.victoriametrics.com
# vmauth.victoriametrics.com
# vmcluster.victoriametrics.com
# vmnodescrape.victoriametrics.com
# vmpodscrape.victoriametrics.com
# vmrule.victoriametrics.com
# vmsingle.victoriametrics.com
# vmstaticscrape.victoriametrics.com
# vmuser.victoriametrics.com
# vmalertmanager.victoriametrics.com
# vmalertmanagerconfig.victoriametrics.com
# victorialogs.victoriametrics.com
```

**Documentation:** https://docs.victoriametrics.com/operator/

**Notes:**
- The operator watches all namespaces by default when installed in `openshift-operators`
- The Helm chart creates VictoriaMetrics custom resources (VMCluster, VMAuth, VMUser, etc.) in the `jamaibase` namespace
- No additional configuration is needed - the operator will automatically reconcile resources created by the Helm chart

---

#### 3. Dragonfly Operator (Redis-Compatible Cache)
Required for Dragonfly high-performance cache.

**Installation (Cluster-Wide):**

**IMPORTANT:** If you encounter a CRD ownership error from a previous installation, follow these steps first:

```bash
# If you get an error about existing CRD with wrong ownership metadata:
# 1. Uninstall any existing dragonfly-operator releases
helm uninstall dragonfly-operator -n dragonfly-operator-system 2>/dev/null || true

# 2. Remove Helm metadata from the CRD
kubectl patch crd dragonflies.dragonflydb.io \
  -p '{"metadata":{"annotations":{"meta.helm.sh/release-name":null,"meta.helm.sh/release-namespace":null},"labels":{"app.kubernetes.io/managed-by":null}}}' \
  --type=merge

# 3. Add correct metadata for your target namespace (e.g., openshift-operators)
kubectl patch crd dragonflies.dragonflydb.io \
  -p '{"metadata":{"annotations":{"meta.helm.sh/release-name":"dragonfly-operator","meta.helm.sh/release-namespace":"openshift-operators"},"labels":{"app.kubernetes.io/managed-by":"Helm"}}}' \
  --type=merge
```

**Installation to openshift-operators namespace:**
```bash
# Install via Helm to openshift-operators namespace
helm install dragonfly-operator \
  oci://ghcr.io/dragonflydb/dragonfly-operator/helm/dragonfly-operator \
  --version v1.1.10 \
  -f k8s/manifest/openshift/dragonfly-operator-values.yaml \
  -n openshift-operators
```

**dragonfly-operator-values.yaml:**
```yaml
replicaCount: 1
manager:
  resources:
    requests:
      cpu: 100m
      memory: 200Mi
    limits:
      cpu: 1000m
      memory: 2000Mi
  # Watch the jamaibase namespace for Dragonfly resources
  watchNamespace: jamaibase
serviceMonitor:
  enabled: true
  labels:
    scrape-by: vmagent
grafanaDashboard:
  enabled: true
  folder: dragonfly
  # -- Grafana dashboard configmap annotations.
  annotations:
    name: dragonfly_folder
  # -- Grafana dashboard configmap labels
  labels:
    name: dragonfly_dashboard
```

**Apply configuration updates:**
```bash
# Apply the updated values to the running operator
helm upgrade dragonfly-operator \
  oci://ghcr.io/dragonflydb/dragonfly-operator/helm/dragonfly-operator \
  --version v1.1.10 \
  -f k8s/manifest/openshift/dragonfly-operator-values.yaml \
  -n openshift-operators
```

# Verify installation
kubectl get pods -n openshift-operators | grep dragonfly

# Verify CRD is registered
kubectl get crd dragonflies.dragonflydb.io
```

---

**IMPORTANT: Apply Security Context Constraints (SCC)**

Dragonfly containers run with UID/GID 999, which requires special SCC permissions in OpenShift. You must apply the SCC before deploying Dragonfly instances:

```bash
# Apply the jamaibase SCC
kubectl apply -f k8s/manifest/openshift/jamaibase-scc.yaml

# Add the default service account to the SCC
kubectl patch scc jamaibase-scc --type='json' \
  -p='[{"op": "add", "path": "/users/-", "value": "system:serviceaccount:jamaibase:default"}]'

# Verify SCC was created
kubectl get scc jamaibase-scc
```

**Note:** The `jamaibase-scc` allows containers to run with UID/GID 999-2000, which is required for Dragonfly and other Jamaibase components.

---

**Deploy Dragonfly Instance:**

After installing the operator and applying the SCC, deploy a Dragonfly instance:

```bash
# Deploy Dragonfly with 2 replicas
kubectl apply -f k8s/manifest/openshift/dragonfly-replica-deploy.yaml -n jamaibase

# Verify Dragonfly pods are running
kubectl get pods -n jamaibase -l app.kubernetes.io/name=dragonfly

# Check Dragonfly service
kubectl get svc -n jamaibase dragonfly
```

**Expected output:**
```
NAME          READY   STATUS    RESTARTS   AGE
dragonfly-0   1/1     Running   0          30s
dragonfly-1   1/1     Running   0          15s
```

**Documentation:** https://dragonflydb.github.io/dragonfly-operator/

---

#### 4. ClickHouse Operator
Required for ClickHouse analytical database.

**Installation (Cluster-Wide):**
```bash
# Install via Helm to openshift-operators namespace
helm repo add clickhouse https://docs.altinity.com/clickhouse-operator/
helm install clickhouse-operator clickhouse-operator/clickhouse-operator \
  --namespace openshift-operators \
```

```bash
helm upgrade clickhouse-operator clickhouse-operator/altinity-clickhouse-operator \
  -n clickhouse-operator-system \
  -f clickhouse-operator-values.yaml
```
# apply clickhouse operator values
clickhouse-operator-values.yaml
```yaml
configs:
  files:
    config.yaml:
      watch:
        namespaces:
          - jamaibase
          - tokenvisor
serviceMonitor:
  enabled: true
  additionalLabels:
    scrape-by: vmagent
dashboards:
  enabled: true
  additionalLabels:
    grafana_dashboard: "clickhouse"
  annotations: {}
  grafana_folder: clickhouse
```

# Verify installation
```bash
kubectl get pods -n openshift-operators | grep clickhouse
```
**Documentation:** https://github.com/Altinity/clickhouse-operator

---

#### 5. CloudNativePG Operator (PostgreSQL)
Required for PostgreSQL database management.

```bash
# Install via OpenShift Subscription (cluster-wide)
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: cnpg-global-operator-group
  namespace: openshift-operators
spec:
  targetNamespaces:
  - "*"  # All namespaces
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: cloudnative-pg
  namespace: openshift-operators
spec:
  channel: stable-v1
  installPlanApproval: Automatic
  name: cloudnative-pg
  source: certified-operators
  sourceNamespace: openshift-marketplace
  startingCSV: cloudnative-pg.v1.22.0
EOF
```

**IMPORTANT: Pull Secret Required**

The custom PostgreSQL image (`ghcr.io/embeddedllm/cnpg-postgresql:17.5`) is hosted in a private registry and requires authentication. Before deploying the Helm chart:

1. **Create a GitHub Personal Access Token** with `read:packages` scope at https://github.com/settings/tokens
2. **Create the image pull secret** in the `jamaibase` namespace:
   ```bash
   kubectl create secret docker-registry github-registry-secret \
     --docker-server=ghcr.io \
     --docker-username=YOUR_GITHUB_USERNAME \
     --docker-password=YOUR_GITHUB_TOKEN \
     --namespace=jamaibase
   ```
3. The Helm chart will automatically create the ImageCatalog in your deployment namespace and reference this secret

This custom PostgreSQL image includes additional extensions and optimizations for the Jamaibase platform.

# Verify installation
```bash
kubectl get pods -n openshift-operators | grep cloudnative-pg
```
---

#### 6. SeaweedFS Operator (S3-Compatible Storage) or bring your own s3
Required for object storage.

**Installation (Cluster-Wide):**
```bash
# Install via Helm
helm repo add seaweedfs https://seaweedfs.github.io/seaweedfs/helm
helm install seaweedfs-operator seaweedfs/seaweedfs \
  --namespace seaweedfs-system \
  --create-namespace \
  --set controller.watchNamespace="*"  # Watch all namespaces

# Verify installation
kubectl get pods -n seaweedfs-system
```

**Documentation:** https://github.com/seaweedfs/seaweedfs

---

### Verify All Operators
Before deploying Jamaibase, verify all operators are running:

```bash
# For OpenShift - check all required operators in openshift-operators namespace
oc get pods -n openshift-operators | grep -E "cloudnative-pg|clickhouse|dragonfly|prometheus-operator|victoria-metrics-operator"

# Check CRDs are registered for all operators
oc get crd | grep -E "cluster.postgresql|clickhouse|dragonfly|podmonitor|servicemonitor|vmagent|vmauth|vmuser|vmcluster|vmpodscrape|vmnodescrape|victorialogs|seaweed"

# Expected CRDs:
# CloudNativePG: clusters.cnpg.io, poolers.cnpg.io
# ClickHouse: clickhouseoperatorconfigs.clickhouse.altinity.com, clickhouseinstallations.clickhouse.altinity.com
# Dragonfly: dragonflies.dragonflydb.io
# Prometheus: podmonitors.monitoring.coreos.com, servicemonitors.monitoring.coreos.com
# VictoriaMetrics: vmagents.victoriametrics.com, vmauths.victoriametrics.com, vmusers.victoriametrics.com, vmclusters.victoriametrics.com, vmpodscrapes.victoriametrics.com, vmnodescrapes.victoriametrics.com, victorialogs.victoriametrics.com
# SeaweedFS: seaweedfs.seaweedfs.com (if using operator)
```

### Cluster Requirements
- **OpenShift 4.8+** or **Kubernetes 1.24+**
- **Minimum 8 CPU cores** and **16GB RAM** for full deployment
- **100GB+** available storage for all components
- **Helm 3.8+** installed locally
- **NVIDIA GPU nodes** with CUDA support (REQUIRED for Docling by default)
  - NVIDIA GPU Operator should be installed to manage GPU drivers and labels
  - See [GPU Requirements](#gpu-requirements-required-for-docling) below for details

### Storage Requirements
The cluster manager must provide **Persistent Volumes** for the following components:

| Component | Storage Size | Storage Class | Purpose |
|-----------|-------------|---------------|---------|
| PostgreSQL | 20Gi+ | RWX/ReadWriteOnce | Application database |
| ClickHouse | 50Gi+ | RWX/ReadWriteOnce | Analytics and logs |
| SeaweedFS | 100Gi+ | RWX/ReadWriteMany | Object storage |
| VictoriaMetrics | 20Gi+ | RWX/ReadWriteOnce | Monitoring data |
| Dragonfly  | 1Gi+ | RWX/ReadWriteOnce | Cache persistence |

**Storage Configuration:**
Cluster managers should create StorageClasses before installation or configure existing ones in `values.yaml`:

```yaml
global:
  storageClass: "your-storage-class-name"

storage:
  classes:
    create: false  # Set to true if you want the chart to create StorageClasses
```

### GPU Requirements (REQUIRED for Docling)
For **Docling document processing**, GPU nodes are **REQUIRED** by default:
- **NVIDIA GPUs** with CUDA support and compute capability
- **NVIDIA GPU Operator** installed on the cluster (manages drivers, device plugins, and node labels)
- GPU nodes labeled by the NVIDIA GPU Operator
- At least 1 GPU per Docling pod (configurable via `docling.gpu.count`)

**Verifying GPU Setup:**
```bash
# Check if GPU nodes are available
kubectl get nodes -o json | jq '.items[].status.capacity["nvidia.com/gpu"]'

# Verify GPU operator has labeled nodes
kubectl get nodes -L nvidia.com/gpu.count -L nvidia.com/gpu.product

# Check NVIDIA device plugin pods
kubectl get pods -n nvidia-gpu-operator
```

**To run Docling in CPU-only mode** (not recommended for production):
```yaml
docling:
  gpu:
    enabled: false
```

**Note:** Docling performance is significantly better with GPU acceleration. CPU-only mode may result in 5-10x slower document processing and increased latency.

### Required Tools
```bash
# Install OpenShift CLI (if using OpenShift)
curl -LO "https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-client-linux.tar.gz"
tar -xzf openshift-client-linux.tar.gz
sudo mv oc /usr/local/bin/

# Install Helm
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/
```

### Docker Registry Access
You must have access to the private registry:
```bash
# Login to GitHub Container Registry
docker login ghcr.io
```

## 🚀 Installation

### 1. Prepare Namespace and Secrets (OpenShift Best Practices)

**Step 1: Create Namespace**
```bash
# Create namespace for Jamaibase
oc new-project jamaibase
```

**Step 2: Create Image Pull Secret**

The Jamaibase platform uses private container images hosted on GitHub Container Registry (ghcr.io). Create an image pull secret in the `jamaibase` namespace:

```bash
kubectl create secret docker-registry github-registry-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  --namespace=jamaibase
```

**Getting GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Create a new Personal Access Token (PAT)
3. Select `read:packages` scope
4. Use the token as `YOUR_GITHUB_TOKEN`

**Alternative: Using a YAML manifest**

You can also create the secret from a YAML file:

```bash
kubectl apply -f github-registry-secret-v8-kopi.yaml --namespace=jamaibase
```

**Alternative: Using the provided script**

```bash
# Edit apply-secret.bash with your credentials, then run:
bash apply-secret.bash
```

**Important Notes:**
- Secrets are namespace-scoped in Kubernetes/OpenShift
- The secret must be created in the same namespace where you deploy the Helm chart
- The jamaibase namespace secret is used by all application pods (OWL, Starling, Kopi, Docling, PostgreSQL)
- Do NOT use `--create-namespace` with Helm in OpenShift

### 2. Install Chart
```bash
# Navigate to chart directory
cd k8s/manifest/openshift/jamaibase-helm

# IMPORTANT: No need to run 'helm dependency update' - operators are managed separately
# All operators must be installed cluster-wide BEFORE running this command

# Install Jamaibase with image pull secret
helm install jamaibase . \
  --namespace jamaibase \
  --set global.imagePullSecrets[0].name=github-registry-secret \
  --wait \
  --timeout 15m
```

**Installation Options:**

**Option A: Using pre-created secret (Recommended)**
```bash
helm install jamaibase . \
  --namespace jamaibase \
  --set global.imagePullSecrets[0].name=github-registry-secret
```

**Option B: Using service account patching**
```bash
# Patch the default service account (do this before installing)
oc patch serviceaccount default -n jamaibase \
  -p '{"imagePullSecrets": [{"name": "github-registry-secret"}]}'

# Then install without specifying imagePullSecrets
helm install jamaibase . \
  --namespace jamaibase
```

### 3. Verify Installation
```bash
# Check pod status
oc get pods -n jamaibase

# Check services
oc get services -n jamaibase

# Check routes (OpenShift only)
oc get routes -n jamaibase
```

## ⚙️ Configuration

### Values Overview
Key configuration options in `values.yaml`:

```yaml
# Global settings
global:
  namespace: jamaibase
  imageRegistry: ghcr.io/embeddedllm
  imagePullSecret: github-registry-secret
  storageClass: openebs-hostpath

# Application components
jamaibase:
  owl:
    enabled: true
    replicaCount: 1
    resources:
      requests:
        cpu: "1000m"
        memory: "2Gi"
  jambu:
    enabled: true
    replicaCount: 1
    resources:
      requests:
        cpu: "500m"
        memory: "512Mi"
```

### Custom Installation
```bash
# Install with custom values
helm install jamaibase . \
  --namespace jamaibase \
  --set global.imagePullSecrets[0].name=github-registry-secret \
  --values custom-values.yaml \
  --set jamaibase.owl.replicaCount=3 \
  --set jamaibase.jambu.replicaCount=2
```

### Environment-Specific Values

#### Development
```yaml
# values-dev.yaml
jamaibase:
  owl:
    replicaCount: 1
    resources:
      requests:
        cpu: "200m"
        memory: "512Mi"
  jambu:
    replicaCount: 1
    resources:
      requests:
        cpu: "100m"
        memory: "256Mi"

openshift:
  enabled: false
```

#### Production
```yaml
# values-prod.yaml
jamaibase:
  owl:
    replicaCount: 3
    resources:
      requests:
        cpu: "2000m"
        memory: "4Gi"
      limits:
        cpu: "4000m"
        memory: "8Gi"
  jambu:
    replicaCount: 2
    resources:
      requests:
        cpu: "1000m"
        memory: "1Gi"
      limits:
        cpu: "2000m"
        memory: "2Gi"

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true

podDisruptionBudgets:
  enabled: true
  minAvailable: 1
```

## 🧩 Components

### OWL Backend
Python-based API server with Celery workers for background processing.

**Key Features:**
- RESTful API endpoints
- Celery task queue with beat scheduler
- OpenTelemetry instrumentation
- Health check endpoints
- ServiceAccount merged into deployment
- PodDisruptionBudgets for high availability
- ServiceMonitor integration for Prometheus/VictoriaMetrics
- OpenShift Route for external access

**Helm Templates:**
- [`templates/owl-secret.yaml`](templates/owl-secret.yaml) - Creates owl-secret with LLM provider API keys and Stripe configuration
- [`templates/owl-config.yaml`](templates/owl-config.yaml) - Creates owl-config and otel-collector-config ConfigMaps
- [`templates/owl-deployment.yaml`](templates/owl-deployment.yaml) - Creates owl-deployment, starling deployment, ServiceAccount, Service, and PodDisruptionBudgets
- [`templates/owl-servicemonitor.yaml`](templates/owl-servicemonitor.yaml) - Creates ServiceMonitor resources for monitoring
- [`templates/owl-route.yaml`](templates/owl-route.yaml) - Creates OpenShift Route for external access

**Configuration:**
```yaml
jamaibase:
  owl:
    enabled: true
    
    # Secret Configuration
    secret:
      enabled: true
      name: owl-secret
      # LLM Provider API Keys (set your actual keys)
      anthropicApiKey: ""
      azureApiKey: ""
      azureAiApiKey: ""
      bedrockApiKey: ""
      cerebrasApiKey: ""
      cohereApiKey: ""
      deepseekApiKey: ""
      ellmApiKey: ""
      geminiApiKey: ""
      groqApiKey: ""
      hyperbolicApiKey: ""
      jinaAiApiKey: ""
      openaiApiKey: ""  # Required
      openrouterApiKey: ""
      sagemakerApiKey: ""
      sambanovaApiKey: ""
      serviceKey: ""
      togetherAiApiKey: ""
      vertexAiApiKey: ""
      voyageApiKey: ""
      # Stripe Configuration
      stripeApiKey: ""
      stripePublishableKeyLive: ""
      stripePublishableKeyTest: ""
      stripeWebhookSecretLive: ""
      stripeWebhookSecretTest: ""
    
    # ConfigMap Configuration
    config:
      enabled: true
      name: owl-config
      otelConfigName: otel-collector-config
      
      # API Configuration
      dbPath: "postgresql+psycopg://owlpguser:owlpgpassword@jamaibase-pgbouncer.cnpg-operator-system.svc.cluster.local:5432/jamaibase_owl"
      host: "0.0.0.0"
      port: "6969"
      workers: "8"
      maxConcurrency: "300"
      dbInit: "True"
      dbReset: "False"
      dbInitMaxUsers: "1"
      cacheReset: "False"
      encryptionKey: "..."  # Set to a secure encryption key
      serviceKey: ""
      
      # Service Endpoints
      redisHost: "dragonfly.jamaibase.svc.cluster.local"
      redisPort: "6379"
      fileProxyUrl: "owl-api-route-jamaibase.apps.ellm-3.local.com"
      fileDir: "s3://file"
      s3Endpoint: "http://seaweedfs-s3.seaweedfs.svc.cluster.local:8333"
      s3AccessKeyId: "seaweedfsJamaibase"
      s3SecretAccessKey: "seaweedfsJamaibaseS3"
      codeExecutorEndpoint: "http://v8-kopi-server-service.v8-kopi.svc.cluster.local:8000"
      doclingUrl: "http://docling-server.jamaibase.svc.cluster.local:5001"
      doclingTimeoutSec: "20"
      
      # File Upload Limits
      embedFileUploadMaxBytes: "209715200"  # 200MiB
      imageFileUploadMaxBytes: "20971520"   # 20MiB
      audioFileUploadMaxBytes: "125829120"  # 120MiB
      
      # Timeouts
      computeStoragePeriodSec: "300"
      documentLoaderCacheTtlSec: "900"
      llmTimeoutSec: "3600"
      embedTimeoutSec: "3600"
      
      # Generative Table Configs
      concurrentRowsBatchSize: "3"
      concurrentColsBatchSize: "5"
      maxWriteBatchSize: "100"
      maxFileCacheSize: "20"
      
      # PDF Loader
      fastPdfParsing: "True"
      
      # Starling configs
      s3BackupBucketName: ""
      flushClickhouseBufferSec: "60"
      
      # OpenTelemetry Configuration
      otelHost: "localhost"
      otelPort: "4317"
      clickhouseHost: "clickhouse-jamaibase.jamaibase.svc.cluster.local"
      clickhousePort: "8123"
      victoriaMetricsHost: "vmauth-vmauth.jamaibase.svc.cluster.local"
      victoriaMetricsPort: "8427"
      victoriaMetricsUser: "vmuser"
      victoriaMetricsPassword: "jamaibase-vm-operator"
      victoriaLogsHost: "vls-victoria-logs-single-server.jamaibase.svc.cluster.local"
      victoriaLogsPort: "9428"
      serviceName: "owl"
      
      # OpenTelemetry Collector Exporters
      otel:
        victoriaMetricsEndpoint1: "http://vmagent-vmagent-agg-0.vmagent-owl-aggregate.jamaibase.svc:8429/opentelemetry"
        victoriaMetricsEndpoint2: "http://vmagent-vmagent-agg-1.vmagent-owl-aggregate.jamaibase.svc:8429/opentelemetry"
        clickhouseEndpoint: "http://clickhouse-jamaibase.jamaibase.svc.cluster.local:8123?dial_timeout=10s&compress=lz4&async_insert=1"
        clickhouseTtl: "24h"
        clickhouseDatabase: "jamaibase_owl"
        clickhouseTracesTable: "owl_traces"
        clickhouseUsername: "owluser"
        clickhousePassword: "owlpassword"
        victoriaLogsEndpoint1: "http://vls-victoria-logs-single-server-0.vls-victoria-logs-single-server.jamaibase.svc.cluster.local:9428/insert/opentelemetry/v1/logs"
        victoriaLogsEndpoint2: "http://vls-victoria-logs-single-server-1.vls-victoria-logs-single-server.jamaibase.svc.cluster.local:9428/insert/opentelemetry/v1/logs"
    
    # ServiceAccount
    serviceAccount:
      create: true
      name: owl
      annotations: {}
      automountToken: false
    
    # Service
    service:
      name: owl-api-server
      type: ClusterIP
      port: 6969
    
    # Deployment: owl-deployment (API Server)
    deployment:
      enabled: true
      name: owl-deployment
      replicas: 1
      image:
        repository: ghcr.io/embeddedllm/jamaibase/owl-openshift
        tag: "20251212"
        pullPolicy: Always
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      resources:
        requests:
          cpu: "1000m"
          memory: "2Gi"
        limits:
          cpu: "2000m"
          memory: "4Gi"
    
    # Deployment: starling (Celery Worker)
    starling:
      enabled: true
      deployment:
        name: starling
        replicas: 1
        image:
          repository: ghcr.io/embeddedllm/jamaibase/owl-openshift
          tag: "20251125"
          pullPolicy: Always
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
          runAsGroup: 1001
          fsGroup: 1001
        resources:
          requests:
            cpu: "1000m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
      autoscale:
        min: 2
        max: 4
        maxMemoryPerChild: "65536"
    
    # PodDisruptionBudgets
    podDisruptionBudget:
      enabled: true
      name: owl-pdb
      minAvailable: 1
    
    # ServiceMonitor
    serviceMonitor:
      enabled: true
      name: owl-servicemonitor
    
    # OpenShift Route
    route:
      enabled: true
      name: owl-api-server-route
      host: ""  # Set to your OpenShift route hostname
```

**Usage:**
```bash
# Install with default values
helm install jamaibase . \
  --namespace jamaibase \
  --set global.imagePullSecrets[0].name=github-registry-secret

# Install with custom values
helm install jamaibase . \
  --namespace jamaibase \
  -f values.yaml \
  -f values-owl.yaml
```

**Important Notes:**
- **Image Pull Secret**: The `github-registry-secret` must exist in the namespace before deployment (not created by Helm chart)
- **PostgreSQL Dependency**: OWL requires PostgreSQL to be ready. The chart uses Helm hooks to ensure proper startup order.
- **Starling Affinity**: Starling pods have pod affinity to co-locate with owl pods on the same node.
- **OpenTelemetry**: Both owl-deployment and starling include OpenTelemetry collector sidecars.
- **Monitoring**: ServiceMonitor resources are created for Prometheus/VictoriaMetrics integration when enabled.
- **OpenShift Route**: External access to OWL API is provided via OpenShift Route when enabled.

### Jambu Frontend
Node.js-based web interface for the Jamaibase platform.

**Key Features:**
- Modern web UI
- Authentication system
- Real-time updates
- Mobile-responsive design

**Configuration:**
```yaml
jamaibase:
  jambu:
    enabled: true
    replicaCount: 1
    image:
      repository: jamaibase-jambu
      tag: "latest"
    config:
      auth_secret: "changeme"
      owl_url: "http://owl-api-server:6969"
```

### V8-Kopi Code Execution System
Secure code execution system with isolated worker containers for running untrusted code safely.

**Key Features:**
- **Isolated Workers**: Each code execution runs in a separate container
- **Resource Limits**: Configurable CPU and memory constraints
- **Timeout Protection**: Automatic termination of long-running code
- **Queue Management**: Efficient request queuing and load balancing

**Configuration:**
```yaml
v8kopi:
  enabled: true
  namespace: v8-kopi  # Separate namespace for isolation

  # IMPORTANT: Update with your registry credentials
  registryAuth: "base64-encoded-username:password"

  server:
    replicaCount: 1
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
    config:
      maxQueueSize: "50"
      requestTimeout: "15"

  worker:
    replicaCount: 5  # Scale based on workload
    resources:
      requests:
        memory: "2Gi"  # Workers need significant memory
        cpu: "500m"
      limits:
        memory: "4Gi"
        cpu: "4000m"
    config:
      maxSizeBytes: "20971520"  # 20MB max code size
      timeoutMs: "10000"        # 10 second timeout
```

**Cluster Manager Requirements:**
- **Nodes with sufficient resources**: 4GB+ RAM per worker
- **Proper networking**: Workers need to communicate with server
- **Security**: RBAC permissions for pod management

### Docling Document Processing
GPU-enabled document processing service for OCR and document understanding.

**Key Features:**
- **OCR Capabilities**: Text extraction from PDFs, images, and documents
- **GPU Acceleration**: CUDA-enabled for high-performance processing (REQUIRED by default)
- **Multiple Formats**: Support for PDF, DOCX, DOC, JPG, PNG, TIFF
- **Health Monitoring**: Comprehensive health checks and monitoring

**⚠️ IMPORTANT: GPU Requirement**
By default, Docling requires NVIDIA GPU nodes for optimal performance:
- **GPU Nodes**: NVIDIA GPUs with CUDA drivers and compute capability
- **NVIDIA GPU Operator**: Should be installed to manage GPU drivers, device plugins, and node labels
- **GPU Resources**: At least 1 GPU per Docling pod

**Configuration:**
```yaml
docling:
  enabled: true

  gpu:
    enabled: true  # REQUIRED by default - set to false only for testing
    count: 1       # Number of GPUs per pod
    nodeSelectorLabel: nvidia.com/gpu.count  # GPU nodes managed by NVIDIA GPU Operator

  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

  config:
    maxFileSize: "52428800"      # 50MB max file size
    allowedFileTypes: "pdf,docx,doc,jpg,jpeg,png,tiff"
    cudaVisibleDevices: "0"      # Which GPU to use
```

**GPU Verification:**
```bash
# Check if GPU nodes are available
kubectl get nodes -o json | jq '.items[].status.capacity["nvidia.com/gpu"]'

# Verify GPU operator has labeled nodes
kubectl get nodes -L nvidia.com/gpu.count -L nvidia.com/gpu.product

# Check NVIDIA device plugin pods
kubectl get pods -n nvidia-gpu-operator
```

**CPU-Only Mode (Not Recommended):**
For testing or development only - performance will be significantly degraded:
```yaml
docling:
  gpu:
    enabled: false
  # Remove GPU node selector and tolerations
```

**Note:** CPU-only mode may result in 5-10x slower document processing and is not recommended for production workloads.

### OpenEBS Storage
Provides persistent storage with hostpath volumes.

**Configuration:**
```yaml
openebs:
  enabled: true
  engines:
    local:
      hostpath:
        enabled: true
  crds:
    csi:
      volumeSnapshots:
        enabled: false
```

### Dragonfly Cache
High-performance Redis-compatible cache.

**Configuration:**
```yaml
dragonfly:
  enabled: true
  dragonfly:
    replica:
      replicas: 1
      resources:
        requests:
          cpu: "200m"
          memory: "256Mi"
```

### ClickHouse Database
Analytical database for logs and time-series data.

**Configuration:**
```yaml
clickhouse:
  enabled: true
  cluster:
    name: "jamaibase-clickhouse"
    replicas: 1
    templates:
      - name: default
        configuration:
          compression:
            method: zstd
```

### CloudNativePG
PostgreSQL operator for relational data storage.

**IMPORTANT Prerequisites:**

1. **CloudNativePG Operator** must be installed cluster-wide (see [Prerequisites](#-prerequisites))

2. **Image Pull Secret** is required for custom PostgreSQL image:
   ```bash
   kubectl create secret docker-registry github-registry-secret \
     --docker-server=ghcr.io \
     --docker-username=YOUR_USERNAME \
     --docker-password=YOUR_GITHUB_TOKEN \
     --namespace=jamaibase
   ```

**Configuration:**
```yaml
postgresql:
  enabled: true
  
  # ImageCatalog Configuration (automatically created in deployment namespace)
  imageCatalog:
    enabled: true
    name: jamaibase-postgres
    image: ghcr.io/embeddedllm/cnpg-postgresql:17.5
  
  # PostgreSQL Cluster Configuration
  cluster:
    enabled: true
    name: jamaibase-postgresql-cluster
    instances: 1
    postgresqlMajorVersion: 17
    
    # PostgreSQL Parameters
    parameters:
      max_connections: "100"  # Maximum concurrent connections
      max_locks_per_transaction: "512"
      pgroonga:
        enable_wal_resource_manager: "on"
    
    # Shared Preload Libraries
    sharedPreloadLibraries:
      - pgroonga_wal_resource_manager
      - pg_stat_statements
    
    # Bootstrap Configuration
    bootstrap:
      initdb:
        database: jamaibase_owl
        owner: owlpguser
        secret:
          name: pg-owl-user-secret
        postInitApplicationSQL:
          - "ALTER ROLE owlpguser SET deadlock_timeout = '5s';"
          - "CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;"
          - "CREATE EXTENSION IF NOT EXISTS pgroonga;"
    
    # Monitoring
    monitoring:
      enablePodMonitor: true
    
    # Storage
    storage:
      size: 10Gi
      storageClassName: openebs-hostpath  # Can be overridden by global.storageClass
  
  # PgBouncer Pooler Configuration
  pooler:
    enabled: true
    name: jamaibase-pgbouncer
    instances: 1
    type: rw  # rw (read-write) or ro (read-only)
    pgbouncer:
      poolMode: transaction
      parameters:
        max_client_conn: "1000"
        default_pool_size: "80"
        server_idle_timeout: "600"
        query_wait_timeout: "120"
        server_reset_query: "DISCARD ALL"
    monitoring:
      enablePodMonitor: true
  
  # Database Credentials
  credentials:
    username: owlpguser
    password: owlpgpassword  # In production, use external secret management
```

**Configuration Options:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL deployment | `true` |
| `postgresql.imageCatalog.enabled` | Enable automatic ImageCatalog creation | `true` |
| `postgresql.imageCatalog.name` | ImageCatalog name | `"jamaibase-postgres"` |
| `postgresql.imageCatalog.image` | Custom PostgreSQL image | `"ghcr.io/embeddedllm/cnpg-postgresql:17.5"` |
| `postgresql.cluster.instances` | Number of PostgreSQL replicas | `1` |
| `postgresql.cluster.parameters.max_connections` | Max concurrent connections | `"100"` |
| `postgresql.cluster.storage.size` | PVC storage size | `"10Gi"` |
| `postgresql.cluster.storage.storageClassName` | Storage class name | `"openebs-hostpath"` |
| `postgresql.pooler.enabled` | Enable PgBouncer pooler | `true` |
| `postgresql.pooler.type` | Pooler type (rw/ro) | `"rw"` |
| `postgresql.pooler.pgbouncer.poolMode` | Pool mode (transaction/session/statement) | `"transaction"` |
| `postgresql.pooler.pgbouncer.parameters.max_client_conn` | Max client connections | `"1000"` |

**Production Considerations:**

1. **Secret Management**: Use external secret management (External Secrets Operator, HashiCorp Vault) instead of storing passwords in values.yaml:
   ```yaml
   postgresql:
     credentials:
       username: {{ .Values.postgresql.username }}
       password: {{ .Values.postgresql.password }}
   ```

2. **High Availability**: For production, increase instances to 3:
   ```yaml
   postgresql:
     cluster:
       instances: 3
   ```

3. **Resource Limits**: Define resource requests and limits:
   ```yaml
   postgresql:
     cluster:
       resources:
         requests:
           cpu: "1000m"
           memory: "2Gi"
         limits:
           cpu: "2000m"
           memory: "4Gi"
   ```

4. **Backup Strategy**: Configure scheduled backups using CloudNativePG Backup resources (not included in this chart - create separately).

5. **Storage Class**: Use production-grade storage classes with appropriate performance characteristics.

**Connection String:**

The OWL application connects to PostgreSQL via PgBouncer:
```yaml
jamaibase:
  owl:
    config:
      database_url: "postgresql://owlpguser:owlpgpassword@jamaibase-pgbouncer:5432/jamaibase_owl"
```

**Troubleshooting:**

```bash
# Check PostgreSQL cluster status
kubectl get cluster -n jamaibase

# Check ImageCatalog status (created automatically in deployment namespace)
kubectl get imagecatalog -n jamaibase

# Check PostgreSQL pods
kubectl get pods -n jamaibase -l cnpg.io/cluster=jamaibase-postgresql-cluster

# Check PgBouncer status
kubectl get pooler -n jamaibase

# View PostgreSQL logs
kubectl logs -n jamaibase -l cnpg.io/cluster=jamaibase-postgresql-cluster -c postgres

# Connect to PostgreSQL
kubectl exec -it -n jamaibase jamaibase-postgresql-cluster-1 -- psql -U owlpguser -d jamaibase_owl
```

### VictoriaMetrics
Time-series database for monitoring and observability.

**Configuration:**
```yaml
victoriaMetrics:
  enabled: true
  logs:
    enabled: true
    spec:
      retentionPeriod: "14d"
      storage:
        requests:
          storage: 20Gi
```

### SeaweedFS
S3-compatible object storage for file management.

**Configuration:**
```yaml
seaweedfs:
  enabled: true
  volume:
    replicaCount: 1
    volumeSize: 50Gi
  seaweedfs:
    s3:
      enabled: true
  job:
    enabled: true
    bucketName: "jamaibase"
```

## 🔄 Upgrading

### Upgrade Chart
```bash
# IMPORTANT: No need to run 'helm dependency update' - operators are managed separately

# Upgrade to latest version
helm upgrade jamaibase . \
  --namespace jamaibase \
  --values custom-values.yaml
```

### Rollback
```bash
# List revision history
helm history jamaibase -n jamaibase

# Rollback to previous version
helm rollback jamaibase 1 -n jamaibase
```

### Zero-Downtime Upgrades
The chart includes rolling update strategies and PodDisruptionBudgets for zero-downtime upgrades:

```yaml
podDisruptionBudgets:
  enabled: true
  minAvailable: 1
```

## 🗑️ Uninstallation

### Remove Chart
```bash
# Uninstall Jamaibase
helm uninstall jamaibase -n jamaibase

# Remove namespace (optional)
oc delete namespace jamaibase
```

### Clean Up Resources
```bash
# Remove PVCs (WARNING: This deletes data!)
oc get pvc -n jamaibase
oc delete pvc --all -n jamaibase

# Remove monitoring resources (if installed)
kubectl delete servicemonitor --all -n jamaibase
```

## 🔍 Troubleshooting

### Common Issues

#### Pods Not Starting
```bash
# Check pod status and events
oc describe pod <pod-name> -n jamaibase

# Check pod logs
oc logs <pod-name> -n jamaibase --follow

# Check resource constraints
oc describe node <node-name>
```

#### Image Pull Issues
```bash
# Verify image pull secret
oc get secret github-registry-secret -n jamaibase -o yaml

# Test image pull manually
oc run test-pod --image=ghcr.io/embeddedllm/jamaibase-owl:latest --dry-run=client -o yaml
```

#### Storage Issues
```bash
# Check storage classes
oc get storageclass

# Check PVC status
oc get pvc -n jamaibase
oc describe pvc <pvc-name> -n jamaibase
```

#### Network Issues
```bash
# Test service connectivity
oc exec -it <pod-name> -n jamaibase -- curl http://owl-api-server:6969/api/health

# Check network policies
oc get networkpolicy -n jamaibase
```

### Debug Mode
Enable debug logging:

```bash
helm upgrade jamaibase . \
  --namespace jamaibase \
  --set global.logLevel=debug \
  --set monitoring.enabled=true
```

### Resource Monitoring
```bash
# Monitor resource usage
oc top pods -n jamaibase
oc top nodes

# Check resource quotas
oc describe quota -n jamaibase
```

## 📊 Monitoring and Observability

### Built-in Monitoring
The chart includes comprehensive monitoring:

- **OpenTelemetry** for distributed tracing
- **Prometheus** metrics collection
- **Grafana** dashboards
- **VictoriaMetrics** for long-term storage

### Access Monitoring
```bash
# Check ServiceMonitors
oc get servicemonitor -n jamaibase

# Check PrometheusRule alerts
oc get prometheusrule -n jamaibase

# Access Grafana (if installed)
oc port-forward svc/grafana 3000:3000 -n monitoring
```

### Key Metrics
- **Application**: Request rate, response time, error rate
- **Infrastructure**: CPU, memory, disk usage
- **Database**: Connection count, query performance
- **Cache**: Hit rate, eviction rate

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd JAM.ai.dev/k8s/manifest/openshift/jamaibase

# Install Helm plugins for linting
helm plugin install https://github.com/helm-unittest/helm-unittest
helm plugin install https://github.com/instrumenta/helm-lint

# Run tests
helm unittest ./
helm lint .
```

### Chart Structure
```
jamaibase/
├── Chart.yaml                 # Chart metadata and dependencies
├── values.yaml               # Default configuration values
├── values-prod.yaml          # Production overrides
├── values-dev.yaml           # Development overrides
├── templates/
│   ├── _helpers.tpl          # Template helpers
│   ├── owl-deployment.yaml   # OWL backend deployment
│   ├── jambu-deployment.yaml # Jambu frontend deployment
│   ├── services.yaml         # Service definitions
│   ├── configmaps.yaml       # Configuration maps
│   ├── serviceaccounts.yaml  # Service accounts and RBAC
│   ├── poddisruptionbudgets.yaml # PDB definitions
│   ├── monitoring.yaml       # Monitoring and alerting
│   ├── openshift.yaml        # OpenShift-specific resources
│   └── NOTES.txt             # Installation notes
└── charts/                   # Subcharts directory
```

### Submitting Changes
1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests if applicable
5. Submit pull request with detailed description

## 📄 License

This chart is licensed under the same license as the Jamaibase project. Please see the main repository for licensing details.

## 🆘 Support

For support and questions:

1. **Documentation**: Check this README and inline comments
2. **Issues**: Create GitHub issue with detailed description
3. **Community**: Join our Slack/Discord channels
4. **Enterprise**: Contact sales for enterprise support

## 🔄 Version Compatibility

| Chart Version | App Version | OpenShift | Kubernetes |
|---------------|-------------|-----------|------------|
| 0.1.0         | 1.0.0       | 4.8+      | 1.24+      |

### Upgrade Path
- **0.1.x**: Current stable version
- **0.2.x**: Upcoming features (breaking changes possible)

---

**Note**: This chart is actively maintained and updated. Please check for new releases regularly.