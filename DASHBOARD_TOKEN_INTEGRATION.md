# Dashboard Token Integration Guide

## Overview

The LMArenaBridge main API server (`api_server.py`) is now fully integrated with the dashboard token system. This integration provides multi-user token management with automatic usage tracking and analytics.

## What Changed

### 1. Token Authentication

The API now supports **two authentication methods**:

#### A. Dashboard Tokens (Primary - Recommended)
- Multi-user support with individual tokens
- Automatic usage tracking and analytics
- Token expiration and revocation
- Per-user request history
- Managed through the web dashboard

#### B. Simple API Key (Fallback)
- Single shared key from `config.jsonc`
- No usage tracking
- No user management
- Used only when dashboard tokens are disabled or as fallback

### 2. Configuration

New option in `config.jsonc`:

```jsonc
{
  // Use Dashboard Token System
  // When enabled, uses the dashboard's multi-user token system
  // for authentication and usage tracking.
  "use_dashboard_tokens": true,
  
  // Simple API Key (fallback)
  // Used as backup when dashboard tokens fail or are disabled
  "api_key": ""
}
```

### 3. Usage Logging

When using dashboard tokens, all requests are automatically logged with:
- Token used (user identification)
- Model name
- Response time (milliseconds)
- HTTP status code
- Error messages (if any)
- Timestamp

## How to Use

### Option 1: Dashboard Token System (Recommended)

**Step 1: Start the Dashboard Server**
```bash
python dashboard_server.py
```
The dashboard runs on http://127.0.0.1:5105

**Step 2: Create User Account**

First user (admin):
```bash
curl -X POST http://127.0.0.1:5105/api/admin/init \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "your_secure_password"
  }'
```

Or register via the web interface at http://127.0.0.1:5105

**Step 3: Generate API Token**

1. Login to the dashboard
2. Go to the Tokens page (`/tokens`)
3. Click "Create New Token"
4. Give it a name (e.g., "My OpenAI Client")
5. Optionally set an expiration date
6. Copy the generated token (starts with `sk-lmarena-`)

**Step 4: Use the Token**

Configure your OpenAI-compatible client:
- **API Base URL**: `http://127.0.0.1:5102/v1`
- **API Key**: `sk-lmarena-xxxxxxxxxxxx` (your token)
- **Model**: Any model from your `models.json`

**Step 5: View Analytics**

Visit the dashboard to see:
- Total requests
- Response times
- Model usage breakdown
- Request history
- Charts and graphs

### Option 2: Simple API Key (Legacy)

**Step 1: Disable Dashboard Tokens**

Edit `config.jsonc`:
```jsonc
{
  "use_dashboard_tokens": false,
  "api_key": "your-secret-key-here"
}
```

**Step 2: Use the Key**

Configure your client with:
- **API Base URL**: `http://127.0.0.1:5102/v1`
- **API Key**: `your-secret-key-here`

**Note**: With this method, you won't get usage tracking or analytics.

## Authentication Flow

```
Client Request
     ↓
Authorization Header Check
     ↓
[Dashboard Tokens Enabled?]
     ↓ YES                    ↓ NO
Validate Dashboard Token    Use Simple API Key
     ↓ Valid?                    ↓ Valid?
     ↓ YES        ↓ NO          ↓ YES     ↓ NO
  Proceed    Try API Key     Proceed    Reject
                  ↓
            Valid API Key?
                  ↓
            YES / NO
```

## Benefits of Dashboard Token System

### Multi-User Support
- Each user has their own tokens
- Independent usage tracking
- Individual quotas (future feature)

### Security
- Tokens can be revoked instantly
- Expiration dates supported
- No need to share a single key
- User-level access control

### Analytics & Insights
- Track who's using what models
- Monitor response times
- Identify usage patterns
- Export data for analysis

### Management
- Web-based interface
- Create/revoke tokens easily
- View recent activity
- User account management

## API Endpoints

### Dashboard Server (Port 5105)

**Authentication**
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user info

