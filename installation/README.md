

## Installation

### 1. To install the Helm Chart without a HelmChartRepository, run the following command:

```
    helm install -n <your-rhdh-project> --generate-name https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-28-CI/charts/redhat/redhat/developer-hub/1.2-28-CI/developer-hub-1.2-28-CI.tgz
```

### 2. Or, to install from a Helm Chart Repository:

First, run this to create the above chart repo, with .metadata.name = `rhdh-next-ci-repo`:

```
    oc apply -f https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-28-CI/installation/rhdh-next-ci-repo.yaml
```

Then, browse to the Helm Chart Repository created above and install via OpenShift UI.



## Optional Verification

### To verify a chart, use chart-verifier. This is only needed if you built your own chart and want to check it passes compliance checks.

```
    cd /tmp && mkdir -p chartverifier; \
    podman run --rm -i -e KUBECONFIG=/.kube/config \
      -v /root/.kube:/.kube:z -v /tmp/chartverifier:/app/chartverifier:z \
      quay.io/redhat-certification/chart-verifier \
      verify --write-to-file https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-28-CI/charts/redhat/redhat/developer-hub/1.2-28-CI/developer-hub-1.2-28-CI.tgz
    echo 'Report in /tmp/chartverifier/report.yaml'
```    

