{{- define "fortanix-cert-setup.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "fortanix-cert-setup.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "fortanix-cert-setup.image" -}}
{{- $tag := .Values.image.tag | toString -}}
{{- printf "%s/%s:%s" .Values.global.registry .Values.image.name $tag -}}
{{- end -}}
