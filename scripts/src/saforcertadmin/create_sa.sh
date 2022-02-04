#!/usr/bin/env bash

user_name='rh-cert-user'
oc create sa $user_name
token_secret=$(oc get sa $user_name -o json | jq -r '.secrets[].name | select( index("token") )')
token=$(oc get secret $token_secret -o json | jq -r .data.token | base64 -d)
oc apply -f cluster_role_binding.yaml

echo "Service Account Token:"
echo $token
