# lcs

Helm chart for the Zainar 5G LCS stack, version **26.6.0**. Source of truth:
`controller/docker/deployment-release/docker-compose.yml`.

Chart name `lcs` matches the OpenShift partner catalog path
`charts/partners/zainar/lcs`. Catalog display name is **Zainar LCS**.

Requires Kubernetes `>=1.27.0-0`.

## Components

| values key | K8s Service | Ports | Compose name |
|---|---|---|---|
| `controller` | `controller` | 4000–4004 | `controller` |
| `lmfPe` | `lmf-pe` | 8080, 8081, 8888, 9878 | `lmf_pe` |
| `amfProxy` | `amf-proxy` | 8082 | `amf-proxy` |
| `zpsLight` | `zps-light` | 9094, 9095 | `zps-light` |
| `db` | `db` | 5432 | `db` |
| `lcsTestFramework` | `lcs-test-framework` | 9000, 9001 | `lcs_test_framework` |

Certified product images (Red Hat catalog / Pyxis):

| values key | Image | Tag |
|---|---|---|
| `controller` | `registry.gitlab.com/zainar-suite/5g/controller` | `v0.11.0` |
| `lmfPe` | `registry.gitlab.com/zainar-suite/5g/production-lmf-and-pe` | `v0.3.1` |

Defaults pin the certified digests. `amfProxy`, `zpsLight`, and
`lcsTestFramework` default to **off** (local-test images; they are not Red Hat
certified). Enable them with
[`examples/values-local-test.yaml`](../../examples/values-local-test.yaml):

```bash
helm upgrade --install zainar-lcs ./charts/lcs -n zainar \
  -f examples/values-local-test.yaml -f values-secrets.yaml
```

Disable any other component with `<key>.enabled: false`.

Third-party images default to `registry.redhat.io` so chart-verifier
`images-are-certified` skips them: UBI 9 for init waiters / `helm test`,
and `rhel9/postgresql-16` for `db`. The RH Postgres image reserves the
`postgres` role; `db.role` (default `controller`) is the app user it
creates. Controller still connects as `secretEnv.DB_USER` (`postgres`)
because `POSTGRESQL_ADMIN_PASSWORD` is set from `DB_PASSWORD`. Data is
stored at `/var/lib/pgsql/data` (not the Docker Hub path).

`db.persistence.enabled` defaults to `false` (`emptyDir`) so a bare
OpenShift `helm install --wait` does not stall on a PVC. Set it `true`
in production to create a PVC via `volumeClaimTemplates`:

```bash
helm upgrade --install zainar-lcs ./charts/lcs -n zainar \
  --set db.persistence.enabled=true
```

## Secrets

When `externalSecret.enabled` is `false` (default), `secretEnv` is rendered as
Secret `zainar-lcs-app` and mounted into the controller.

`global.imagePullSecrets` defaults to empty. Add `gitlab-registry` (create it
out of band, or set `registrySecret.enabled: true`) only when pulling private
overrides.

## Inter-service DNS

Kubernetes DNS uses hyphens (`lmf-pe`), not compose underscores (`lmf_pe`).
Values already use the Kubernetes names.

## Tests

`helm test` runs `templates/tests/test-connection.yaml`, which curls
`http://controller:4002/healthz` when `controller.enabled` is true.

## Troubleshooting

- `global.waitForLoki` defaults to **false**. Set it `true` only when Service
  `loki:3100` is already in the namespace (observability chart).
- Controller init still waits for `db` when `db.enabled` is true.
- Stuck in Init: `kubectl -n <ns> logs deploy/controller -c wait-for-dependencies`
  (not the default container).
- Keep `LOCATION_PROVIDER=namf` or `lmf-pe` crashes on direct nlmf callbacks.

Full catalog: [docs/troubleshooting.md](../../docs/troubleshooting.md).
