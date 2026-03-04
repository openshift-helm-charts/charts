# Prophaze WAF Helm Chart

This Helm chart deploys the Prophaze Web Application Firewall on Kubernetes or OpenShift.

## Installation

helm install waf ./src

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| replicaCount | Number of replicas | 1 |
| image.repository | Container image | nginx |
| image.tag | Container image tag | 1.25 |
| service.port | Service port | 80 |
