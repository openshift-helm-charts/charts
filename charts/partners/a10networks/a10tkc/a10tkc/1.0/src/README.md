A10 Thunder Kubernetes Connector Helm Chart

    ⚠️ Please note: We take security and our users' trust very seriously. If you believe you have found a security issue in A10 Thunder Kubernetes Connecotr, please responsibly disclose by contacting us at support@a10networks.com.

This repository contains the official A10 Thunder Kuberneres Connector(TKC) Helm chart for installing Thunder Kubernetes Connector (TKC) on Kubernetes. This chart supports multiple use cases of Configuring the ACOS device configuration depending on the values /CRD provided.

For full documentation on this Helm chart with Kubernetes, please see the A10 Thunder Kubernetes Connector Documentation.
Prerequisites

To use the charts here, Helm must be configured for your Kubernetes cluster. Setting up Kubernetes and Helm is outside the scope of this README. Please refer to the Kubernetes and Helm documentation.

The versions required are:

    Helm 3.x
    Kubernetes 1.19+ - This is the earliest version of Kubernetes tested. It is possible that this chart works with earlier versions but it is untested.

Usage

To install the latest version of this chart, add the A10 Thunder Kubernetes Connector helm repository and run helm install:

$ helm repo add "TBD"
"a10tkc" has been added to your repositories

$ helm install a10tkc a10networks/a10tkc

Please see the many options supported in the values.yaml file. These are also fully documented directly on the A10 Thunder Kubernetes Connector Documentation page along with more detailed  instructions.