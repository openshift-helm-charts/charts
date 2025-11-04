{{/*
Expand the name of the chart.
*/}}
{{- define "wave-autoscale.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "wave-autoscale.fullname" -}}
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
{{- define "wave-autoscale.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "wave-autoscale.labels" -}}
helm.sh/chart: {{ include "wave-autoscale.chart" . }}
{{ include "wave-autoscale.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "wave-autoscale.selectorLabels" -}}
app.kubernetes.io/name: {{ include "wave-autoscale.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "wave-autoscale.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "wave-autoscale.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the agent service account to use
*/}}
{{- define "wave-autoscale.agentServiceAccountName" -}}
{{- if .Values.serviceAccountAgent.create }}
{{- default (printf "%s-agent" (include "wave-autoscale.fullname" .)) .Values.serviceAccountAgent.name }}
{{- else }}
{{- default "default" .Values.serviceAccountAgent.name }}
{{- end }}
{{- end }}

{{/*
Return the proper namespace
*/}}
{{- define "wave-autoscale.namespace" -}}
{{- if eq .Release.Namespace "default" }}
{{- .Values.default_namespace }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}

{{/*
Return the proper image name for core
*/}}
{{- define "wave-autoscale.core.image" -}}
{{- printf "%s:%s" .Values.spec.core.image.repository .Values.spec.core.image.tag }}
{{- end }}

{{/*
Return the proper image name for web console
*/}}
{{- define "wave-autoscale.webConsole.image" -}}
{{- printf "%s:%s" .Values.spec.webConsole.image.repository .Values.spec.webConsole.image.tag }}
{{- end }}

{{/*
Return the proper image name for intelligence
*/}}
{{- define "wave-autoscale.intelligence.image" -}}
{{- printf "%s:%s" .Values.spec.intelligence.image.repository .Values.spec.intelligence.image.tag }}
{{- end }}

{{/*
Return the proper image name for agent
*/}}
{{- define "wave-autoscale.agent.image" -}}
{{- printf "%s:%s" .Values.spec.agent.image.repository .Values.spec.agent.image.tag }}
{{- end }}

{{/*
Return the proper image name for cadvisor
*/}}
{{- define "wave-autoscale.cadvisor.image" -}}
{{- printf "%s:%s" .Values.spec.cadvisor.image.repository .Values.spec.cadvisor.image.tag }}
{{- end }}
