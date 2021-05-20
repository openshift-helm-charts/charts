## Generating New Token for Cluster Access

Access to an OpenShift cluster is necessary to run
[chart-testing][chart-testing] as part of the [chart-verifier][chart-verifier]
tool.  This document explains how to generate a service account and
corresponding token.

Login using your OpenShift token (change the API server URL for different
cluster):

```
oc login --token=<token-string> --server=https://api.ocpappsvc-osd.zn6c.p1.openshiftapps.com:6443
```

Delete existing service account, roles, and role bindings:

```
oc delete -k scripts/config/overlays/prod/
```

Create new service account, roles, and role bindings:

```
oc apply -k scripts/config/overlays/prod/
```

There are two secrets associated with the service account.  Use the secret with
the `token` word in it.  To see the secrets run this command:

```
oc get sa chart-verifier-admin -n prod-chart-verifier-infra -o yaml
```

The output of the above command should end something like this:
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

(Note: the [yq][yq] is a command-line YAML processor)

You can store the returned value in the GitHub secrets with key as
`CLUSTER_TOKEN`.

[chart-testing]: https://github.com/helm/chart-testing
[chart-verifier]: https://github.com/redhat-certification/chart-verifier
[yq]: https://mikefarah.gitbook.io/yq/
