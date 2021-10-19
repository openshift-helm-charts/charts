## Generating New Token for Cluster

To generate a new token follow these instructions.

Login using your OpenShift token:

```
oc login --token=<token-string> --server=<api-server-url>
```

Delete existing service account, roles, and role bindings:

```
oc delete -k scripts/config/overlays/prod/
```

Create new service account, roles, and role bindings:

```
oc apply -k scripts/config/overlays/prod/
```

There are two secrets associated with the service account, use the note down the
secret with `token` word in it.  To see the secrets run this command:

```
oc get sa chart-verifier-admin -n prod-chart-verifier-infra -o yaml
```

The out should end something like this:
```
...
secrets:
- name: chart-verifier-admin-token-t9sjg
- name: chart-verifier-admin-dockercfg-zkhzm
```

Now you can extract the token with this command:

```
oc get secret chart-verifier-admin-token-t9sjg -n prod-chart-verifier-infra -o yaml | yq e '.data.token' - | base64 -d -
```

You can store the returned value in the GitHub secrets with key as
`CLUSTER_TOKEN`.

Alternatively, run `scripts/get-secrets --server <token-string> --server <api-server-url>` to get `CLUSTER_TOKEN` and `API_SERVER`.
