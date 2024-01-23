
### 1. To install the Helm Chart without a HelmChartRepository, run the following command:

```
    helm install -n <your-rhdh-project-or-namespace-here> --generate-name https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.1-59-CI/charts/redhat/redhat/developer-hub/1.1-59-CI/developer-hub-1.1-59-CI.tgz
```

### 2. Or, to install from a Helm Chart Repository:

#### a. Run this to create the above chart repo, with .metadata.name = `rhdh-next-ci-repo`:

```
    oc apply -f https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.1-59-CI/installation/rhdh-next-ci-repo.yaml
```

#### b. Browse to the Helm Chart Repository created above and install via OpenShift UI.

### 3. [OPTIONAL] To verify a chart, use chartverifier. This is only needed if you'd built your own chart and want to check it passes compliance checks.

```
    cd /tmp && mkdir -p chartverifier;     podman run --rm -i -e KUBECONFIG=/.kube/config       -v /home/nboldt/.kube:/.kube:z -v /tmp/chartverifier:/app/chartverifier:z       quay.io/redhat-certification/chart-verifier       verify --write-to-file https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.1-59-CI/charts/redhat/redhat/developer-hub/1.1-59-CI/developer-hub-1.1-59-CI.tgz
    echo 'Report in /tmp/chartverifier/report.yaml'
```    

