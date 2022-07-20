{{- define "fortanix-secrets-injector.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "fortanix-secrets-injector.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "fortanix-secrets-injector.image" -}}
{{- $tag := .Values.image.tag | toString -}}
{{- printf "%s/%s:%s" .Values.global.registry .Values.image.name $tag -}}
{{- end -}}
