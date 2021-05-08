# Chart Verifier Cluster Setup

We should create a service account token to set up a new cluster to run the
chart-verifier for the chart-testing checks.  Later this token can be saved as a
GitHub secret with the name OPENSHIFT_TOKEN.  The API server address also should
be stored in another GitHub secret with the name OPENSHIFT_SERVER.

To get token, first log in to cluster with your user token:

```
oc login --token=<user-token> --server=<api-server-address>
```

To retrieve the token:

```
oc apply -f scripts/chart-verifier-cluster-setup.yaml
SECRET_NAME=`oc get sa chart-verifier-admin -n chart-verifier-infra -o yaml | yq e '.secrets[1].name' -`
oc get secret $SECRET_NAME -n chart-verifier-infra -o yaml | yq e '.data.token' -
```

To revoke an existing token, remove the secret:

```
oc delete secret $SECRET_NAME -n  chart-verifier-infra
```

After removing the existing secret, the controller recreates it automatically.
The new token can be retrieved using this command:

```
oc get secret $SECRET_NAME -n chart-verifier-infra -o yaml | yq e '.data.token' -
```
