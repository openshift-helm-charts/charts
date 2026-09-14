Kamailio SBC Helm Chart

Overview
- Packages the Kamailio SBC workload for OpenShift/Kubernetes.
- Exposes SIP over UDP/TCP and optional TLS, plus a TCP health port.
- Supports two Service layouts: a single Service (mixed protocols) or split Services by protocol.

Chart Structure
- `Chart.yaml` — chart metadata (name, version, keywords, annotations).
- `values.yaml` — defaults for image, ports, Service options, probes, resources, and policies.
- `values-dev.yaml` — dev overrides for ROSA HCP (AWS). Uses NLB, Local traffic policy, and split Services.
- `values-prod.yaml` — production image/labels and any prod‑specific overrides.
- `values.schema.json` — JSON‑schema for values validation.
- `templates/_helpers.tpl` — helper templates for names, labels, and selectors.
- `templates/deployment.yaml` — Deployment with SIP and health ports exposed.
- `templates/configmap.yaml` — application configuration (env via ConfigMap).
- `templates/configmap-cfg.yaml` — mounted `kamailio.cfg` for the SBC image.
- `templates/service.yaml` — internal Service exposing UDP 5060 + TCP 5060/5061 when `service.splitByProtocol` is false.
- `templates/service-udp.yaml` — internal UDP Service (port 5060) when `service.splitByProtocol` is true.
- `templates/service-tcp.yaml` — internal TCP Service (ports 5060/5061) when `service.splitByProtocol` is true.
- `templates/serviceaccount.yaml`, `templates/hpa.yaml`, `templates/poddisruptionbudget.yaml`, `templates/networkpolicy.yaml`, `templates/NOTES.txt` — operational resources.
- `tests/*` — chart tests asserting labels, ports, and key resources.

Service Behavior
- `service.type` controls Service kind. Use `ClusterIP` for backend-only exposure behind `kamailio-proxy`.
- `service.externalTrafficPolicy: Local` preserves source IPs for SIP.
- `service.annotations` passes cloud‑LB settings (e.g., AWS NLB).
- `service.splitByProtocol`:
  - `false` (default): a single internal Service with UDP 5060 and TCP 5060/5061.
  - `true`: two internal Services are rendered: `<fullname>-udp` (UDP 5060) and `<fullname>-tcp` (TCP 5060/5061).

Backend Exposure
- The SBC is now backend-only behind `kamailio-proxy`.
- It still renders separate UDP/TCP Services when `service.splitByProtocol: true`, but they are `ClusterIP` services and are not externally load balanced.

Render and Validate
- Template:
  - `helm template apps/kamailio/chart -f apps/kamailio/chart/values-dev.yaml`
- Lint:
  - `helm lint apps/kamailio/chart`
- API (server) validation on a cluster:
  - `oc apply --dry-run=server -n cogvoice-sip-dev -f <(helm template apps/kamailio/chart -f apps/kamailio/chart/values-dev.yaml)`

Deploy (dev namespace example)
  - `helm upgrade --install kamailio apps/kamailio/chart -n cogvoice-sip-dev -f apps/kamailio/chart/values-dev.yaml`
- Verify Services:
  - `oc get svc -n cogvoice-sip-dev | grep kamailio` should list the internal backend services.

Notes
- If you need a stable in‑cluster name independent of protocol, you can add an internal `ClusterIP` Service and keep the cloud‑facing LBs split by protocol.

Config Mounting
- The chart mounts `kamailio.cfg` from a dedicated ConfigMap so the same image can be shared with `kamailio-proxy` while keeping different routing logic.

Troubleshooting
- EXTERNAL-IP pending (AWS NLB):
  - Ensure `service.type: LoadBalancer`, worker subnets are tagged for NLB, and annotations match your cluster (ROSA examples belong in values-dev.yaml).
  - On AWS, set `service.splitByProtocol: true` to avoid mixed protocol errors.
- Health checks failing but pod Ready:
  - Confirm `readinessProbe` checks the correct TCP health port and that NetworkPolicy allows it from kubelet/ELB.
- Permission denied starting Kamailio on OpenShift:
  - Images must run as non-root. Use an image that supports arbitrary UID and grant group write on runtime paths, or set `securityContext.fsGroup`.
- SIP not reaching pods (hostNetwork=false):
  - Verify NLB target health, security group ports (UDP/TCP 5060/5061), and that `externalTrafficPolicy: Local` is set if you rely on client IP.
- TLS 5061 not exposed:
  - Set `service.enableTls: true` and ensure certificates are mounted and referenced by Kamailio config.

Validation
- Template and lint prior to apply:
- `helm template apps/kamailio/chart -f apps/kamailio/chart/values-dev.yaml`
- `helm lint apps/kamailio/chart`
- `oc apply --dry-run=server -n <ns> -f <(helm template apps/kamailio/chart -f apps/kamailio/chart/values-dev.yaml)`

JSON-RPC HTTP notes
- The Deployment exposes container port `8033` as `rpc-http`; the Service publishes it as `rpc-http` on TCP 8033.
- The `jsonrpcs` module is enabled via `xhttp` on path `/RPC`. Ensure your NetworkPolicy permits egress to TCP 8033 from the dispatcher-sync CronJob.
