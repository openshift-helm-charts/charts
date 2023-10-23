#!/usr/bin/env bash

user_name='rh-cert-user'
oc create sa $user_name
token_secret=$(oc get secrets --field-selector=type=kubernetes.io/service-account-token -o=jsonpath="{.items[?(@.metadata.annotations.kubernetes\.io/service-account\.name=='"$user_name"')].metadata.name}")
token=$(oc get secret $token_secret -o json | jq -r .data.token | base64 -d)
oc apply -f cluster_role_binding.yaml

echo "Service Account Token:"
echo $token
