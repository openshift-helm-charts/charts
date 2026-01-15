# Troubleshooting

## Pods stuck in Pending

- Ensure the RWX model PVC exists (`nfs-model-storage-pvc` by default).
- If you want to disable the fail-fast check, set `validation.failOnMissingModelPVC: false`.

## ImagePullBackOff

- Create GHCR image pull secrets in the **tokenvisor** and **skypilot** namespaces.
- Confirm `global.imagePullSecrets` and `skypilot.imagePullSecrets` names.

## CRDs missing

- If you see errors about missing kinds, install the operators/CRDs.
- Confirm with `kubectl api-resources` for each CRD group.

## Gateway not routing

- Check Gateway and HTTPRoute status: `kubectl get gateway,httproute -n tokenvisor`.
- Ensure Cilium is installed and Gateway API CRDs are present.

## EMU cannot connect to DB/ClickHouse

- Verify `emu-secret` contains `EMU_DB_PATH` and `EMU_SERVICE_KEY`.
- Verify `clickhouse-secret` and `pg-emu-user-secret` are correct.
