# Secrets

This chart requires several secrets to be created before installation. You have two options:

## Option 1: Use the Secrets Template (Recommended)

Use the provided template to create all required secrets in one step:

```bash
kubectl apply -f charts/tokenvisor-openshift/docs/SECRETS_TEMPLATE.yaml
```

If you are using a packaged chart:

```bash
helm pull <repo>/tokenvisor --version <ver> --untar
kubectl apply -f tokenvisor/docs/SECRETS_TEMPLATE.yaml
```

## Option 2: Let Helm Create Secrets

You can also let Helm create secrets for you by setting `.secrets.create: true` in values.yaml for each component. However, the template approach (Option 1) is recommended for better control.

## Required Secrets

The chart **fails fast** if these secrets are missing (defaults point to these names).

### clickhouse-secret (for ClickHouse)

Required by ClickHouse operator for cluster authentication and user management.

**Secret keys:**
- `cluster_secret`: Cluster authentication secret
- `db_user_password`: Main user password (emuuser)
- `db_readonly_user_password`: Readonly user password (emu_readonly)

**Important Security Note:** ClickHouse stores passwords in XML configuration files. **DO NOT use XML special characters** in passwords: `< > & ' "`. Use only alphanumeric characters and simple symbols: `a-z, A-Z, 0-9, -, _`.

**Example good passwords:** `emupassword`, `my-secure-pw-2025`, `Pass1234`
**Example BAD passwords (will fail):** `<password>`, `"x&y&z"`, `'quote'`, `tag >`

### pg-emu-user-secret (for PostgreSQL)

Required by CloudNativePG for EMU database user authentication.

**Secret keys:**
- `username`: Database username (default: `emupg`)
- `password`: Database password

**Type:** `kubernetes.io/basic-auth`

### vmuser-secret (for VictoriaMetrics)

Required for VictoriaMetrics authentication.

**Secret keys:**
- `password`: VM authentication password

### studio-secret (for Studio UI)

Required by Studio frontend for authentication.

**Secret keys:**
- `STUDIO_AUTH_SECRET`: Studio authentication secret

### emu-secret (for EMU backend)

Required by EMU backend for database connection and provider API keys.

**Required secret keys:**
- `EMU_DB_PATH`: PostgreSQL connection string
  - Format: `postgresql+psycopg://emupg:password@tokenvisor-pgbouncer.tokenvisor.svc.cluster.local:5432/emu`
  - **Important:** The password in `EMU_DB_PATH` must match `pg-emu-user-secret.password`
  - Keep this value in sync with values.yaml `emu.config.EMU_DB_PATH`

- `EMU_SERVICE_KEY`: Service authentication key

**Optional provider API keys** (add only the ones you need):
- `EMU_OPENAI_API_KEY`: OpenAI API key
- `EMU_HUGGINGFACE_API_KEY`: Hugging Face API key
- `EMU_OPENROUTER_API_KEY`: OpenRouter API key
- `EMU_ANTHROPIC_API_KEY`: Anthropic API key
- `EMU_CEREBRAS_API_KEY`: Cerebras API key
- `EMU_COHERE_API_KEY`: Cohere API key
- `EMU_GEMINI_API_KEY`: Google Gemini API key
- `EMU_GROQ_API_KEY`: Groq API key
- `EMU_HYPERBOLIC_API_KEY`: Hyperbolic API key
- `EMU_JINA_AI_API_KEY`: Jina AI API key
- `EMU_SAMBANOVA_API_KEY`: SambaNova API key
- `EMU_TOGETHER_AI_API_KEY`: Together AI API key
- `EMU_VOYAGE_API_KEY`: Voyage API key
- `EMU_RESEND_API_KEY`: Resend API key

## Optional Secrets

### grafana-secret (for Grafana)

Only required if Grafana is enabled in Helm values.

**Secret keys:**
- `admin_password`: Grafana admin password

**Note:** Grafana also reads the ClickHouse readonly password from `clickhouse-secret` (`db_readonly_user_password` key) for datasource configuration.

## How Secrets Are Used

### EMU + OTEL behavior
- EMU reads `EMU_DB_PATH` and `EMU_SERVICE_KEY` from `emu-secret`
- The password in `EMU_DB_PATH` must match `pg-emu-user-secret.password`
- EMU reads `EMU_VICTORIA_METRICS_PASSWORD` from `vmuser-secret`
- OTEL reads `CH_PASSWORD` from `clickhouse-secret`

This design avoids configmap/secret drift by having services read directly from secrets.

### Secret Creation by Templates

The chart can create secrets via templates if you enable `.secrets.create: true` in values.yaml:

- `templates/clickhouse-secret.yaml`: Creates `clickhouse-secret`
- `templates/cnpg-secret.yaml`: Creates `pg-emu-user-secret`
- `templates/victoriametrics-secret.yaml`: Creates `vmuser-secret`
- `templates/studio-secret.yaml`: Creates `studio-secret`
- `templates/emu-secret.yaml`: Creates `emu-secret`

**Note:** If you use the template approach, you must provide the secret values in `values.yaml` under each component's `.secrets.data` section.

## Custom Secret Names or Keys

If your secret names or keys differ from the defaults, you can customize the references:

```yaml
emu:
  secretRefs:
    clickhouseSecretName: my-clickhouse-secret
    clickhousePasswordKey: my-password-key
    vmuserSecretName: my-vm-secret
    vmuserPasswordKey: my-vm-password-key

grafana:
  adminSecret:
    name: my-grafana-secret
    key: my-admin-password
  clickhouseSecret:
    name: my-clickhouse-readonly-secret
    key: my-readonly-password
```
