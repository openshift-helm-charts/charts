# vistergy-agent-server Helm chart

Deploys the Vistergy governed AI agent server for asset-intensive critical
infrastructure. Its agents are grounded in engineering
and asset-management standards: international, domain-specific, or the
owner's own. An optional read connection reaches IBM Maximo as the system
of record. Answers cite their grounding and never fabricate.

The chart targets Red Hat OpenShift 4.14 or later. Any Kubernetes 1.27 or
later also works, with `route.enabled=false`. The container image is Red Hat
certified and built on Red Hat Universal Base Image 9. It runs under
OpenShift's default `restricted-v2` Security Context Constraint, with an
arbitrary user ID in group 0. So no SCC exception is required.

## Licence and what Vistergy supplies

Vistergy Ltd licenses the server per client, under a licence agreement.
The licence notice is in `/licenses` in the image. With the
licence, Vistergy issues:

- agent API keys
- a corpus-reader key, with the corpus store's name, region and digest
- a key for Vistergy's model service, with its endpoint and region
- the outbound addresses your egress allowlist needs

You bring the OpenShift cluster, and optionally your own IBM Maximo.

## How data moves

- At each fresh start, the server fetches its corpus from Vistergy's store
  with the corpus-reader key. The corpus is the retrieval index and the
  standards and facility data the agents read. The copy is held in the
  pod's local storage, on your cluster, for the pod's lifetime.
- Each question to an agent goes to Vistergy's model service, outside your
  cluster, to be answered. Any Maximo context the question carries goes
  with it.
- The embedding model is baked into the image, so the cluster needs no
  route to a model hub.

The pod needs outbound HTTPS to the corpus store, its token service and the
model service. Without the first two, the server does not start.

## Prerequisites

The chart creates **no Secrets**. Create these in the release namespace
first and pass their names in values. Each Secret's keys become
environment variables, so the key names must be exactly as shown, or as
Vistergy supplies them:

| Secret | Purpose | Keys | Passed via |
|---|---|---|---|
| Image pull secret (optional) | Pull access to `registry.connect.redhat.com` | Standard pull secret | `imagePullSecrets` |
| Corpus reader | The key the server fetches its corpus with at start | `apikey` | `envFromSecrets` |
| Agent API keys | Per-client keys checked on every agent call | `VISTERGY_AGENT_KEYS` | `envFromSecrets` |
| Model service | Credentials for Vistergy's model service | The names Vistergy supplies | `envFromSecrets` |
| Maximo connection (optional) | Read access to IBM Maximo as the system of record | The names Vistergy supplies | `envFromSecrets` |

Set these variables in `env`:

| Variable | Purpose |
|---|---|
| `VISTERGY_AGENT_CORPUS_BUCKET` | The corpus store. The server does not start without it |
| `VISTERGY_AGENT_CORPUS_REGION` | The corpus store's region |
| `VISTERGY_ENV` | `production` |
| `VISTERGY_EXPECTED_CORPUS_DIGEST` | The digest of the corpus the server is meant to load. Production requires it, and the server refuses any other corpus. So whoever can write the corpus store cannot change what the server runs |
| `VISTERGY_AGENT_PUBLIC_URL` | The address clients reach the server at, usually its Route: `https://<route host>`, with no path |

The A2A agent card names `VISTERGY_AGENT_PUBLIC_URL`, so an A2A client
calls this install. Without it the card names `http://localhost:8080`, and
the server logs a warning at start. Any other form, a path or a query
included, turns the A2A endpoint off, also with a warning. The server reads
this variable from app version 1.62.

## Install

Put the values in a file, for example `my-values.yaml`:

```yaml
envFromSecrets:
  - vistergy-agent-keys
  - vistergy-model-service
  - vistergy-corpus-reader
env:
  - name: VISTERGY_AGENT_CORPUS_BUCKET
    value: <supplied by Vistergy>
  - name: VISTERGY_AGENT_CORPUS_REGION
    value: <supplied by Vistergy>
  - name: VISTERGY_ENV
    value: production
  - name: VISTERGY_EXPECTED_CORPUS_DIGEST
    value: <supplied by Vistergy>
  - name: VISTERGY_AGENT_PUBLIC_URL
    value: https://<route host>
route:
  enabled: true
  host: <route host>
# Only if the cluster's global pull secret does not cover
# registry.connect.redhat.com:
# imagePullSecrets:
#   - name: <your pull secret>
```

