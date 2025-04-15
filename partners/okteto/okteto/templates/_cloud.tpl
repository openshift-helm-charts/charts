{{/*
    Returns if cloud.provider is enabled (aws, gcp, digitalocean or azure)
*/}}
{{- define "okteto.cloud.provider.isEnabled" -}}
    {{- $enabled := false -}}
    {{- if .Values.cloud.provider.aws.enabled -}}
        {{- $enabled = true -}}
    {{- else if .Values.cloud.provider.gcp.enabled -}}
        {{- $enabled = true -}}
    {{- else if .Values.cloud.provider.azure.enabled -}}
        {{- $enabled = true -}}
    {{- else if .Values.cloud.provider.digitalocean.enabled -}}
        {{- $enabled = true -}}
    {{- end -}}
    {{- print $enabled -}}
{{- end -}}