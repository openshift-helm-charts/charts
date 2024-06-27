{{/*
Expand the name of the chart.
*/}}
{{- define "cryostat.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "cryostat.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "cryostat.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "cryostat.labels" -}}
helm.sh/chart: {{ include "cryostat.chart" . }}
{{ include "cryostat.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "cryostat.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cryostat.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use.
*/}}
{{- define "cryostat.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "cryostat.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get or generate a default connection key for database.
*/}}
{{- define "cryostat.databaseConnectionKey" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-db" .Release.Name)) -}}
{{- if $secret -}}
{{/*
   Use current key. Do not regenerate.
*/}}
{{- $secret.data.CONNECTION_KEY -}}
{{- else -}}
{{/*
    Generate new key.
*/}}
{{- (randAlphaNum 32) | b64enc | quote -}}
{{- end -}}
{{- end -}}

{{/*
Get or generate a default encryption key for database.
*/}}
{{- define "cryostat.databaseEncryptionKey" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-db" .Release.Name)) -}}
{{- if $secret -}}
{{/*
   Use current key. Do not regenerate.
*/}}
{{- $secret.data.ENCRYPTION_KEY -}}
{{- else -}}
{{/*
    Generate new key
*/}}
{{- (randAlphaNum 32) | b64enc | quote -}}
{{- end -}}
{{- end -}}

{{/*
Get or generate a default secret key for object storage.
*/}}
{{- define "cryostat.objectStorageSecretKey" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-storage" .Release.Name)) -}}
{{- if $secret -}}
{{/*
   Use current secret. Do not regenerate.
*/}}
{{- $secret.data.SECRET_KEY -}}
{{- else -}}
{{/*
    Generate new secret
*/}}
{{- (randAlphaNum 32) | b64enc | quote -}}
{{- end -}}
{{- end -}}

{{/*
Generate or retrieve a default value for cookieSecret.
*/}}
{{- define "cryostat.cookieSecret" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-cookie-secret" .Release.Name)) -}}
{{- if $secret -}}
{{/*
   Use the current secret. Do not regenerate.
*/}}
{{- $secret.data.COOKIE_SECRET | b64dec | quote -}}
{{- else -}}
{{/*
    Generate a new secret.
*/}}
{{- $newSecret := randAlphaNum 24 | b64enc -}}
{{- $newSecret | quote -}}
{{- end }}
{{- end }}

{{/*
    Get sanitized list or defaults (if not disabled) as comma-separated list.
*/}}
{{- define "cryostat.commaSepList" -}}
{{- $l := index . 0 -}}
{{- $default := index . 1 -}}
{{- $disableDefaults := index . 2 -}}
{{- if and (not $l) (not $disableDefaults) -}}
{{- $l = list $default -}}
{{- end -}}
{{- join "," (default list $l | compact | uniq) | quote -}}
{{- end -}}
