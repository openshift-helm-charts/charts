{{- define "cryostat.reportsAuthProxy" -}}
{{- if (.Values.authentication.openshift).enabled }}
- name: {{ printf "%s-reports-%s" .Chart.Name "authproxy" }}
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
  {{- with (.Values.openshiftOauthProxy.config.extra).inPod.reports.envVars }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  envFrom:
  {{- with (.Values.openshiftOauthProxy.config.extra).envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  {{- with (.Values.openshiftOauthProxy.config.extra).inPod.reports.envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  args:
    - --pass-access-token=false
    - --pass-user-bearer-token=false
    - --pass-basic-auth=false
    - --htpasswd-file=/etc/oauth2_proxy/basicauth/htpasswd
    - --upstream=http://localhost:10001/
    - --cookie-secret=$(COOKIE_SECRET)
    - --request-logging=true
    - --openshift-service-account={{ include "cryostat.serviceAccountName" . }}
    - --proxy-websockets=true
    - --http-address=0.0.0.0:4180
    - --https-address=:8443
    - --tls-cert=/etc/tls/private/tls.crt
    - --tls-key=/etc/tls/private/tls.key
    - --proxy-prefix=/oauth2
    - --bypass-auth-for=^/health$
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
    - name: {{ .Release.Name }}-proxy-tls
      mountPath: /etc/tls/private
    - name: {{ .Release.Name }}-reports-secret
      mountPath: /etc/oauth2_proxy/basicauth
      readOnly: true
  terminationMessagePath: /dev/termination-log
  terminationMessagePolicy: File
{{- else if .Values.oauth2Proxy.tls.selfSigned.enabled }}
- name: {{ printf "%s-reports-%s" .Chart.Name "authproxy" }}
  securityContext:
    {{- toYaml (.Values.oauth2Proxy).securityContext | nindent 4 }}
  image: "{{ (.Values.oauth2Proxy).image.repository }}:{{ (.Values.oauth2Proxy).image.tag }}"
  imagePullPolicy: {{ (.Values.oauth2Proxy).image.pullPolicy }}
  env:
  - name: OAUTH2_PROXY_CLIENT_ID
    value: dummy
  - name: OAUTH2_PROXY_CLIENT_SECRET
    value: none
  - name: OAUTH2_PROXY_HTTP_ADDRESS
    value: 0.0.0.0:4180
  - name: OAUTH2_PROXY_HTTPS_ADDRESS
    value: :8443
  - name: OAUTH2_PROXY_TLS_CERT_FILE
    value: /etc/tls/private/cert
  - name: OAUTH2_PROXY_TLS_KEY_FILE
    value: /etc/tls/private/key
  - name: OAUTH2_PROXY_UPSTREAMS
    value: http://localhost:10001/
  - name: OAUTH2_PROXY_REDIRECT_URL
    value: "http://localhost:4180/oauth2/callback"
  - name: OAUTH2_PROXY_COOKIE_SECRET
    valueFrom:
      secretKeyRef:
        name: {{ default (printf "%s-cookie-secret" .Release.Name) .Values.authentication.cookieSecretName }}
        key: COOKIE_SECRET
        optional: false
  - name: OAUTH2_PROXY_EMAIL_DOMAINS
    value: "*"
  - name: OAUTH2_PROXY_HTPASSWD_USER_GROUP
    value: write
  - name: OAUTH2_PROXY_HTPASSWD_FILE
    value: /etc/oauth2_proxy/basicauth/htpasswd
  - name: OAUTH2_PROXY_SKIP_AUTH_ROUTES
    value: "^/health$"
  - name: OAUTH2_PROXY_PROXY_WEBSOCKETS
    value: "false"
  {{- with (.Values.oauth2Proxy.config.extra).envVars }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  {{- with (.Values.oauth2Proxy.config.extra).inPod.reports.envVars }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  envFrom:
  {{- with (.Values.oauth2Proxy.config.extra).envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  {{- with (.Values.oauth2Proxy.config.extra).inPod.reports.envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  ports:
    - containerPort: 4180
      name: http
      protocol: TCP
    - containerPort: 8443
      name: https
      protocol: TCP
  resources:
    {{- toYaml .Values.oauth2Proxy.resources | nindent 4 }}
  volumeMounts:
    - name: {{ .Release.Name }}-reports-secret
      mountPath: /etc/oauth2_proxy/basicauth
      readOnly: true
    {{- if .Values.oauth2Proxy.tls.selfSigned.enabled }}
    - name: {{ .Release.Name }}-oauth2proxy-reports-tls
      mountPath: /etc/tls/private
    {{- end }}
{{- else }}
- name: {{ printf "%s-reports-%s" .Chart.Name "authproxy" }}
  securityContext:
    {{- toYaml (.Values.oauth2Proxy).securityContext | nindent 4 }}
  image: "{{ (.Values.oauth2Proxy).image.repository }}:{{ (.Values.oauth2Proxy).image.tag }}"
  imagePullPolicy: {{ (.Values.oauth2Proxy).image.pullPolicy }}
  env:
  - name: OAUTH2_PROXY_CLIENT_ID
    value: dummy
  - name: OAUTH2_PROXY_CLIENT_SECRET
    value: none
  - name: OAUTH2_PROXY_HTTP_ADDRESS
    value: 0.0.0.0:4180
  - name: OAUTH2_PROXY_UPSTREAMS
    value: http://localhost:10001/
  - name: OAUTH2_PROXY_REDIRECT_URL
    value: "http://localhost:4180/oauth2/callback"
  - name: OAUTH2_PROXY_COOKIE_SECRET
    valueFrom:
      secretKeyRef:
        name: {{ default (printf "%s-cookie-secret" .Release.Name) .Values.authentication.cookieSecretName }}
        key: COOKIE_SECRET
        optional: false
  - name: OAUTH2_PROXY_EMAIL_DOMAINS
    value: "*"
  - name: OAUTH2_PROXY_HTPASSWD_USER_GROUP
    value: write
  - name: OAUTH2_PROXY_HTPASSWD_FILE
    value: /etc/oauth2_proxy/basicauth/htpasswd
  - name: OAUTH2_PROXY_SKIP_AUTH_ROUTES
    value: "^/health$"
  - name: OAUTH2_PROXY_PROXY_WEBSOCKETS
    value: "false"
  {{- with (.Values.oauth2Proxy.config.extra).envVars }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  {{- with (.Values.oauth2Proxy.config.extra).inPod.reports.envVars }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  envFrom:
  {{- with (.Values.oauth2Proxy.config.extra).envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  {{- with (.Values.oauth2Proxy.config.extra).inPod.reports.envSources }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
  ports:
    - containerPort: 4180
      name: http
      protocol: TCP
  resources:
    {{- toYaml .Values.oauth2Proxy.resources | nindent 4 }}
  volumeMounts:
    - name: {{ .Release.Name }}-reports-secret
      mountPath: /etc/oauth2_proxy/basicauth
      readOnly: true
{{- end }}
{{- end}}
