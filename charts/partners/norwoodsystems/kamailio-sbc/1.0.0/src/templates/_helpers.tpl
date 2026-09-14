{{/*
Expand the name of the chart.
*/}}
{{- define "kamailio-sbc.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Truncated at 63 chars because some Kubernetes name fields are limited.
*/}}
{{- define "kamailio-sbc.fullname" -}}
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
{{- define "kamailio-sbc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to ALL resources.
*/}}
{{- define "kamailio-sbc.labels" -}}
helm.sh/chart: {{ include "kamailio-sbc.chart" . }}
{{ include "kamailio-sbc.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: cogvoice
{{- end }}

{{/*
Selector labels - used in spec.selector.matchLabels.
MUST be immutable: never include version here.
*/}}
{{- define "kamailio-sbc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kamailio-sbc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: sbc
{{- end }}

{{/*
ServiceAccount name.
*/}}
{{- define "kamailio-sbc.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kamailio-sbc.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
