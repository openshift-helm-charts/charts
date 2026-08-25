# Kubesense Helm Chart

Kubesense is a Kubernetes observability platform providing APM, distributed tracing, log aggregation, and infrastructure monitoring.

## Prerequisites

- Kubernetes 1.21+
- Helm 3.0+
- MySQL or PostgreSQL (external)
- ClickHouse (external)
- VictoriaMetrics (optional, external)

## Installation

```bash
helm install kubesense ./kubesense \
  --set secrets.jwtSecret=<your-jwt-secret> \
  --set config.database.host=<mysql-host> \
  --set config.database.source=<db-name> \
  --set config.database.username=<db-user> \
  --set secrets.databasePassword=<db-password> \
  --set config.tracesStore.host=<clickhouse-host> \
  --set secrets.tracesStorePassword=<clickhouse-password> \
  --set config.metricsStore.url=http://<victoria-metrics-host>:8428
```

## Configuration

The following table lists the configurable parameters and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `quay.io/guruprasad_kubesense/kubesense-api` |
| `image.tag` | Image tag | `1.0.0` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `3000` |
| `config.port` | Application port | `3000` |
| `config.apiRateLimit` | API rate limit per minute | `600` |
| `config.database.driver` | Primary DB driver (`mysql` or `postgres`) | `mysql` |
| `config.database.host` | Primary DB host | `""` |
| `config.database.port` | Primary DB port | `3306` |
| `config.database.source` | Primary DB name | `""` |
| `config.database.username` | Primary DB username | `""` |
| `config.tracesStore.host` | ClickHouse host | `""` |
| `config.tracesStore.port` | ClickHouse port | `9000` |
| `config.metricsStore.enabled` | Enable VictoriaMetrics | `true` |
| `config.metricsStore.url` | VictoriaMetrics URL | `""` |
| `config.logger.level` | Log level | `info` |
| `config.alertmanager.enabled` | Enable Alertmanager integration | `false` |
| `secrets.jwtSecret` | JWT signing secret | `""` |
| `secrets.databasePassword` | Primary DB password | `""` |
| `secrets.tracesStorePassword` | ClickHouse password | `""` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `256Mi` |

## Security

- Runs as non-root user (UID 1001), compatible with OpenShift's restricted SCC
- `allowPrivilegeEscalation: false`
- All capabilities dropped
- Sensitive values stored in a Kubernetes Secret

## Health Checks

Liveness and readiness probes are configured on `GET /api/health`.

## Uninstalling

```bash
helm uninstall kubesense
```
