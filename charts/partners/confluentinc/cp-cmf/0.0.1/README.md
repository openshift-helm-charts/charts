# Confluent Manager for Apache Flink Helm Chart

This chart deploys Confluent Manager for Apache Flink on Kubernetes.

## Prerequisites

* Kubernetes 1.19+
* Helm 3.0+
* Confluent Distribution of Apache Flink Kubernetes Operator 1.13+

## Installing the Chart

```bash
helm repo add confluentinc https://packages.confluent.io/helm
helm repo update
helm upgrade --install cp-flink-kubernetes-operator --version "~1.130.0" \
  confluentinc/flink-kubernetes-operator \
  --set watchNamespaces="{namespace1,namespace2,...}"
```

For more details, refer to https://docs.confluent.io/platform/current/flink/installation/helm.html

## Support

* Home: https://www.confluent.io/
* Support: https://support.confluent.io/
