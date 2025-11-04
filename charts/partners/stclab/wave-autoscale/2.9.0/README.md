# Wave Autoscale Helm Chart

Wave Autoscale replaces HPA and VPA with AI-driven workload scaling, container rightsizing, and traffic shaping—cutting cloud costs, improving reliability, and simplifying Kubernetes operations.

## Overview

Wave Autoscale is an intelligent Kubernetes resource management solution that:
- Provides AI-driven workload autoscaling
- Optimizes container resource allocation (rightsizing)
- Implements intelligent traffic shaping
- Reduces cloud infrastructure costs
- Improves application reliability and performance

## Prerequisites

- Kubernetes 1.26.0+
- Helm 3.x
- OpenShift 4.8+ (for OpenShift deployments)
- Persistent Volume provisioner support in the underlying infrastructure
- Valid Wave Autoscale license key (contact [STCLab Inc.](https://waveautoscale.com) for licensing)

## Components

This Helm chart deploys the following components:

- **Wave Autoscale Core** - Main control plane and API server (port 3024)
- **Web Console** - Management and monitoring interface (port 3025)
- **Intelligence Module** - AI/ML engine for optimization decisions (port 3026)
- **Agent** - Node-level metrics collection via DaemonSet
- **cAdvisor** - Container metrics collection

## Installation

### Add Helm Repository

```bash
helm repo add openshift-helm-charts https://charts.openshift.io/
helm repo update
```

### Install from OpenShift Helm Repository
<!-- !REPLACE IMAGE LINKS WHEN WE HAVE CERTIFIED IMAGES! -->

```bash
helm install wave-autoscale openshift-helm-charts/wave-autoscale \
  --namespace wave-autoscale \
  --create-namespace \
  --set spec.core.image.repository=<your-image-repository> \
  --set spec.core.image.tag=<version> \
  --set spec.webConsole.image.repository=<your-image-repository> \
  --set spec.webConsole.image.tag=<version> \
  --set spec.intelligence.image.repository=<your-image-repository> \
  --set spec.intelligence.image.tag=<version> \
  --set license.key=<your-license-key>
```

### Install from Source

```bash
helm install wave-autoscale ./wave-autoscale \
  --namespace wave-autoscale \
  --create-namespace \
  --values custom-values.yaml
```

## Configuration

### Required Configuration

Before installation, you must configure:

1. **Container Images** - Set the repository and tag for all components:
   ```yaml
   spec:
     core:
       image:
         repository: <your-registry>/wave-autoscale-core
         tag: 2.9.0
     webConsole:
       image:
         repository: <your-registry>/wave-autoscale-console
         tag: 2.9.0
     intelligence:
       image:
         repository: <your-registry>/wave-autoscale-intelligence
         tag: 2.9.0
     agent:
       image:
         repository: <your-registry>/wave-autoscale-agent
         tag: 2.9.0
   ```

2. **License Key** - Set your Wave Autoscale license:
   ```yaml
   license:
     key: "<your-license-key>"
   ```

### Key Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `spec.core.image.repository` | Wave Autoscale core image repository | `$repository` (must be set) |
| `spec.core.image.tag` | Wave Autoscale core image tag | `$tag` (must be set) |
| `spec.core.resources.requests.cpu` | CPU request for core component | `1500m` |
| `spec.core.resources.requests.memory` | Memory request for core component | `1Gi` |
| `spec.webConsole.image.repository` | Web console image repository | `$repository` (must be set) |
| `spec.webConsole.image.tag` | Web console image tag | `$tag` (must be set) |
| `spec.intelligence.image.repository` | Intelligence module image repository | `$repository` (must be set) |
| `spec.intelligence.image.tag` | Intelligence module image tag | `$tag` (must be set) |
| `spec.agent.enabled` | Enable Wave Autoscale agent DaemonSet | `true` |
| `spec.agent.image.repository` | Agent image repository | `$repository` (must be set) |
| `spec.agent.image.tag` | Agent image tag | `$tag` (must be set) |
| `spec.pvcStorage` | Persistent volume size | `30Gi` |
| `spec.storageClassName` | Storage class name for PVC | `""` (default storage class) |
| `spec.existingPvcName` | Use existing PVC instead of creating new one | `""` |
| `license.key` | Wave Autoscale license key | `""` (required) |
| `license.mode` | License mode | `""` |
| `license.plan` | License plan | `""` |
| `default_namespace` | Default namespace when installed in 'default' | `wave-autoscale` |
| `serviceSpec.type` | Kubernetes service type | `ClusterIP` |
| `serviceSpec.core.port` | Core API service port | `3024` |
| `serviceSpec.webConsole.port` | Web console service port | `3025` |
| `serviceSpec.intelligence.port` | Intelligence module service port | `3026` |
| `ghcr.enabled` | Enable GitHub Container Registry secret | `false` |
| `ghcr.dockerconfigjson` | Base64 encoded Docker config JSON | `""` |
| `clusterRole.readOnly` | Use read-only cluster role | `false` |
| `clusterRole.istioAdmin` | Enable Istio admin permissions | `false` |

### OpenShift Specific Configuration

For OpenShift deployments, you may need to enable Security Context Constraints (SCC):

```yaml
openshift:
  waveAutoscale:
    scc:
      create: true
  waveAutoscaleAgent:
    scc:
      create: true
```

### Image Pull Secrets

If using a private registry, configure image pull secrets:

```yaml
ghcr:
  enabled: true
  dockerconfigjson: "<base64-encoded-docker-config>"
```

### Storage Configuration

#### Using Default Storage Class

```yaml
spec:
  pvcStorage: 30Gi
  storageClassName: ""  # Uses default storage class
```

#### Using Specific Storage Class

```yaml
spec:
  pvcStorage: 30Gi
  storageClassName: "gp2"  # AWS EBS gp2, for example
```

#### Using Existing PVC

```yaml
spec:
  existingPvcName: "my-existing-pvc"
```

### Resource Requests

Adjust resource requests based on your cluster size:

```yaml
spec:
  core:
    resources:
      requests:
        cpu: 1500m
        memory: 1Gi
  webConsole:
    resources:
      requests:
        cpu: 300m
        memory: 300Mi
  intelligence:
    resources:
      requests:
        cpu: 1000m
        memory: 2Gi
  agent:
    resources:
      requests:
        cpu: 100m
        memory: 50Mi
```

### Environment Variables

Core component environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `WA_LICENSE` | License key (overridden by license.key) | `""` |
| `WA_LOG_LEVEL` | Logging level (debug, info, warn, error) | `debug` |
| `WA_API_SERVER_HOST` | API server bind address | `0.0.0.0` |
| `WA_PLATFORM_K8S` | Enable Kubernetes platform mode | `true` |
| `WA_WAVE_SHAPER_MODULE_URL` | Wave Shaper module image URL | `public.ecr.aws/wave-autoscale/wave-shaper:0.1.3` |

Agent environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `WAA_LOG_LEVEL` | Agent logging level | `debug` |
| `WAA_WA_URI` | Wave Autoscale core API URL | `http://wave-autoscale-svc.wave-autoscale.svc.cluster.local:3024` |
| `WAA_CADVISOR_URI` | cAdvisor metrics endpoint | `http://0.0.0.0:8080/metrics` |

## Accessing Wave Autoscale

### Port Forward (Development)

```bash
# Access Core API
kubectl port-forward -n wave-autoscale svc/wave-autoscale-svc 3024:3024

# Access Web Console
kubectl port-forward -n wave-autoscale svc/wave-autoscale-svc 3025:3025

# Access Intelligence API
kubectl port-forward -n wave-autoscale svc/wave-autoscale-svc 3026:3026
```

Then access:
- Core API: http://localhost:3024
- Web Console: http://localhost:3025
- Intelligence API: http://localhost:3026

### OpenShift Route (Production)

Create an OpenShift route for the web console:

```bash
oc create route edge wave-autoscale-console \
  --service=wave-autoscale-svc \
  --port=3025 \
  -n wave-autoscale
```

Get the route URL:
```bash
oc get route wave-autoscale-console -n wave-autoscale
```

### Ingress (Kubernetes)

Create an ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wave-autoscale-ingress
  namespace: wave-autoscale
spec:
  rules:
  - host: wave-autoscale.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: wave-autoscale-svc
            port:
              number: 3025
```

## Upgrading

### Upgrade to New Version

```bash
helm upgrade wave-autoscale openshift-helm-charts/wave-autoscale \
  --namespace wave-autoscale \
  --values custom-values.yaml
```

### Rollback

```bash
helm rollback wave-autoscale -n wave-autoscale
```

## Uninstallation

```bash
helm uninstall wave-autoscale -n wave-autoscale
```

**Note:** By default, PersistentVolumeClaims are retained even after uninstallation to prevent data loss. To manually delete them:

```bash
kubectl delete pvc -n wave-autoscale -l app.kubernetes.io/name=wave-autoscale
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n wave-autoscale
```

### View Logs

```bash
# Core component logs
kubectl logs -n wave-autoscale -l app.kubernetes.io/component=core

# Web console logs
kubectl logs -n wave-autoscale -l app.kubernetes.io/component=core -c wave-autoscale-web-console

# Intelligence module logs
kubectl logs -n wave-autoscale -l app.kubernetes.io/component=core -c wave-autoscale-intelligence

# Agent logs
kubectl logs -n wave-autoscale -l app.kubernetes.io/name=wave-autoscale-agent
```

### Common Issues

#### Pods in CrashLoopBackOff

1. Check if license key is properly configured
2. Verify image repository and tag are correct
3. Check resource availability in the cluster
4. Review pod logs for specific errors

#### Storage Issues

1. Verify storage class exists and is available
2. Check PVC status: `kubectl get pvc -n wave-autoscale`
3. Ensure sufficient storage capacity in the cluster

#### Agent Not Collecting Metrics

1. Verify agent DaemonSet is running on all nodes
2. Check SCC permissions on OpenShift
3. Verify cAdvisor container is running

## Support

For issues, questions, or feature requests:
- Visit: https://waveautoscale.com
- Email: team@waveautoscale.com
- Documentation: https://waveautoscale.com/docs

## License

Wave Autoscale requires a valid license key. Contact STCLab Inc. for licensing information.

## Chart Information

- **Chart Version:** 2.9.0
- **App Version:** 2.9.0
- **Maintainer:** STCLab Inc.
- **Source Code:** Contact STCLab Inc. for access
