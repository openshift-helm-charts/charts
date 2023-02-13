{{/*
Expand the name of the chart.
*/}}
{{- define "a10tkc.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "a10tkc.fullname" -}}
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
{{- define "a10tkc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "a10tkc.labels" -}}
helm.sh/chart: {{ include "a10tkc.chart" . }}
{{ include "a10tkc.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "a10tkc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "a10tkc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "a10tkc.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "a10tkc.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Create the arguments for a10-a10tkc container
*/}}
{{- define "a10tkc.container.args" -}}
- --watch-namespace={{ .Values.args.watchNamespace | quote}}
- --ingress-class={{ .Values.args.ingressClass | quote }}
- --use-node-external-ip={{ .Values.args.useNodeExternalIp }}
- --patch-to-update={{ .Values.args.PatchToUpdate }}
- --safe-acos-delete={{ .Values.args.safeDelete }} 
- --use-ingress-class-only={{ .Values.args.useIngressClassOnly }}  
- --include-all-nodes={{ .Values.args.includeAllNodes }}
- --use-os-routes={{ .Values.args.useOpenShiftRoutes }}
{{- end }}


{{/*
Create environment variables for a10tkc container
*/}}
{{- define "a10tkc.container.env" -}}
- name: POD_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
- name: WATCH_NAMESPACE
  value: {{ .Values.args.watchNamespace  | default "api_v1.NamespaceAll" | quote }}
- name: CONTROLLER_URL
  value: {{required "CONTROLLER_URL is required!" .Values.env.lbUrl | quote }}
- name: ACOS_USERNAME_PASSWORD_SECRETNAME
  value: {{ template "a10tkc.fullname" . }}-secret
- name: PARTITION 
  value: {{ .Values.env.partition | default "shared" | quote }}
{{- if .Values.env.config_overlay.enable }}
- name: CONFIG_OVERLAY
  value: {{ .Values.env.config_overlay.enable | default "true" | quote }}
- name: OVERLAY_ENDPOINT_IP
  value: {{ required "OVERLAY_ENDPOINT_IP is required" .Values.env.config_overlay.overlay_endpoint_ip }}
- name: VTEP_ENCAPSULATION
  value: {{ .Values.env.config_overlay.vtep_encapsulation | default "ip-encap" | quote  }}
{{- end }}
{{- if .Values.env.config_overlay.lif_ippool }}
- name: LIF_ADDR_IPPOOL
  value: {{ .Values.env.config_overlay.lif_ippool | quote }}
{{- end }}
{{- if eq .Values.env.acosMemory.enable true }}
- name: ACOS_MEMORY_SAVE
  value: {{ .Values.env.acosMemory.enable }}
- name: ACOS_MEMORY_SAVE_INTERVAL 
  value: {{ .Values.env.acosMemory.saveInterval | default "3m" | quote }} 
{{- end }}
{{- if eq .Values.env.ipUnNumbered.enable true }}
- name: IP_UNNUMBERED_LIF
  value: true
- name: IP_UNNUMBERED_SOURCE_IP
  value: {{ required "SourceIP  is required" .Values.env.ipUnNumbered.sourceIp | quote }}
- name: LOOPBACK_INTERFACE_ID
  value: {{ required "LoopbackInterfaceId  is required" .Values.env.ipUnNumbered.loopBackInterfaceId}}
{{- end }}  
{{- if eq .Values.env.bgp.enable true }}
- name: BGP_ROUTE
  value: {{ .Values.env.bgp.enable | quote }}
- name: BGP_ROUTER_AS_NUMBER
  value: {{ .Values.env.bgp.bgpRouterAsNumber | default 106  }}
  {{- if .Values.env.bgp.bgpNetworks }}
- name: BGP_NETWORKS
  value: {{ .Values.env.bgp.bgpNetworks | quote }}
  {{- end }}
  {{- if .Values.env.bgp.bgpNeighbors }}
- name: BGP_NEIGHBORS
  value: {{ .Values.env.bgp.bgpNeighbors | quote }}
  {{- end }}
{{- end }}
{{- end }}




