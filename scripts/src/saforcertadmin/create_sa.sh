#!/usr/bin/env bash

user_name='rh-cert-user'
token_secret='rh-cert-user-token'
oc create sa $user_name
oc apply -f token_secret.yaml
token=$(oc get secret $token_secret -o json | jq -r .data.token | base64 -d)
oc apply -f cluster_role_binding.yaml

echo "Service Account Token:"
echo $token
