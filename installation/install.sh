#!/bin/bash  -e
#
# Copyright (c) 2024 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#
# install a helm chart with the correct global.clusterRouterBase

# default namespace if none set
namespace="rhdh-helm"

usage ()
{
  echo "Usage: $0 CHART_VERSION [-n namespace]

Examples:
  $0 1.1.0 
  $0 1.0-201-CI -n rhdh-ci

Options:
  -n  Project or namespace into which to install specified chart; default: $namespace
"
  exit
}

if [[ $# -lt 1 ]]; then usage; fi

while [[ "$#" -gt 0 ]]; do
  case $1 in
    '-n') namespace="$2"; shift 1;;
    '-h') usage;;
    *) CV="$1";;
  esac
  shift 1
done

if [[ ! $CV ]]; then usage; fi

tmpfile=/tmp/developer-hub.chart.values.yml
CHART_URL="https://github.com/rhdh-bot/openshift-helm-charts/raw/developer-hub-${CV}/charts/redhat/redhat/developer-hub/${CV}/developer-hub-${CV}.tgz"

# 0. choose namespace for the install (or create if non-existant)
oc new-project "$namespace" || oc project "$namespace"

# 1. install (or upgrade)
helm upgrade developer-hub -i "${CHART_URL}"

# 2. collect values
PASSWORD=$(kubectl get secret developer-hub-postgresql -o jsonpath="{.data.password}" | base64 -d)
CLUSTER_ROUTER_BASE=$(oc get route console -n openshift-console -o=jsonpath='{.spec.host}' | sed 's/^[^.]*\.//')

# 3. change values
helm upgrade developer-hub -i "${CHART_URL}" \
    --set global.clusterRouterBase="${CLUSTER_ROUTER_BASE}" \
    --set global.postgresql.auth.password="$PASSWORD"

# 4. cleanup
rm -f "$tmpfile"
