{{- define "lcs.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "lcs.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" (include "lcs.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "lcs.labels" -}}
app.kubernetes.io/name: {{ include "lcs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
env: {{ .Values.global.env }}
{{- end -}}

{{- define "lcs.selectorLabels" -}}
app.kubernetes.io/name: {{ include "lcs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Do not set runAsUser: OpenShift restricted SCC assigns the namespace UID. */}}
{{- define "lcs.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "lcs.containerSecurityContext" -}}
allowPrivilegeEscalation: false
capabilities:
  drop:
    - ALL
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "lcs.image" -}}
{{- $repo := .repo -}}
{{- $tag := .tag -}}
{{- $digest := .digest | default "" -}}
{{- $registry := .root.Values.global.imageRegistry -}}
{{- if and $digest (ne $digest "") -}}
{{- if $registry -}}
{{- printf "%s/%s@%s" $registry $repo $digest -}}
{{- else -}}
{{- printf "%s@%s" $repo $digest -}}
{{- end -}}
{{- else if $registry -}}
{{- printf "%s/%s:%s" $registry $repo $tag -}}
{{- else -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}
{{- end -}}
