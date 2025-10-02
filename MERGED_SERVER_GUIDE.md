# Merged Server Guide

## Overview
The `merged_server.py` file combines both `api_server.py` and `dashboard_server.py` into a single server that runs on **port 5102**.

## What's Included

### API Server Features (from api_server.py)
- ✅ OpenAI-compatible API endpoints (`/v1/chat/completions`, `/v1/models`)
- ✅ WebSocket connection for browser script (`/ws`)
- ✅ Model management and updates
- ✅ File uploading and processing
- ✅ Session and message ID handling

### Dashboard Features (from dashboard_server.py)
- ✅ User authentication and management
- ✅ API token creation and management
- ✅ Usage statistics and analytics
- ✅ Web interface for dashboard, tokens, and analytics

## How to Run

Instead of running two separate servers, you now only need to run one:

```bash
python3 merged_server.py
```

## Access Points

Once running, you can access:

- **API Endpoint**: http://127.0.0.1:5102/v1/chat/completions
- **WebSocket**: ws://127.0.0.1:5102/ws
- **Dashboard Login**: http://127.0.0.1:5102/ (or /login)
- **Dashboard Home**: http://127.0.0.1:5102/dashboard
- **Token Management**: http://127.0.0.1:5102/tokens
- **Analytics**: http://127.0.0.1:5102/analytics
- **API Documentation**: http://127.0.0.1:5102/docs

## Benefits

1. **Single Process**: Only one server process to manage
2. **Single Port**: Everything runs on port 5102
3. **Simplified Deployment**: Easier to deploy and monitor
4. **Unified Logging**: All logs in one place
5. **Resource Efficient**: Lower memory and CPU usage

## Migration Notes

### Before (Two Servers)
```bash
# Terminal 1
python3 api_server.py      # Port 5102

# Terminal 2  
python3 dashboard_server.py # Port 5105
```

### After (One Server)
```bash
# Single terminal
python3 merged_server.py    # Port 5102 (includes both)
```

### Configuration Changes Needed

If you were accessing the dashboard at port 5105, update any bookmarks or scripts to use port 5102:
- Old: `http://127.0.0.1:5105/dashboard`
- New: `http://127.0.0.1:5102/dashboard`

## Environment Variables

The merged server supports the same environment variables:

- `ADMIN_USERNAME`: Initial admin username
- `ADMIN_EMAIL`: Initial admin email
- `ADMIN_PASSWORD`: Initial admin password

## Troubleshooting

If you encounter issues:

1. **Port already in use**: Make sure the old api_server.py and dashboard_server.py are not running
   ```bash
   pkill -f api_server.py
   pkill -f dashboard_server.py
   ```

2. **Check logs**: The merged server includes all logging from both original servers

3. **Verify syntax**: Run a syntax check
   ```bash
   python3 -m py_compile merged_server.py
   ```

## Original Files

The original `api_server.py` and `dashboard_server.py` files are still available if you need to reference them or revert to the two-server setup.
