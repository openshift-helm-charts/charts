
# DSM Secrets Injector Helm Chart v3

This repository contains Helm chart for deploying and configuring secrets injection with Fortanix DSM in Kubernetes applications.

It deploys Mutating Webhook Controller and sidecar container for injecting secrets.

Note: This chart supports kubernetes version 1.16 and above.

## Dependency Charts

* **fortanix-cert-setup** - `cert-setup` folder in this repository

## Install Chart

* Install Dependency Chart
````console
$ helm dep up dsm-secrets-injector-chart
````
* Install dsm-secrets-injector Chart
** Kubernetes cluster
````console
$ helm install dsm-secrets-injector-chart ./dsm-secrets-injector-chart
````
** OpenShift Cluster
```console
$ 
$ helm install dsm-secrets-injector-chart ./dsm-secrets-injector --set global.
## Uninstall chart 
* Uninstall dsm-secrets-injector-chart
````console
$ helm delete dsm-secrets-injector-chart
````

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Parameters

The following tables lists the configurable parameters of the sdkms-secrets-injection chart and their default values.

| Parameter                        | Description                                                                               | Default                                                      |
|----------------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| `global.registry`           | Global Docker image registry                                                              | `fortanix`                                                        |
| `global.namespace`        | Global Namespace                                           | `fortanix`      |
| `global.service`                 | Global Kubernetes Service                                                              | `fortanix-secrets-injector-svc`                                                  |
| `global.serviceAccount`               |  Service Account for cert TLS                                                                  | `fortanix-webhook-certs-sa`                                             |
| `global.secret`                      | Secret containing cert TLS                                                                     | `fortanix-secrets-injector-certs`                                                 |
| `global.caBundle`          | Kubernetes API Server CA Certificate pem bytes as base64 string    | nil
| `configmap.name`               | ConfigMap for Controller configuration                                                            | `fortanix-webhook-config`                                                     |
| `configmap.authTokenType`              | Authentication Type for Secrets-Injection                                          | `api-key` (can be set as `jwt` or `api-key`)      |
| `configmap.secretAgent.imageName`                   | Image name for Secret Agent Image                                                                      | `k8s-sdkms-secret-agent`                                                  |
| `configmap.secretAgent.tag`                 | Image tag for Secret Agent  Image                                                                       | `"1.0"`
| `configmap.tokenVolumeProjection.audience` | The audience of the Service Account JWT token. This should be same as SDKMS endpoint. e.g. https://sdkms.fortanix.com. Applies only if `jwt`type of authentication is set | nil
| `configmap.tokenVolumeProjection.expirationSeconds` | The expiration period of the Service Account JWT token (in seconds). Applies only if `jwt`type of authentication is set | `3600`
| `replicas`                   | Number of replicas of the Secrets Injector deployment                                               | `1`                                                  |
| `image.name`                | Secrets Injector Image Name                                                  | `k8s-sdkms-secrets-injector`                                                        |
| `image.tag`                      | Secrets Injector Image Tag                                                        | `"1.0"`                                                        |
| `image.pullPolicy`                | Secrets Injector Image Pull Policy                                                  | `IfNotPresent`                                                        |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`.
