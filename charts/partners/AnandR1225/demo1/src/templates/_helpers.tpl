{{- define "anrs-dashboard.name" -}}
{{- .Chart.Name -}}
{{- end }}

{{- define "anrs-dashboard.fullname" -}}
{{- .Release.Name }}-{{ .Chart.Name }}
{{- end }}

{{- define "anrs-dashboard.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
