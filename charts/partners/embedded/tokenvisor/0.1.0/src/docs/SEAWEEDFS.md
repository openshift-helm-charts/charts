# SeaweedFS Setup (RWX)

This guide installs SeaweedFS + CSI driver and prepares RWX storage for TokenVisor. Adjust paths and storage classes to match your environment.

## 1) Install SeaweedFS (Helm)

Create a values file (example below) and install the chart.

```bash
cat <<'YAML' > seaweedfs-values.yaml
global:
  monitoring:
    enabled: true
  enableReplication: false
  replicationPlacement: "001"

master:
  enabled: true
  replicas: 1
  data:
    type: "persistentVolumeClaim"
    size: "5Gi"
    storageClass: "local-path"
  logs:
    type: "persistentVolumeClaim"
    size: "5Gi"
    storageClass: "local-path"

volume:
  enabled: true
  replicas: 1
  dataDirs:
    - name: data1
      type: "hostPath"
      hostPathPrefix: "/data/seaweedfs_vol1"  # <-- change this path
      maxVolumes: 0

filer:
  enabled: true
  replicas: 1
  data:
    type: "persistentVolumeClaim"
    size: "25Gi"
    storageClass: "local-path"
  logs:
    type: "persistentVolumeClaim"
    size: "25Gi"
    storageClass: "local-path"
  s3:
    enabled: false
YAML

helm repo add seaweedfs https://seaweedfs.github.io/seaweedfs/helm
helm repo update
kubectl create ns seaweedfs
helm install -n seaweedfs seaweedfs seaweedfs/seaweedfs \
  -f seaweedfs-values.yaml --version 4.0.402
```

Notes:

- `hostPathPrefix` must exist on the node(s) where volume pods run.
- Replace `local-path` with your storage class if needed.

## 2) Install SeaweedFS CSI Driver

```bash
helm repo add seaweedfs-csi-driver https://seaweedfs.github.io/seaweedfs-csi-driver/helm
helm repo update
helm install -n seaweedfs seaweedfs-csi-driver seaweedfs-csi-driver/seaweedfs-csi-driver \
  --set seaweedfsFiler=seaweedfs-filer.seaweedfs.svc:8888 \
  --set mountService.enabled=true \
  --version 0.2.3
```

## 3) Create PV/PVC for TokenVisor

Use the example in `docs/STORAGE.md` (SeaweedFS PV/PVC template), and make sure:

- PVC name is `nfs-model-storage-pvc` (hardcoded in EMU backend)
- PVC exists in **tokenvisor** namespace
- If you also need RWX in **skypilot**, create another PVC in that namespace

## 4) Configure the chart

```yaml
emu:
  modelStorage:
    existingClaim: nfs-model-storage-pvc
storage:
  modelPvc:
    create: false
```
