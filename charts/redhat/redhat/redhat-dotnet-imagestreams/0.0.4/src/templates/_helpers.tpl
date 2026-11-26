{{- define "platformTag" -}}
  {{- $platform := . -}}
  {{- $tag := $platform | replace " " "" | lower -}}
  {{- $tag -}}
{{- end -}}