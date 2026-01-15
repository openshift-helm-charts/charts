# Customization

Below are the most common values you may want to change.

## Images / tags

```yaml
emu:
  image: ghcr.io/embeddedllm/tokenvisor-emu:<tag>
starling:
  image: ghcr.io/embeddedllm/tokenvisor-emu:<tag>
studio:
  image: ghcr.io/embeddedllm/tokenvisor-studio:<tag>
```

## Studio hostnames

```yaml
studio:
  config:
    HOST: "studio.example.com"
    ORIGIN: "https://studio.example.com"
```

## Studio theme + logos

The chart ships with the **default theme** from `k8s/manifest/studio-theme-config.yaml`. Logos are optional and only needed if you want custom branding. `theme.css` is a ConfigMap entry, and logos can be provided as either plain data or base64 in `binaryData`.

```yaml
studio:
  themeCss: |
    :root {
      --primary: 192 67% 32%;
    }
  # plain text files (stringData)
  logos:
    favicon.svg: "<svg ...>"
  # base64 files (binaryData)
  logosBinaryData:
    favicon.svg: "<base64>"
    favicon.svg.gz: "<base64>"
    favicon.svg.br: "<base64>"
```

## OpenShift Routes routing

The chart uses OpenShift Routes for external access:

```yaml
network:
  openshiftRoutes:
    enabled: true
    clusterDomain: "apps.cluster.example.com"
    hostPrefix: "tokenvisor"
    tls:
      termination: edge
      insecureEdgeTerminationPolicy: Allow
    # ArgoCD route configuration (disabled by default to match main chart)
    argocd:
      enabled: false
      namespace: argocd
      serviceName: argocd-server
      port: 80
    # Victoria Metrics route configuration
    victoriaMetrics:
      enabled: true
      serviceName: vmauth-vmauth
      port: 8427
    # Victoria Logs route configuration
    victoriaLogs:
      enabled: true
      serviceName: vmauth-vmauth
      port: 8427
```

Route URLs follow the pattern:
`{service-name}-{hostPrefix}.{namespace}.{clusterDomain}`

For example:
- Studio Frontend: `studio-frontend-server-tokenvisor.tokenvisor.apps.cluster.example.com`
- EMU API: `emu-api-server-tokenvisor.tokenvisor.apps.cluster.example.com`
- VictoriaMetrics: `vmauth-vmauth-tokenvisor.tokenvisor.apps.cluster.example.com`

## Enable optional components

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

When Grafana is enabled, the chart installs TokenVisor dashboards plus operator/VM/VLogs dashboards.

## Skypilot

```yaml
skypilot:
  enabled: false
```

## Startup dependency waiters

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

If you manage ClickHouse schema yourself, either keep the required tables list in sync or disable the waiter.

## Secrets wiring

If your secret names/keys differ:

```yaml
emu:
  secretRefs:
    clickhouseSecretName: clickhouse-secret
    clickhousePasswordKey: db_user_password
    vmuserSecretName: vmuser-secret
    vmuserPasswordKey: password

grafana:
  adminSecret:
    name: grafana-secret
    key: admin_password
  clickhouseSecret:
    name: clickhouse-secret
    key: db_readonly_user_password
```
