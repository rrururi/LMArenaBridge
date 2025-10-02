## 🔐 Environment Variables for Deployment

For easier deployment to cloud platforms like Render.com, Heroku, or Docker, you can use environment variables instead of configuration files for sensitive credentials.

### Dashboard Admin Credentials

Set these environment variables to automatically create an admin user on first startup:

```bash
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password
```

The dashboard server will:
- Check if any users exist in the database
- If no users exist, create an admin user with the provided credentials
- If users already exist, skip creation to avoid conflicts

### Worker Authentication Tokens

For cloud worker architecture, set worker tokens via environment variable:

```bash
WORKER_TOKENS="token1,token2,token3"
```

**Format**: Comma-separated list of tokens

**Priority**: Environment variable takes precedence over `config.jsonc`

**Example for Render.com**:
1. Go to your service settings
2. Add environment variables in the "Environment" section
3. Set `WORKER_TOKENS` with your comma-separated tokens
4. Workers can now authenticate using these tokens

### Configuration Priority

The system uses the following priority order:

1. **Environment Variables** (highest priority)
   - `WORKER_TOKENS` for worker authentication
   - `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` for admin creation

2. **Configuration Files** (fallback)
   - `config.jsonc` for worker tokens (if `WORKER_TOKENS` not set)
   - Manual user creation via API or web interface (if admin env vars not set)

### Example: Render.com Deployment

```yaml
# render.yaml
services:
  - type: web
    name: lmarena-bridge
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python api_server.py
    envVars:
      - key: WORKER_TOKENS
        value: secret-token-1,secret-token-2
      - key: ADMIN_USERNAME
        value: admin
      - key: ADMIN_EMAIL  
        value: admin@yourdomain.com
      - key: ADMIN_PASSWORD
        generateValue: true  # Auto-generate secure password
```

### Security Best Practices

✅ **DO**:
- Use environment variables for production deployments
- Generate strong, unique tokens for each worker
- Rotate tokens periodically
- Use secrets management services (AWS Secrets Manager, etc.)

❌ **DON'T**:
- Commit tokens to version control
- Share tokens between environments (dev/staging/prod)
- Use simple or predictable token values
- Store tokens in plain text files in production
