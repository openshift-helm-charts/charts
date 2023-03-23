# Carbonio Helm Chart

This repository contains the official Zextras Carbonio Helm chart for
installing and configuring Carbonio on Kubernetes. This chart supports
multiple use cases of Carbonio on Kubernetes depending on the values
provided.

For full documentation on this Helm chart along with all the ways you can use
Carbonio with Kubernetes, please see the
[Carbonio and Kubernetes documentation](https://docs.zextras.com/carbonio/html).

## Prerequisites

To use the charts here, [Helm](https://helm.sh/) must be configured for your
Kubernetes cluster. Setting up Kubernetes and Helm is outside the scope of
this README. Please refer to the Kubernetes and Helm documentation.

The versions required are:

- **Helm 3.0+** - This is the earliest version of Helm tested. It is possible it
  works with earlier versions but this chart is untested for those versions.

- **Kubernetes 1.14+** - This is the earliest version of Kubernetes tested. It
  is possible that this chart works with earlier versions but it is untested.

## Usage

To install the latest version of this chart, add the Zextras helm repository and
run `helm install`:

```console
$ helm repo add Zextras https://helm.releases.zextras.com
"Zextras" has been added to your repositories

$ helm install carbonio zextras/carbonio
```

Please see the many options supported in the `values.yaml` file. These are also
fully documented directly on the [Carbonio
website](https://docs.zextras.com/carbonio/html) along with more detailed
installation instructions.

## NOTES for OpenShiftdeployment

```sh
oc create sa --namespace carbonio-system sa-with-anyuid
oc adm policy add-scc-to-user anyuid -z sa-with-anyuid --namespace carbonio-system
```
