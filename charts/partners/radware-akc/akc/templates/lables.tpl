{{/*
Include global labels
*/}}
{{- define "akc.labels" }}
{{- range $k, $v := .Values.global.labels }}
{{ $k }} : {{ $v}}
{{- end }}
{{- end }}