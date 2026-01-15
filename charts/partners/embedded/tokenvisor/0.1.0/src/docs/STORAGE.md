# Storage

TokenVisor requires persistent storage. This chart uses a **bring your own storage class** approach - you must have a StorageClass configured in your cluster that matches your values.

## Bringing Your Own Storage Class

The chart defaults to `openebs-hostpath` but you should update this to match your cluster's storage provisioner.

Configure your storage class in values.yaml:

```yaml
clickhouse:
  storageClassName: <your-storage-class>
  storageSize: 10Gi

cnpg:
  storageClassName: <your-storage-class>
  storageSize: 10Gi

victoriametrics:
  storageClassName: <your-storage-class>
  storageSize: 10Gi

victoria-logs-single:
  server:
    persistentVolume:
      storageClassName: <your-storage-class>
      size: 10Gi

storage:
  modelPvc:
    storageClassName: <your-rwx-storage-class>
    size: 20Gi
```

### Storage Class Requirements

Select a storage class that provides:
- **ReadWriteOnce** for databases (ClickHouse, PostgreSQL, VictoriaMetrics, VictoriaLogs)
- **ReadWriteMany** for model storage (EMU/Starling shared `/hf_repo`)

### Example Storage Providers

Choose a storage provider that fits your environment:

- **OpenEBS**: The default in values.yaml - lightweight containerized storage
- **OpenShift Container Storage (OCS/ODF)**: Recommended for OpenShift clusters
- **Longhorn**: Lightweight distributed storage for Kubernetes
- **NFS client provisioner**: For existing NFS servers
- **Cloud provider storage**: AWS EBS, Azure Disk, GCE Persistent Disk

## Model Storage (RWX)

EMU and Starling require a shared ReadWriteMany volume mounted at `/hf_repo`. The PVC name is **hardcoded** in the backend as:

```
nfs-model-storage-pvc
```

Do not change this unless you also update the backend code.

### Dynamic Provisioning

If your storage class supports dynamic RWX provisioning:

```yaml
storage:
  modelPvc:
    create: true
    name: nfs-model-storage-pvc
    storageClassName: <your-rwx-storage-class>
    accessModes:
      - ReadWriteMany
    size: 20Gi
```

### Manual Provisioning

For manual PV/PVC creation (e.g., with SeaweedFS or NFS), see `docs/SEAWEEDFS.md`.

When using manually provisioned storage:

```yaml
storage:
  modelPvc:
    create: false

emu:
  modelStorage:
    existingClaim: nfs-model-storage-pvc
```

### Fail-fast Validation

By default the chart fails if the model PVC is missing. Disable if needed:

```yaml
validation:
  failOnMissingModelPVC: false
```

## Shared Storage Across Namespaces

If you need the same RWX storage in multiple namespaces (e.g., `tokenvisor` and `skypilot`), create a PVC in **each** namespace that binds to the same PV or shared backend path.

Example with SeaweedFS:
- Create one PV that points to your SeaweedFS collection
- Create a PVC in `tokenvisor` namespace that binds to this PV
- If needed, create another PVC in `skypilot` namespace that binds to the same PV

Both namespaces will then have access to the same shared models.
