{{- define "lcs.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "lcs.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" (include "lcs.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "lcs.labels" -}}
app.kubernetes.io/name: {{ include "lcs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
env: {{ .Values.global.env }}
{{- end -}}

{{- define "lcs.selectorLabels" -}}
app.kubernetes.io/name: {{ include "lcs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Do not set runAsUser: OpenShift restricted SCC assigns the namespace UID. */}}
{{- define "lcs.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "lcs.containerSecurityContext" -}}
allowPrivilegeEscalation: false
capabilities:
  drop:
    - ALL
runAsNonRoot: true
readOnlyRootFilesystem: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "lcs.serviceAccountName" -}}
{{- default "lcs" .Values.serviceAccount.name -}}
{{- end -}}

{{- define "lcs.podIdentity" -}}
serviceAccountName: {{ include "lcs.serviceAccountName" . }}
automountServiceAccountToken: false
{{- end -}}

{{- define "lcs.containerLifecycle" -}}
lifecycle:
  postStart:
    exec:
      command: ["/bin/true"]
  preStop:
    exec:
      command: ["/bin/sleep", "2"]
{{- end -}}

{{- define "lcs.terminationMessagePolicy" -}}
terminationMessagePolicy: FallbackToLogsOnError
{{- end -}}

{{- define "lcs.initResources" -}}
{{- toYaml .Values.global.initResources -}}
{{- end -}}

{{- define "lcs.tmpVolume" -}}
- name: tmp
  emptyDir: {}
{{- end -}}

{{- define "lcs.tmpVolumeMount" -}}
- name: tmp
  mountPath: /tmp
{{- end -}}

{{- define "lcs.serviceDualStack" -}}
ipFamilyPolicy: {{ .Values.global.ipFamilyPolicy }}
{{- end -}}

{{- define "lcs.certsuiteLabels" -}}
{{- if .Values.global.certsuite.target }}
redhat-best-practices-for-k8s.com/generic: target
{{- end }}
{{- end -}}

{{- define "lcs.plainImage" -}}
{{- $repo := .repository -}}
{{- $tag := .tag | default "" -}}
{{- $digest := .digest | default "" -}}
{{- if and $tag $digest -}}
{{- printf "%s:%s@%s" $repo $tag $digest -}}
{{- else if $digest -}}
{{- printf "%s@%s" $repo $digest -}}
{{- else -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}
{{- end -}}

{{- define "lcs.waitImage" -}}
{{- include "lcs.plainImage" .Values.global.waitImage -}}
{{- end -}}

{{- define "lcs.image" -}}
{{- $repo := .repo -}}
{{- $tag := .tag | default "" -}}
{{- $digest := .digest | default "" -}}
{{- $registry := .root.Values.global.imageRegistry -}}
{{- $ref := $repo -}}
{{- if $registry -}}
{{- $ref = printf "%s/%s" $registry $repo -}}
{{- end -}}
{{- if and $tag $digest -}}
{{- printf "%s:%s@%s" $ref $tag $digest -}}
{{- else if $digest -}}
{{- printf "%s@%s" $ref $digest -}}
{{- else -}}
{{- printf "%s:%s" $ref $tag -}}
{{- end -}}
{{- end -}}
