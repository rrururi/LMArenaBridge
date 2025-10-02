# 🚀 Quick Start Guide - LMArena Bridge Dashboard

Get your dashboard up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install fastapi uvicorn pydantic[email]
```

## Step 2: Start the Dashboard Server

```bash
python dashboard_server.py
```

You should see:
```
🚀 LMArena Bridge Dashboard Server starting...
   - Dashboard URL: http://127.0.0.1:5105
   - API docs: http://127.0.0.1:5105/docs
```

## Step 3: Create Your First Admin User

Open a new terminal and run:

```bash
curl -X POST http://127.0.0.1:5105/api/admin/init \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "changeme123"
  }'
```

**Response:**
```json
{
  "message": "Admin user created successfully",
  "user_id": 1
}
```

## Step 4: Login to Dashboard

1. Open your browser to: **http://127.0.0.1:5105**
2. Login with:
   - Username: `admin`
   - Password: `changeme123`

## Step 5: Create Your First API Token

1. Navigate to the **Tokens** page
2. Click **"Create New Token"**
3. Enter a name (e.g., "My First Token")
4. (Optional) Set expiration days
5. Click **"Create"**
6. **Copy the token immediately** - it won't be shown again!

Your token will look like:
```
sk-lmarena-Abc123XyZ...
```

## Step 6: Test Your Token

Use your new token with the main LMArena Bridge API:

```bash
curl http://127.0.0.1:5102/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-lmarena-YOUR_TOKEN_HERE" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 🎉 You're All Set!

Your dashboard is now ready to:
- ✅ Manage multiple API tokens
- ✅ Track usage statistics
- ✅ Monitor requests in real-time
- ✅ View analytics and charts

## Next Steps

### Add More Users

Other users can register directly through the web interface at http://127.0.0.1:5105

### View Analytics

Navigate to the **Analytics** page to see:
- Request trends over time
- Most used models
- Response time metrics
- Usage by token

### Make it Public

See `DASHBOARD_README.md` for instructions on exposing your dashboard to the internet securely.

## Common Issues

### Port Already in Use

If port 5105 is busy, edit `dashboard_server.py` and change:
```python
uvicorn.run(app, host="0.0.0.0", port=5105)  # Change 5105 to another port
```

### Can't Create Admin

If you get "Admin user already exists", you can login with your existing credentials or create a regular user through the registration form.

### Database Locked

If you see database errors, make sure only one instance of the dashboard is running.

## File Locations

- **Database**: `dashboard.db` (created automatically)
- **Frontend**: `frontend/` directory
- **Server**: `dashboard_server.py`
- **Database logic**: `modules/dashboard_db.py`

## Quick Commands

```bash
# Start dashboard
python dashboard_server.py

# View database
sqlite3 dashboard.db "SELECT * FROM users;"
sqlite3 dashboard.db "SELECT * FROM api_tokens;"

# Check logs
# (Logs appear in the terminal where you ran dashboard_server.py)
```

## Need Help?

- Full documentation: `DASHBOARD_README.md`
- API docs: http://127.0.0.1:5105/docs (when server is running)
- GitHub Issues: Report problems on the repository

---

**Security Reminder:** Change the default admin password immediately after first login!
