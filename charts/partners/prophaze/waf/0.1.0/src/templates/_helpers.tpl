{{- define "waf.name" -}}
waf
{{- end }}

{{- define "waf.fullname" -}}
{{ .Release.Name }}-waf
{{- end }}