**Token Management**
- `GET /api/tokens` - List user's tokens
- `POST /api/tokens` - Create new token
- `DELETE /api/tokens/{id}` - Revoke token

**Usage Stats**
- `GET /api/usage/summary?days=30` - Usage summary
- `GET /api/usage/logs?limit=100` - Recent logs

**Web Pages**
- `/` - Login page
- `/dashboard` - Main dashboard
- `/tokens` - Token management
- `/analytics` - Usage analytics

Full API documentation: http://127.0.0.1:5105/docs

### Main API Server (Port 5102)

**OpenAI-Compatible Endpoints**
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions

**Note**: Token authentication applies to `/v1/chat/completions`

## Database

The dashboard uses SQLite database (`dashboard.db`) with tables:
- `users` - User accounts
- `api_tokens` - Generated tokens
- `usage_logs` - Request history
- `sessions` - Login sessions

Location: `dashboard.db` (auto-created on first run)

## Troubleshooting

### Tokens not working

**Check 1**: Is the dashboard server running?
```bash
# Should see the dashboard server process
ps aux | grep dashboard_server
```

**Check 2**: Is the token active?
- Login to dashboard
- Check Tokens page
- Verify token is not expired or revoked

**Check 3**: Is `use_dashboard_tokens` enabled?
```bash
# Check config.jsonc
grep "use_dashboard_tokens" config.jsonc
```

**Check 4**: Check the logs
```bash
# Main server logs will show authentication attempts
python api_server.py
# Look for: "Dashboard token 验证成功" or "提供的 Token 无效"
```

### No usage data showing

**Check 1**: Are you using dashboard tokens?
- Simple API keys don't generate usage logs
- Only dashboard tokens are tracked

**Check 2**: Check the database
```bash
sqlite3 dashboard.db "SELECT COUNT(*) FROM usage_logs;"
```

**Check 3**: Verify time range
- Default analytics shows last 30 days
- Check if requests are within that range

## Migration Guide

### From Simple API Key to Dashboard Tokens

1. **Keep existing setup working**
   - Leave `api_key` in config.jsonc
   - This acts as fallback

2. **Start dashboard server**
   ```bash
   python dashboard_server.py
   ```

3. **Create user accounts**
   - Use the admin init endpoint
   - Or register via web interface

4. **Generate tokens**
   - Login to dashboard
   - Create tokens for each user/client

5. **Update clients gradually**
   - Replace old API key with new tokens
   - Test each client
   - Old API key still works as fallback

6. **Optional: Disable API key**
   - Once all clients use tokens
   - Set `api_key` to `""` in config.jsonc
   - Set `use_dashboard_tokens` to `true`

## Security Best Practices

1. **Use strong passwords** for dashboard accounts
2. **Set token expiration dates** when possible
3. **Revoke unused tokens** regularly
4. **Monitor usage logs** for suspicious activity
5. **Use HTTPS** in production (via reverse proxy)
6. **Don't share tokens** between users
7. **Rotate tokens periodically**
8. **Keep dashboard.db secure** (contains hashed passwords)

## Future Enhancements

Potential features to add:
- Rate limiting per user/token
- Usage quotas
- Billing integration
- Role-based access control
- IP whitelist/blacklist
- Webhook notifications
- API usage reports via email

## Example Integration Code

### Python
```python
import openai

client = openai.OpenAI(
    base_url="http://127.0.0.1:5102/v1",
    api_key="sk-lmarena-your-token-here"
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### cURL
```bash
curl http://127.0.0.1:5102/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-lmarena-your-token-here" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Support

For issues or questions:
1. Check this guide
2. Review dashboard logs
3. Check main server logs
4. Open an issue on GitHub

## Summary

The dashboard token integration provides:
- ✅ Multi-user token management
- ✅ Automatic usage tracking
- ✅ Web-based dashboard
- ✅ Backward compatibility with simple API keys
- ✅ Detailed analytics
- ✅ Security features (expiration, revocation)
- ✅ Easy migration path

The integration is **enabled by default** but falls back to the simple API key if needed, ensuring no breaking changes to existing setups.
