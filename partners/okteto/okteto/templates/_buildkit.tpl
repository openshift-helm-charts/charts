
{{/*
    Returns the buildkit cache size in megabytes as in int.
    It is calculated as 90% of the configured persistence size.
*/}}
{{- define "okteto.buildkit.persistence.cache" -}}
    {{- $storageSizeBytes := include "okteto.quantityToBytes" .Values.buildkit.persistence.size -}}
    {{- $storageSizeMB := divf $storageSizeBytes (mulf 1024 1024)  -}}
    {{- print (mulf $storageSizeMB .Values.buildkit.persistence.cacheRatio | floor)  -}}
{{- end -}}

{{/*
    Returns buildkit.ingress.enabled
    Fails if buildkit.ingress.enabled is true and buildkit.service.type is LoadBalancer
*/}}
{{- define "okteto.buildkit.ingress.enabled" -}}
    {{- $ingressEnabled := .Values.buildkit.ingress.enabled -}}
    {{- if and .Values.buildkit.ingress.enabled (eq .Values.buildkit.service.type "LoadBalancer") -}}
        {{- fail "The configuration '.Values.buildkit.ingress.enabled' cannot be set to 'true' if '.Values.buildkit.service.type' is configured as 'LoadBalancer'." -}}
    {{- end -}}
    {{- if and .Values.buildkit.ingress.enabled (ne (int .Values.buildkit.service.port) 443) -}}
        {{- fail "The configuration '.Values.buildkit.ingress.enabled' cannot be set to 'true' if '.Values.buildkit.service.port' is not configured as 443." -}}
    {{- end -}}
    {{- print $ingressEnabled -}}
{{- end -}}

{{/*
    Returns buildkit metrics service/endpoint name used by buildkit metrics exporter (okteto insights)
*/}}
{{- define "okteto.buildkit.metrics.endpointName" -}}
    {{- printf "%s-buildkit-metrics" (include "okteto.fullname" .) -}}
{{- end -}}

{{- define "okteto.buildkit.network.mode" -}}
    {{- $rootless := .Values.buildkit.rootless.enabled | default false -}}
    {{- $networkMode := .Values.buildkit.network.mode | default "" -}}
    {{- if and $rootless (eq $networkMode "bridge") -}}
        {{ fail "Network 'bridge' mode is incompatible with rootless mode" }}
    {{- else -}}
        {{ $networkMode }}
    {{- end -}}
{{- end -}}
