# Expanso Edge Compute - Helm Chart

[![Docker Repository on Quay](https://quay.io/repository/expanso/expanso-edge/status "Docker Repository on Quay")](https://quay.io/repository/expanso/expanso-edge)
![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square)
![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square)
![AppVersion: 1.4.0](https://img.shields.io/badge/AppVersion-1.4.0-informational?style=flat-square)

Expanso Edge Compute Node for edge computing workloads on Kubernetes and OpenShift.

## Description

This Helm chart deploys the Expanso Edge compute node, enabling distributed computing across edge infrastructure. The compute node executes workloads on edge devices and connects to the Expanso Cloud orchestrator.

## Prerequisites

- Kubernetes 1.19+ or OpenShift 4.10+
- Helm 3.8+
- PodSecurityPolicy or Pod Security Standards support (optional)

## Installation

### Quick Start

```bash
helm install expanso-edge oci://quay.io/expanso/helm/expanso-edge
```

### From Local Chart

```bash
helm install expanso-edge ./expanso-edge
```

### With Custom Values

```bash
helm install expanso-edge ./expanso-edge \
  --set expansoEdge.bootstrap.token=YOUR_BOOTSTRAP_TOKEN \
  --set expansoEdge.orchestrators[0]=nats://your-orchestrator:4222
```

### From Values File

```bash
helm install expanso-edge ./expanso-edge -f values.yaml
```

## Configuration

The following table lists the configurable parameters of the Expanso Edge Compute chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `quay.io/expanso/expanso-edge` |
| `image.tag` | Container image tag | `1.4.0-ubi9` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `replicaCount` | Number of replicas | `1` |
| `expansoEdge.version` | Expanso Edge version | `1.4.0` |
| `expansoEdge.nodeType` | Node type (compute/orchestrator) | `compute` |
| `expansoEdge.apiHost` | API host binding | `0.0.0.0` |
| `expansoEdge.apiPort` | API port | `1234` |
| `expansoEdge.bootstrap.url` | Bootstrap URL | `https://start.cloud.expanso.io` |
| `expansoEdge.bootstrap.token` | Bootstrap token | `""` |
| `expansoEdge.orchestrators` | List of orchestrator URLs | `["nats://expanso-orchestrator:4222"]` |
| `expansoEdge.labels` | Compute node labels | See values.yaml |
| `expansoEdge.jobSelection.locality` | Job locality preference | `anywhere` |
| `expansoEdge.logging.level` | Log level | `info` |
| `resources.requests.cpu` | CPU request | `1000m` |
| `resources.requests.memory` | Memory request | `2Gi` |
| `resources.limits.cpu` | CPU limit | `2000m` |
| `resources.limits.memory` | Memory limit | `4Gi` |
| `service.enabled` | Enable Service | `true` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `1234` |
| `serviceAccount.create` | Create service account | `true` |
| `serviceAccount.name` | Service account name | `""` |
| `nodeSelector` | Node selector labels | `{}` |
| `tolerations` | Pod tolerations | `[]` |
| `affinity` | Pod affinity rules | `{}` |

## Examples

### Basic Deployment

```yaml
# values.yaml
expansoEdge:
  bootstrap:
    token: "your-bootstrap-token-here"
  orchestrators:
    - "nats://orchestrator.example.com:4222"
```

### Production Deployment with Custom Resources

```yaml
# values-production.yaml
replicaCount: 3

resources:
  requests:
    cpu: 2000m
    memory: 4Gi
  limits:
    cpu: 4000m
    memory: 8Gi

expansoEdge:
  bootstrap:
    url: "https://start.cloud.expanso.io"
  orchestrators:
    - "nats://orchestrator1.example.com:4222"
    - "nats://orchestrator2.example.com:4222"
  labels:
    environment: "production"
    region: "us-east-1"
    cloud: "openshift"
  logging:
    level: "info"

nodeSelector:
  node-role.kubernetes.io/edge: "true"

tolerations:
  - key: "edge"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

### Using Secrets for Bootstrap Token

Instead of setting the token in values, create a secret:

```bash
kubectl create secret generic expanso-edge-bootstrap \
  --from-literal=token=YOUR_BOOTSTRAP_TOKEN
```

Then deploy without specifying the token in values.yaml:

```bash
helm install expanso-edge ./expanso-edge
```

## Upgrading

### From Chart Version 1.0.0 to 1.1.0

```bash
helm upgrade expanso-edge ./expanso-edge \
  --reuse-values \
  --version 1.1.0
```

### Changing Configuration

```bash
helm upgrade expanso-edge ./expanso-edge \
  --set expansoEdge.logging.level=debug
```

## Uninstalling

```bash
helm uninstall expanso-edge
```

## Troubleshooting

### Pod Not Starting

Check pod status:
```bash
kubectl get pods -l app.kubernetes.io/name=expanso-edge
kubectl describe pod -l app.kubernetes.io/name=expanso-edge
```

Check logs:
```bash
kubectl logs -l app.kubernetes.io/name=expanso-edge
```

### Cannot Connect to Orchestrator

Verify orchestrator URL is correct:
```bash
kubectl get configmap -o yaml | grep orchestrators
```

Test network connectivity:
```bash
kubectl exec -it <pod-name> -- curl -v nats://orchestrator:4222
```

### API Endpoint Not Responding

Port-forward to access locally:
```bash
kubectl port-forward svc/expanso-edge 1234:1234
curl http://localhost:1234/api/v1/agent/alive
```

## OpenShift Specific Configuration

### Security Context Constraints (SCC)

The chart runs as non-root user (UID 1000) and should work with the `restricted` SCC.

For custom SCC requirements:

```yaml
serviceAccount:
  create: true
  annotations:
    openshift.io/scc: restricted
```

### Routes (Instead of Ingress)

OpenShift uses Routes instead of Ingress. To expose the service:

```bash
oc expose svc/expanso-edge
```

## Support

- Documentation: https://expanso.io/docs
- Issues: https://github.com/expanso/expanso-edge/issues
- Email: support@expanso.io

## License

Apache License 2.0

## Maintainers

| Name | Email |
|------|-------|
| Expanso Team | support@expanso.io |

## Source Code

- https://github.com/expanso/expanso-edge

## Red Hat Certification

This Helm chart and container image are certified for Red Hat OpenShift.

- Container Certification: [Pending]
- Helm Chart Certification: [Pending]
- Available on Red Hat Marketplace: [Pending]
