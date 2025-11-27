{{/*
Create OpenShift OAuth Proxy container.
*/}}
{{- define "cryostat.openshiftOauthProxy" -}}
- name: {{ printf "%s-%s" .Chart.Name "authproxy" }}
  securityContext:
    {{- toYaml .Values.openshiftOauthProxy.securityContext | nindent 4 }}
  image: "{{ .Values.openshiftOauthProxy.image.repository }}:{{ .Values.openshiftOauthProxy.image.tag }}"
  env:
  - name: COOKIE_SECRET
    valueFrom:
      secretKeyRef:
        name: {{ default (printf "%s-cookie-secret" .Release.Name) .Values.authentication.cookieSecretName }}
        key: COOKIE_SECRET
        optional: false
  {{- with (.Values.openshiftOauthProxy.config.extra).envVars }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  {{- with (.Values.openshiftOauthProxy.config.extra).inPod.main.envVars }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  envFrom:
  {{- with (.Values.openshiftOauthProxy.config.extra).envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  {{- with (.Values.openshiftOauthProxy.config.extra).inPod.main.envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  args:
    - --skip-provider-button={{ not .Values.authentication.basicAuth.enabled }}
    - --pass-access-token=false
    - --pass-user-bearer-token=false
    - --pass-basic-auth=false
    - --upstream=http://localhost:8181/
    - --upstream=http://localhost:3000/grafana/
    - --cookie-secret=$(COOKIE_SECRET)
    - --openshift-service-account={{ include "cryostat.serviceAccountName" . }}
    - --proxy-websockets=true
    - --http-address=0.0.0.0:4180
    - --https-address=:8443
    - --tls-cert=/etc/tls/private/tls.crt
    - --tls-key=/etc/tls/private/tls.key
    - --proxy-prefix=/oauth2
    {{- if .Values.openshiftOauthProxy.accessReview.enabled }}
    - --openshift-sar=[{{ tpl ( omit .Values.openshiftOauthProxy.accessReview "enabled" | toJson ) . }}]
    - --openshift-delegate-urls={"/":{{ tpl ( omit .Values.openshiftOauthProxy.accessReview "enabled" | toJson ) . }}}
    {{- end }}
    - --bypass-auth-for=^/health(/liveness)?$
    {{- if .Values.authentication.basicAuth.enabled }}
    - --htpasswd-file=/etc/openshift_oauth_proxy/basicauth/{{ .Values.authentication.basicAuth.filename }}
    {{- end }}
  imagePullPolicy: {{ .Values.openshiftOauthProxy.image.pullPolicy }}
  ports:
    - containerPort: 4180
      name: http
      protocol: TCP
    - containerPort: 8443
      name: https
      protocol: TCP
  resources:
    {{- toYaml .Values.openshiftOauthProxy.resources | nindent 4 }}
  volumeMounts:
    {{- if .Values.authentication.basicAuth.enabled }}
    - name: {{ .Release.Name }}-htpasswd
      mountPath: /etc/openshift_oauth_proxy/basicauth
      readOnly: true
    {{- end }}
    - name: {{ .Release.Name }}-proxy-tls
      mountPath: /etc/tls/private
  terminationMessagePath: /dev/termination-log
  terminationMessagePolicy: File
{{- end}}