Setting `route.host` lets the Route and `VISTERGY_AGENT_PUBLIC_URL` name the
same host before install. Left empty, OpenShift names the host from the
release's full name, a hyphen and the namespace. That label must stay
within 63 characters.

Install from the OpenShift Helm charts repository:

```bash
helm repo add openshift-helm-charts https://charts.openshift.io/
helm repo update openshift-helm-charts
helm install agent-server openshift-helm-charts/vistergy-agent-server \
  --namespace vistergy --create-namespace -f my-values.yaml
```

From a local copy of the chart, use its directory in place of
`openshift-helm-charts/vistergy-agent-server`.

Wait for readiness. A cold start fetches the corpus, which can take several
minutes; the startup probe allows up to 10 minutes:

```bash
kubectl -n vistergy rollout status deploy/agent-server-vistergy-agent-server
```

Run the built-in test, which calls `/healthz` from inside the cluster:

```bash
helm test agent-server -n vistergy
```

## Values

| Key | Default | Description |
|---|---|---|
| `replicaCount` | `1` | Number of replicas |
| `image.repository` | `registry.connect.redhat.com/vistergy/agent-server` | The Red Hat certified image |
| `image.tag` | `ubi-v0.26` | Image tag; required |
| `image.pullPolicy` | `IfNotPresent` | Pull policy |
| `imagePullSecrets` | `[]` | Pre-existing pull secret names |
| `nameOverride` / `fullnameOverride` | `""` | Override the chart or release resource names |
| `serviceAccount.create` | `true` | Create a dedicated ServiceAccount (no API token is mounted either way) |
| `serviceAccount.name` | `""` | Use an existing ServiceAccount name |
| `service.type` / `service.port` | `ClusterIP` / `8080` | Service settings |
| `route.enabled` | `false` | Create an OpenShift Route |
| `route.host` | `""` | Optional explicit Route host |
| `route.annotations` | router timeout `120s` | Route annotations. The default raises the router's 30s timeout, because answers that call the model can take longer |
| `route.tls.termination` | `edge` | Route TLS termination |
| `route.tls.insecureEdgeTerminationPolicy` | `Redirect` | HTTP handling on an edge-terminated Route |
| `resources` | requests 500m/1Gi, limits 1/2Gi | Container resources |
| `envFromSecrets` | `[]` | Pre-existing Secret names injected as env |
| `env` | `[]` | Plain environment variables, those in Prerequisites among them |
| `command` / `args` | `[]` | Optional startup override. The image's own entrypoint is the default |
| `podSecurityContext` | `{}` | Empty so OpenShift assigns the UID |
| `containerSecurityContext` | restricted-v2 compatible | Non-root, no privilege escalation, all capabilities dropped |
| `probes.startup/readiness/liveness` | `/healthz`, `timeoutSeconds: 5` | Health probes. The timeout is stated rather than left to Kubernetes' 1-second default, which is thin for a pause on a half-core request |
| `nodeSelector` / `tolerations` / `affinity` | `{}` / `[]` / `{}` | Standard scheduling controls |

TLS note: by policy this chart carries no key material in values.
`route.tls` accepts `caCertificate` and `destinationCACertificate` but not
`certificate`/`key`. Serve custom certificates from a secret managed
outside the chart, for example through the router or cert-manager.

## Uninstall

```bash
helm uninstall agent-server -n vistergy
```

The chart owns only the Deployment, Service, optional Route, optional
ServiceAccount, and its test pod. Nothing durable is left behind, except a
test pod that failed, kept for diagnosis. Delete it with:

```bash
kubectl -n vistergy delete pod agent-server-vistergy-agent-server-test-healthz
```

## Upgrade

An upgrade replaces the values a release holds with the values it passes.
So carry the release's own values forward, then set what changes:

```bash
helm repo update openshift-helm-charts
helm get values agent-server -n vistergy -o yaml > release-values.yaml
helm upgrade agent-server openshift-helm-charts/vistergy-agent-server -n vistergy \
  -f release-values.yaml --set image.tag=<new tag> --wait --timeout 15m
rm release-values.yaml
```

A list such as `env` or `envFromSecrets` is replaced whole, so a changed
list names every entry. After the upgrade, run `helm test` again. Keep the
previous image tag until the new one is ready.
