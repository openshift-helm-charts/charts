{{/*
Create OAuth2 Proxy container. Configurations defined in alpha_config.yaml
*/}}
{{- define "cryostat.oauth2Proxy" -}}
- name: {{ printf "%s-%s" .Chart.Name "authproxy" }}
  securityContext:
    {{- toYaml (.Values.oauth2Proxy).securityContext | nindent 4 }}
  image: "{{ (.Values.oauth2Proxy).image.repository }}:{{ (.Values.oauth2Proxy).image.tag }}"
  args:
    - "--alpha-config=/etc/oauth2_proxy/alpha_config/alpha_config.yaml"
  imagePullPolicy: {{ (.Values.oauth2Proxy).image.pullPolicy }}
  env:
    - name: OAUTH2_PROXY_REDIRECT_URL
      value: "http://localhost:4180/oauth2/callback"
    - name: OAUTH2_PROXY_COOKIE_SECRET
      value: {{ include "cryostat.cookieSecret" . }}
    - name: OAUTH2_PROXY_EMAIL_DOMAINS
      value: "*"
    {{- if .Values.authentication.basicAuth.enabled }}
    - name: OAUTH2_PROXY_HTPASSWD_USER_GROUP
      value: write
    - name: OAUTH2_PROXY_HTPASSWD_FILE
      value: /etc/oauth2_proxy/basicauth/{{ .Values.authentication.basicAuth.filename }}
    {{- end }}
    {{- if not .Values.authentication.basicAuth.enabled }}
    - name: OAUTH2_PROXY_SKIP_AUTH_ROUTES
      value: ".*"
    {{- else }}
    - name: OAUTH2_PROXY_SKIP_AUTH_ROUTES
      value: "^/health(/liveness)?$"
    {{- end }}
  ports:
    - containerPort: 4180
      protocol: TCP
  volumeMounts:
    - name: alpha-config
      mountPath: /etc/oauth2_proxy/alpha_config
    {{- if .Values.authentication.basicAuth.enabled }}
    - name: {{ .Release.Name }}-htpasswd
      mountPath: /etc/oauth2_proxy/basicauth
      readOnly: true
    {{- end }}
{{- end}}
