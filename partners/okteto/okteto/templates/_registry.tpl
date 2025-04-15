{{/*
    Returns true when registry.storage.filesystem is enabled.
    The value is overriden when cloud.provider is enabled (deprecated)
*/}}
{{- define "okteto.registry.storage.filesystem.enabled" -}}
    {{- $enabled := .Values.registry.storage.filesystem.enabled -}}
    {{- $providerObj := include "okteto.registry.storage.provider" . | trim | nindent 2 | fromYaml -}}
    {{- if $providerObj.aws.enabled   -}}
        {{- $enabled = false -}}
    {{- else if $providerObj.gcp.enabled -}}
        {{- $enabled = false -}}
    {{- else if $providerObj.azure.enabled -}}
        {{- $enabled = false -}}
    {{- else if $providerObj.digitalocean.enabled  -}}
        {{- $enabled = false -}}
    {{- end -}}
    {{- print $enabled -}}
{{- end -}}

{{/*
  Returns the name of the cloud provider used for registry storage. If no cloud provider is enabled, then n/a is returned
  When using deprecated cloud.provider, this provider value is used.
*/}}
{{- define "okteto.registry.storage.cloudProvider" -}}
    {{- $providerObj := include "okteto.registry.storage.provider" . | trim | nindent 2 | fromYaml -}}

    {{- $provider := "ephemeral" -}}
    {{- if .Values.registry.storage.filesystem.persistence.enabled -}}
      {{- $provider = "persistent" -}}
    {{- end -}}
    
    {{- if $providerObj.aws.enabled -}}
        {{- $provider = "aws" -}}
    {{- else if $providerObj.gcp.enabled -}}
        {{- $provider = "gcp" -}}
    {{- else if $providerObj.azure.enabled -}}
        {{- $provider = "azure" -}}
    {{- else if $providerObj.digitalocean.enabled -}}
        {{- $provider = "digitalocean" -}}
    {{- end -}}
    {{- print $provider -}}
{{- end -}}

{{/*
    Returns registry.storage.provider yaml string
    If "okteto.cloud.provider.isEnabled" value is taken from cloud.provider
*/}}
{{- define "okteto.registry.storage.provider" -}}
    {{- if eq (include "okteto.cloud.provider.isEnabled" . ) "true" -}}
        {{- print (toYaml .Values.cloud.provider) -}}
    {{- else -}}
        {{- print (toYaml .Values.registry.storage.provider)  -}}
    {{- end -}}
{{- end -}}

{{/*
    Returns registry.secret yaml string
    If "okteto.cloud.provider.isEnabled" value is taken from cloud.secret, in this case key is parsed to secretKey
*/}}
{{- define "okteto.registry.secret" -}}
    {{- if eq (include "okteto.cloud.provider.isEnabled" . ) "true" -}}
        {{ $secret := omit .Values.cloud.secret "secretKey"  }}
        {{ $secret = set $secret "secretKey" .Values.cloud.secret.key }}
        {{- print (toYaml $secret) -}}
    {{- else -}}
        {{- print (toYaml .Values.registry.secret)  -}}
    {{- end -}}
{{- end -}}

