# prophaze-waf

Prophaze Web Application Firewall for Red Hat OpenShift.

## Prerequisites

- OpenShift 4.8 or later
- Helm 3.0 or later

## Installing

```bash
helm install my-waf ./prophaze-waf
```

## Uninstalling

```bash
helm uninstall my-waf
```

## Parameters

| Parameter | Default |
| --- | --- |
| replicaCount | 1 |
| image.repository | registry.access.redhat.com/ubi8/nginx-120 |
| image.tag | latest |
| service.type | ClusterIP |
| service.port | 80 |
