

## Installation

### 1. To install from a Helm Chart Repository:

First, run this to create the above chart repo, with .metadata.name = `rhdh-next-ci-repo`:

```
    oc apply -f https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-33-CI/installation/rhdh-next-ci-repo.yaml
```

Then, following the [standard installation guide](https://access.redhat.com/documentation/en-us/red_hat_developer_hub/1.1/html-single/administration_guide_for_red_hat_developer_hub/index#proc-install-rhdh-helm_admin-rhdh):

* Go to `Developer` perspective in your cluster
* Select your namespace or project
* Click `+Add`, scroll down and select `Helm Chart`
* Filter out the default charts and just select the `Rhdh Next Ci Repo`

* **IMPORTANT**: In the chart's YAML view, change the following line to the correct value for your cluster. For example, change
```
  clusterRouterBase: apps.example.com
```
to
```
  clusterRouterBase: apps.ci-my-cluster-goes-here.com
```
* Click `Create` and watch the deployment happen from the `Topology` view.
* open the `Route` once it's available to see your deployed RHDH instance.

## Optional Verification

### To verify a chart, use chart-verifier. This is only needed if you built your own chart and want to check it passes compliance checks.

```
    cd /tmp && mkdir -p chartverifier; \
    podman run --rm -i -e KUBECONFIG=/.kube/config \
      -v /home/nboldt/.kube:/.kube:z -v /tmp/chartverifier:/app/chartverifier:z \
      quay.io/redhat-certification/chart-verifier \
      verify --write-to-file https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-33-CI/charts/redhat/redhat/developer-hub/1.2-33-CI/developer-hub-1.2-33-CI.tgz
    echo 'Report in /tmp/chartverifier/report.yaml'
```    

