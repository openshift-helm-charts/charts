# Operator Installation

This chart requires operators to be installed **before** Helm install.

## OpenShift OperatorHub Operators

The following operators can be installed via the OpenShift OperatorHub (recommended) or via Helm:

### Victoria Metrics Operator

**Installation Options:**
- **Recommended:** Install via OpenShift OperatorHub - already installed in `openshift-operators` namespace
- **Alternative:** Helm installation (see below)

### CloudNativePG

**Installation Options:**
- **Recommended:** Install via OpenShift OperatorHub - already installed in `openshift-operators` namespace
- **Alternative:** Helm installation (see below)

## Helm-Installed Operators

The following operators must be installed via Helm:

## ServiceMonitor/PodMonitor CRDs

```bash
kubectl apply -f https://github.com/prometheus-operator/prometheus-operator/releases/download/v0.87.1/stripped-down-crds.yaml
```

## Victoria Metrics Operator (Helm Installation)

**Alternative to OpenShift OperatorHub installation**

```bash
cat <<'YAML' > vm-operator-values.yaml
replicaCount: 1
crds:
  cleanup:
    enabled: true
serviceMonitor:
  enabled: true
  extraLabels:
    scrape-by: vmagent
resources:
  limits:
    cpu: 500m
    memory: 500Mi
  requests:
    cpu: 100m
    memory: 150Mi
YAML

helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
kubectl create ns vm-operator-system
helm install vmoperator vm/victoria-metrics-operator -f vm-operator-values.yaml -n vm-operator-system
```

## CloudNativePG (Helm Installation)

**Alternative to OpenShift OperatorHub installation**

```bash
cat <<'YAML' > cnpg-operator-values.yaml
replicaCount: 1
monitoring:
  podMonitorEnabled: true
  podMonitorAdditionalLabels:
    scrape-by: vmagent
  grafanaDashboard:
    create: true
YAML

helm repo add cnpg https://cloudnative-pg.github.io/charts
kubectl create ns cnpg-operator-system
helm upgrade --install cnpg -n cnpg-operator-system cnpg/cloudnative-pg -f cnpg-operator-values.yaml
```

## Dragonfly Operator

```bash
cat <<'YAML' > dragonfly-operator-values.yaml
replicaCount: 1
manager:
  resources:
    requests:
      cpu: 100m
      memory: 200Mi
    limits:
      cpu: 1000m
      memory: 2000Mi
serviceMonitor:
  enabled: true
  labels:
    scrape-by: vmagent
grafanaDashboard:
  enabled: true
  folder: dragonfly
  annotations:
    name: dragonfly_folder
  labels:
    name: dragonfly_dashboard
YAML

kubectl create ns dragonfly-operator-system
helm upgrade -f dragonfly-operator-values.yaml -n dragonfly-operator-system --install dragonfly-operator \
  oci://ghcr.io/dragonflydb/dragonfly-operator/helm/dragonfly-operator --version v1.1.10
```

## ClickHouse Operator (Altinity)

```bash
cat <<'YAML' > clickhouse-operator-values.yaml
configs:
  files:
    config.yaml:
      watch:
        namespaces:
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
YAML

kubectl create ns clickhouse-operator-system
helm repo add clickhouse-operator https://docs.altinity.com/clickhouse-operator/
helm install clickhouse-operator clickhouse-operator/altinity-clickhouse-operator \
  -n clickhouse-operator-system -f clickhouse-operator-values.yaml
```

## Grafana Operator (optional)

```bash
cat <<'YAML' > grafana-operator-values.yaml
serviceMonitor:
  enabled: true
  additionalLabels:
    scrape-by: vmagent
dashboard:
  enabled: true
YAML

kubectl create ns grafana-operator-system
helm upgrade -i grafana-operator oci://ghcr.io/grafana/helm-charts/grafana-operator \
  --version v5.17.0 -f grafana-operator-values.yaml -n grafana-operator-system
```

## Fluent Operator (optional)

```bash
cat <<'YAML' > fluent-operator-values.yaml
containerRuntime: containerd
Kubernetes: false
YAML

helm repo add fluent https://fluent.github.io/helm-charts
helm upgrade --install fluent-operator fluent/fluent-operator \
  -f fluent-operator-values.yaml -n fluent-operator-system --create-namespace
```
