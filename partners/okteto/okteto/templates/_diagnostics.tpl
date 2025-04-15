
{{- define "okteto.diagnostics.preflightSpec" -}}
apiVersion: troubleshoot.sh/v1beta2
kind: Preflight
metadata:
  name: {{ include "okteto.fullname" . }}-preflight
spec:
  analyzers:
    - clusterVersion:
        outcomes:
          - fail:
              when: "< 1.30.0"
              message: Okteto requires at least Kubernetes 1.30.0
              uri: https://www.okteto.com/docs/release-notes/
          - fail:
              when: ">= 1.33.0"
              message: Okteto requires a Kubernetes version between 1.30 and 1.32
              uri: https://www.okteto.com/docs/release-notes/
          - pass:
              message: Your cluster version meets the Okteto requirements
{{- end -}}

{{- define "okteto.diagnostics.supportBundleSpec" -}}
apiVersion: troubleshoot.sh/v1beta2
kind: SupportBundle
metadata:
  name: {{ include "okteto.fullname" . }}-support-bundle
  namespace: 
spec:
  collectors:
    - clusterResources:
        namespaces:
        - {{ .Release.Namespace }}
    - certificates: 
        secrets:
          - name: {{ include "okteto.tlsSecret" . }}
            collectorName: "wildcard-certificate"
            namespaces:
              - {{ .Release.Namespace }}
          - name: {{ include "okteto.ingress.tlsSecret" . }}
            collectorName: "ingress-certificate"
            namespaces:
              - {{ .Release.Namespace }}
          - name: {{ include "okteto.registry.tlsSecret" . }}
            collectorName: "registry-certificate"
            namespaces:
              - {{ .Release.Namespace }}
          - name: {{ include "okteto.buildkit.tlsSecret" . }}
            collectorName: "buildkit-certificate"
            namespaces:
              - {{ .Release.Namespace }}
          - name: {{ include "okteto.webhook" . }}
            collectorName: "webhook-certificate"
            namespaces:
              - {{ .Release.Namespace }}
          - name: {{ include "okteto.fullname" . }}-regcreds
            collectorName: "regcreds-certificate"
            namespaces:
              - {{ .Release.Namespace }}
    - configMap:
        namespace: {{ .Release.Namespace }}
        name: "{{ include "okteto.fullname" . }}"
        includeAllData: true

    - logs:
        name: api-logs
        selector:
          - app.kubernetes.io/component=api
    - logs:
        name: daemon-logs
        selector:
          - app.kubernetes.io/component=daemon
    - logs:
        name: installer-logs
        selector:
          - app.kubernetes.io/component=installer
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: buildkit-logs
        selector:
          - app.kubernetes.io/component=buildkit
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: frontend-logs
        selector:
          - app.kubernetes.io/component=frontend
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: ingress-nginx-logs
        selector:
          - app.kubernetes.io/component=controller
          - app.kubernetes.io/part-of=ingress-nginx
    - logs:
        name: okteto-nginx-logs
        selector:
          - app.kubernetes.io/component=controller
          - app.kubernetes.io/part-of=okteto-nginx
    {{/*
    ingress-nginx-logs-alternative and okteto-nginx-logs are alternative way of getting controllers logs for installations
    made with ArgoCD, as the value of the label app.kubernetes.io/part-of is not set to the same value when it is generated
    with ArgoCD
    */}}
    - logs:
        name: ingress-nginx-logs-alternative
        selector:
          - app.kubernetes.io/component=controller
          - app.kubernetes.io/name=ingress-nginx
    - logs:
        name: okteto-nginx-logs-alternative
        selector:
          - app.kubernetes.io/component=controller
          - app.kubernetes.io/name=okteto-nginx
    - logs:
        name: defaultbackend-logs
        selector:
          - app.kubernetes.io/component=default-backend
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: webhook-logs
        selector:
          - app.kubernetes.io/component=webhook
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: migration-logs
        selector:
          - app.kubernetes.io/component=migration
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: private-endpoints-logs
        selector:
          - app.kubernetes.io/component=private-endpoints
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: regcreds-logs
        selector:
          - app.kubernetes.io/component=regcreds
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: eventsexporter-logs
        selector:
          - app.kubernetes.io/component=eventsexporter
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: sleep-jobs-logs
        selector:
          - app.kubernetes.io/component=namespace-sleep
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: wake-jobs-logs
        selector:
          - app.kubernetes.io/component=namespace-wake-all
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: namespace-destroy-all-jobs-logs
        selector:
          - app.kubernetes.io/component=namespace-destroy-all
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: resourcemanager-logs
        selector:
          - app.kubernetes.io/component=resourcemanager
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: sshagent-logs
        selector:
          - app.kubernetes.io/component=ssh-agent
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: periodic-metrics-logs
        selector:
          - app.kubernetes.io/component=periodic-metrics
          - app.kubernetes.io/part-of=okteto
    - logs:
        name: registry-logs
        selector:
          - app.kubernetes.io/component=registry
          - app.kubernetes.io/part-of=okteto
    - secret:
        collectorName: cloud-secret
        namespace: {{ .Release.Namespace }}
        name: {{ .Values.cloud.secret.name }}
    - helm:
        collectorName: helm-info
        namespace: {{ .Release.Namespace }}
    - runPod:
        name: helm-values-computed
        collectorName: helm-values-computed
        namespace: {{ .Release.Namespace }}
        podSpec:
          serviceAccountName: {{ include "okteto.fullname" . }}
          containers:
          - name: helm-values-computed
            image: {{ include "okteto.formatRegistryAndRepo" .Values.cli.image }}:{{ include "okteto.cliVersion" . }}
            command: ["helm"]
            args: ["get", "values", "{{ .Release.Name }}", "--all", "-o", "yaml"]
    - runPod:
        name: helm-values-user
        collectorName: helm-values-user
        namespace: {{ .Release.Namespace }}
        podSpec:
          serviceAccountName: {{ include "okteto.fullname" . }}
          containers:
          - name: helm-values-user
            image: {{ include "okteto.formatRegistryAndRepo" .Values.cli.image }}:{{ include "okteto.cliVersion" . }}
            command: ["helm"]
            args: ["get", "values", "{{ .Release.Name }}", "-o", "yaml"]
{{- end -}}

{{- define "okteto.diagnostics.redactorSpec" -}}
apiVersion: troubleshoot.sh/v1beta2
kind: Redactor
metadata:
  name: {{ include "okteto.fullname" . }}-redactor
spec:
  redactors:
    - name: "redact helm values output"
      fileSelector:
        file: "**/helm-values-*/**"
      removals:
        yamlPath:
        - "license"
        - "auth.*.clientSecret"
        - "auth.*.clientId"
        - "auth.token.adminToken"
        - "cookie.secret"
        - "cookie.hash"
        - "github.appId"
        - "github.appPrivateKey"
        - "github.clientId"
        - "github.clientSecret"
        - "privateEndpoints.clientSecret"
        - "privateEndpoints.clientID"
    - name: "redact service accounts"
      removals:
        regex:
          - redactor: '("dev\.okteto\.com\/)(token|external-id|private-endpoint|email|githubid|original-external-id|avatar|config)(": ")(?P<mask>.*)(")'

{{- end -}}
