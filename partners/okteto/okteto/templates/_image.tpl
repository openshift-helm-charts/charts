
{{- /*
This function constructs the full image reference from the given parameters.
Parameters:
  - image: the image value (string or map)
  - globalRegistry: the global values (for accessing globals.registry)
*/ -}}
{{- define "okteto.fullImage" -}}
  {{- $image := index . 0 -}}
  {{- $globalRegistry := index . 1 | default "" -}}
  
  {{- /* Type checking and parsing logic */ -}}
  {{- if and (kindIs "string" $image) (ne $image "") -}}
    {{ printf $image }}
  {{- else if kindIs "map" $image -}}
    {{- $imageRegistry := $image.registry | default $globalRegistry | default "" -}}
    {{- $imageRepository := $image.repository | default "" -}}
    {{- $imageTag := printf "%v" ($image.tag | default "latest") -}}
  
    {{- $fullImage := "" -}}
    {{- if ne $imageRegistry "" -}}
      {{- $fullImage = printf "%s/%s:%s" $imageRegistry $imageRepository $imageTag -}}
    {{- else -}}
      {{- $fullImage = printf "%s:%s" $imageRepository $imageTag -}}
    {{- end -}}
    {{- $fullImage -}}
  {{- else -}}
    {{- fail "Invalid type for image value. Must be string or map." -}}
  {{- end -}}
{{- end -}}


{{- define "okteto.image.backend" -}}
  {{- include "okteto.fullImage" (list .Values.backend.image .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.daemonset" -}}
  {{- include "okteto.fullImage" (list .Values.daemonset.image .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.installerrunner" -}}
  {{- include "okteto.fullImage" (list .Values.installer.runner .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.autoscaler" -}}
  {{- include "okteto.fullImage" (list .Values.autoscaler.image .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.defaultBackend" -}}
  {{- include "okteto.fullImage" (list .Values.defaultBackend.image .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.frontend" -}}
  {{- include "okteto.fullImage" (list .Values.frontend.image .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.cindy" -}}
  {{- include "okteto.fullImage" (list .Values.unsupported.cindy.image .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.sandbox" -}}
  {{- include "okteto.fullImage" (list .Values.unsupported.cindy.sandbox.image .Values.globals.registry) -}}
{{- end -}}

{{- define "okteto.image.registry" -}}
  {{- include "okteto.fullImage" (list .Values.registry.image .Values.globals.registry) -}}
{{- end -}}

{{/*
    Returns buildkit image and tag based on .Values.buildkit.rootless.enabled
*/}}
{{- define "okteto.image.buildkit" -}}
    {{- if .Values.buildkit.rootless.enabled -}}
        {{- include "okteto.fullImage" (list .Values.buildkit.rootless.image .Values.globals.registry) -}}
    {{- else -}}
        {{- include "okteto.fullImage" (list .Values.buildkit.image .Values.globals.registry) -}}
    {{- end -}}
{{- end -}}