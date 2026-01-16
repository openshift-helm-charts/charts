# Prerequisites

TokenVisor requires a Kubernetes cluster with specific operators, CRDs, and storage already installed. The Helm chart **does not** install these.

## Cluster Requirements

- **At least 3 nodes**
- DNS + standard Kubernetes services
- Gateway API CRDs + Cilium Gateway controller
- Storage provider installed (OpenEBS or local-path)
- ServiceMonitor/PodMonitor CRDs

## Required Operators

- Victoria Metrics Operator (CRD: `operator.victoriametrics.com/v1beta1`)
- ClickHouse Operator (CRDs: `clickhouse-keeper.altinity.com/v1`, `clickhouse.altinity.com/v1`)
- CloudNativePG (CRD: `postgresql.cnpg.io/v1`)
- Dragonfly Operator (CRD: `dragonflydb.io/v1alpha1`)
- Grafana Operator (only if Grafana enabled)
- Fluent Operator (only if Fluent Bit enabled)

## Image Pull Secrets (GHCR)

If GHCR images are private, create the registry secret in each namespace that pulls images:

```bash
kubectl -n tokenvisor create secret docker-registry github-registry-secret \
  --docker-server=ghcr.io \
  --docker-username="<github-username>" \
  --docker-password="<github-token>" \
  --docker-email="<email>"

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

## Verify CRDs

```bash
kubectl api-resources --api-group=operator.victoriametrics.com
kubectl api-resources --api-group=clickhouse.altinity.com
kubectl api-resources --api-group=clickhouse-keeper.altinity.com
kubectl api-resources --api-group=postgresql.cnpg.io
kubectl api-resources --api-group=dragonflydb.io
kubectl api-resources --api-group=grafana.integreatly.org
kubectl api-resources --api-group=fluentbit.fluent.io
kubectl api-resources --api-group=gateway.networking.k8s.io
```

## Namespaces

Create required namespaces before install:

```bash
kubectl create namespace tokenvisor
kubectl create namespace skypilot
```

## GatewayClass ownership note

Cilium’s Helm install creates `GatewayClass/cilium` and owns it. The TokenVisor chart does **not** create the GatewayClass by default to avoid Helm ownership conflicts. If you want the chart to create it, set:

```yaml
network:
  gateway:
    createGatewayClass: true
```
