
## Scripted installation

To [install](./install.sh) from a Helm Chart Repository, run the following commands:

```
cd /tmp
# Create or select a namespace
# Install the chart repo
# Install the chart, then update the clusterRouterBase
curl -sSLO https://raw.githubusercontent.com/rhdh-bot/openshift-helm-charts/redhat-developer-hub-1.4-59-CI/installation/install.sh && chmod +x install.sh
./install.sh 1.4-59-CI --namespace rhdh-1-4-59-ci --chartrepo
```

That's it! 


## Manual installation

The [install](./install.sh) script creates a chart repo, then follows the [standard installation guide](https://access.redhat.com/documentation/en-us/red_hat_developer_hub/1.1/html-single/administration_guide_for_red_hat_developer_hub/index#proc-install-rhdh-helm_admin-rhdh) and automates these steps:

1. Create a chart repo, with .metadata.name = `rhdh-next-ci-repo`
```
oc apply -f https://github.com/rhdh-bot/openshift-helm-charts/raw/redhat-developer-hub-1.4-59-CI/installation/rhdh-next-ci-repo.yaml
```
2. Go to `Developer` perspective in your cluster
1. Select your namespace or project (eg., `rhdh-helm` or `rhdh-1-4-59-ci`)
1. Click `+Add`, scroll down and select `Helm Chart`
1. Filter out the default charts and just select the `Rhdh Next Ci Repo`
1. **IMPORTANT**: In the chart's YAML view, change the following line to the correct value for your cluster. For example, change
```
clusterRouterBase: apps.example.com
```
to
```
clusterRouterBase: apps.ci-my-cluster-goes-here.com
```
7. Click `Create` and watch the deployment happen from the `Topology` view.
1. Open the `Route` once it's available to see your deployed RHDH instance.

## Optional Verification

To verify a chart, use chart-verifier. This is only needed if you built your own chart and want to check it passes compliance checks.

```
cd /tmp && mkdir -p chartverifier; \\
podman run --rm -i -e KUBECONFIG=/.kube/config \\
  -v /home/nboldt/.kube:/.kube:z -v /tmp/chartverifier:/app/chartverifier:z \\
  quay.io/redhat-certification/chart-verifier \\
  verify --write-to-file https://github.com/rhdh-bot/openshift-helm-charts/raw/redhat-developer-hub-1.4-59-CI/charts/redhat/redhat/redhat-developer-hub/1.4-59-CI/redhat-developer-hub-1.4-59-CI.tgz
echo 'Report in /tmp/chartverifier/report.yaml'
```  