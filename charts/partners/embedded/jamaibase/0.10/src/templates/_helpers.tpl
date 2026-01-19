{{/*
 =============================================================================
 Helm Template Helpers for Jamaibase
 =============================================================================
 This file contains reusable template helpers for the Jamaibase chart.
 These helpers follow Helm and Kubernetes best practices.
=============================================================================*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "jamaibase.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "jamaibase.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "jamaibase.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create universal labels
*/}}
{{- define "jamaibase.labels" -}}
helm.sh/chart: {{ include "jamaibase.chart" . }}
{{ include "jamaibase.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.global.labels }}
{{- toYaml . | nindent 0 }}
{{- end }}
{{- end }}

{{/*
Create selector labels
*/}}
{{- define "jamaibase.selectorLabels" -}}
app.kubernetes.io/name: {{ include "jamaibase.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create universal annotations
*/}}
{{- define "jamaibase.annotations" -}}
{{- with .Values.global.annotations }}
{{- toYaml . | nindent 0 }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "jamaibase.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "jamaibase.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Determine if pod monitoring is enabled
*/}}
{{- define "jamaibase.monitoring.enabled" -}}
{{- if .Values.monitoring.enabled }}
{{- true }}
{{- else }}
{{- false }}
{{- end }}
{{- end }}

{{/*
Create common metadata for resources
*/}}
{{- define "jamaibase.commonMetadata" -}}
labels:
  {{- include "jamaibase.labels" . | nindent 2 }}
  {{- with .Values.global.labels }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
annotations:
  {{- include "jamaibase.annotations" . | nindent 2 }}
  {{- with .Values.global.annotations }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
{{- end }}

{{/*
Create image pull secret reference
*/}}
{{- define "jamaibase.imagePullSecrets" -}}
{{- if .Values.global.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml .Values.global.imagePullSecrets | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Determine the storage class to use
*/}}
{{- define "jamaibase.storageClass" -}}
{{- if .Values.global.storageClass }}
{{- .Values.global.storageClass }}
{{- else }}
""  # Use default storage class
{{- end }}
{{- end }}

{{/*
Determine the namespace to use
*/}}
{{- define "jamaibase.namespace" -}}
{{- if .Values.global.namespace }}
{{- .Values.global.namespace }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}

{{/*
Create DNS names for services
*/}}
{{- define "jamaibase.serviceFQDN" -}}
{{- if .Values.service.create }}
{{- $name := .Values.service.name | default (include "jamaibase.fullname" .) }}
{{- $namespace := include "jamaibase.namespace" . }}
{{- printf "%s.%s.svc.cluster.local" $name $namespace }}
{{- end }}
{{- end }}
