# LMArena Bridge - Render.com Deployment Guide

This guide explains how to deploy LMArena Bridge on Render.com using the unified entry point architecture.

## Overview

The deployment uses a **reverse proxy architecture** to solve Render.com's single-port limitation:

- **Main Server** (`main.py`) - Acts as a reverse proxy on port 10000 (Render's default)
- **API Server** (`api_server.py`) - Runs internally on port 5102
- **Dashboard Server** (`dashboard_server.py`) - Runs internally on port 5105

All traffic goes through the main server, which routes requests to the appropriate backend.

## Architecture

```
Internet → Render.com (Port 10000) → main.py (Reverse Proxy)
                                          ├─→ /ws, /v1/*, /internal/* → api_server.py (5102)
                                          └─→ /api/*, /static/*, /* → dashboard_server.py (5105)
```

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository contains:
- `main.py` - The unified entry point
- `api_server.py` - API server
- `dashboard_server.py` - Dashboard server
- `requirements.txt` - Python dependencies (including `websockets`)
- `render.yaml` - Render configuration (optional but recommended)
- All other project files (modules, frontend, config files, etc.)

### 2. Deploy on Render.com

#### Option A: Using render.yaml (Recommended)

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **"New"** → **"Blueprint"**
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and configure the service
6. Click **"Apply"** to deploy

#### Option B: Manual Configuration

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **"New"** → **"Web Service"**
4. Connect your GitHub repository
5. Configure the service:
   - **Name**: `lmarena-bridge`
   - **Environment**: `Python`
   - **Region**: Choose your preferred region
   - **Branch**: `main` (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free (or paid plan for better performance)

6. Add Environment Variables:
   - `PORT`: `10000` (Render will override this automatically)
   - `API_SERVER_URL`: `http://127.0.0.1:5102`
   - `DASHBOARD_SERVER_URL`: `http://127.0.0.1:5105`
   - `PYTHON_VERSION`: `3.11.0`

7. Set Health Check Path: `/health`

8. Click **"Create Web Service"**

### 3. Configure Environment Variables (Important!)

After deployment, you'll need to add your application-specific environment variables:

1. Go to your service in Render Dashboard
2. Click **"Environment"** in the left sidebar
3. Add the following variables:

#### Required Variables:
- Your LMArena configuration from `config.jsonc`
- Dashboard admin credentials (if using):
  - `ADMIN_USERNAME`
  - `ADMIN_EMAIL`
  - `ADMIN_PASSWORD`

#### Optional Variables:
- Any API keys or secrets your application needs

### 4. Access Your Deployment

Once deployed, your service will be available at:
```
https://your-service-name.onrender.com
```

#### Endpoints:
- **Dashboard**: `https://your-service-name.onrender.com/`
- **API**: `https://your-service-name.onrender.com/v1/chat/completions`
- **WebSocket**: `wss://your-service-name.onrender.com/ws`
- **Health Check**: `https://your-service-name.onrender.com/health`

## Testing the Deployment

### 1. Check Health Status
```bash
curl https://your-service-name.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "api_server": "online",
  "dashboard_server": "online",
  "port": 10000
}
```

### 2. Test the Dashboard
Open `https://your-service-name.onrender.com/` in your browser.

### 3. Test the API
```bash
curl https://your-service-name.onrender.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 4. Update Your Browser Script
Update the WebSocket URL in your browser script (Tampermonkey) to:
```javascript
const WS_URL = 'wss://your-service-name.onrender.com/ws';
```

## Troubleshooting

### Service Won't Start

**Check the logs:**
1. Go to Render Dashboard → Your Service → Logs
2. Look for startup errors

**Common issues:**
- Missing dependencies in `requirements.txt`
- Port configuration errors
- Database file permissions

### Backend Servers Not Starting

The main server starts both backend servers as subprocesses. Check logs for:
```
[API] ...
[DASHBOARD] ...
```

If you don't see these, the subprocesses failed to start.

### WebSocket Connection Fails

1. Ensure your Tampermonkey script uses `wss://` (not `ws://`)
2. Check that the `/ws` path is accessible
3. Verify the WebSocket proxy in `main.py` is working

### 503 Backend Unavailable

This means the reverse proxy can't reach the backend servers:
1. Check if both servers are running in the logs
2. Verify the internal URLs (`http://127.0.0.1:5102` and `http://127.0.0.1:5105`)
3. Ensure sufficient startup time (3 seconds by default)

## Performance Considerations

### Free Tier Limitations

Render's free tier has limitations:
- Service spins down after 15 minutes of inactivity
- 750 hours/month limit
- Limited resources

**Mitigation:**
- Use Render's paid plans for production
- Implement proper error handling for cold starts
- Consider using the health check endpoint for keep-alive pings (within Render's TOS)

### Scaling

For better performance:
1. Upgrade to a paid plan
2. Consider using Render's Redis for session management
3. Use Render's PostgreSQL instead of SQLite for the dashboard database

## Local Testing

Before deploying, test the unified server locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the unified server
python main.py
```

Access locally at:
- Dashboard: `http://localhost:10000/`
- API: `http://localhost:10000/v1/chat/completions`
- WebSocket: `ws://localhost:10000/ws`

## Updating Your Deployment

Render automatically deploys when you push to your connected branch:

```bash
git add .
git commit -m "Update deployment"
git push origin main
```

For manual deployment:
1. Go to Render Dashboard → Your Service
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

## Security Considerations

1. **Never commit secrets** to your repository
2. Use Render's environment variables for sensitive data
3. Enable HTTPS only (Render provides this automatically)
4. Keep your dependencies updated
5. Use strong passwords for the dashboard admin account

## Support

For issues specific to:
- **Render.com**: Check [Render Documentation](https://render.com/docs)
- **LMArena Bridge**: Check the main README.md or open an issue on GitHub

## Migration from Separate Servers

If you were running `api_server.py` and `dashboard_server.py` separately:

1. **No code changes needed** - They continue to work as-is
2. `main.py` starts them automatically
3. All routing is handled transparently
4. Update your client applications to use the new unified URL

## Cost Estimation

**Free Tier:**
- 750 hours/month (enough for 24/7 if you have only one service)
- Spins down after inactivity
- $0/month

**Paid Plans:**
- Starter: $7/month (no spin down, better resources)
- Standard: $25/month (more resources, better performance)
- Pro: $85/month (dedicated resources)

Choose based on your traffic and uptime requirements.
