

## Pull secret setup

To install CI builds published to https://quay.io/organization/rhdh, you need a pull secret.

Copy your secret to a file and set `metadata.name` == `rhdh-pull-secret` (not the default exported from quay.io!!)

```
cat <<EOF > /tmp/my_quay_secret
apiVersion: v1
kind: Secret
metadata:
  name: rhdh-pull-secret
data:
  .dockerconfigjson: ==your-quay-login-secret-goes-here===
type: kubernetes.io/dockerconfigjson
EOF
```

Now add the secret to your RHDH/Backstage namespace or project:

```
oc new-project <your-rhdh-project>
oc create -f /tmp/my_quay_secret -n <your-rhdh-project>
```



## Installation

### 1. To install the Helm Chart without a HelmChartRepository, run the following command:

```
    helm install -n <your-rhdh-project> --generate-name https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-9-CI/charts/redhat/redhat/developer-hub/1.2-9-CI/developer-hub-1.2-9-CI.tgz
```

### 2. Or, to install from a Helm Chart Repository:

First, run this to create the above chart repo, with .metadata.name = `rhdh-next-ci-repo`:

```
    oc apply -f https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-9-CI/installation/rhdh-next-ci-repo.yaml
```

Then, browse to the Helm Chart Repository created above and install via OpenShift UI.



## Optional Verification

### To verify a chart, use chart-verifier. This is only needed if you built your own chart and want to check it passes compliance checks.

```
    cd /tmp && mkdir -p chartverifier; \
    podman run --rm -i -e KUBECONFIG=/.kube/config \
      -v /root/.kube:/.kube:z -v /tmp/chartverifier:/app/chartverifier:z \
      quay.io/redhat-certification/chart-verifier \
      verify --write-to-file https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-1.2-9-CI/charts/redhat/redhat/developer-hub/1.2-9-CI/developer-hub-1.2-9-CI.tgz
    echo 'Report in /tmp/chartverifier/report.yaml'
```    

