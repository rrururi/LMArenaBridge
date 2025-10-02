# LMArena Bridge Dashboard

A modern web dashboard for managing API tokens and tracking usage of your LMArena Bridge proxy.

## ✨ Features

- 🔐 **User Authentication** - Secure login and registration system
- 🔑 **Token Management** - Create, view, and revoke API tokens
- 📊 **Usage Analytics** - Track requests, response times, and model usage
- 📈 **Visual Charts** - Real-time charts showing usage trends
- 🎨 **Modern UI** - Clean, responsive interface built with Tailwind CSS
- 🔄 **Real-time Updates** - Dashboard auto-refreshes every 30 seconds

## 🚀 Quick Start

### 1. Install Dependencies

The dashboard uses SQLite (no additional database setup needed). Install Python dependencies:

```bash
pip install fastapi uvicorn pydantic[email]
```

### 2. Start the Dashboard Server

```bash
python dashboard_server.py
```

The dashboard will be available at: **http://127.0.0.1:5105**

### 3. Create First Admin User

On first run, create an admin account using the API:

```bash
curl -X POST http://127.0.0.1:5105/api/admin/init \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "your_secure_password"
  }'
```

Or use the registration form in the web interface (first user will need API endpoint).

### 4. Login

Open http://127.0.0.1:5105 in your browser and login with your credentials.

## 📱 Dashboard Pages

### Login Page (`/`)
- Secure authentication
- User registration
- Remember me functionality

### Dashboard (`/dashboard`)
- Overview statistics (total requests, active tokens, avg response time)
- Request trends chart (last 7 days)
- Top models usage chart
- Recent activity log
- Quick action links

### Tokens Page (`/tokens`)
- List all your API tokens
- Create new tokens with custom names
- Set expiration dates (optional)
- Copy token to clipboard
- Revoke tokens

### Analytics Page (`/analytics`)
- Detailed usage statistics
- Filter by date range
- Export data as CSV/JSON
- Per-token breakdown
- Model usage distribution

## 🔧 Configuration

The dashboard is configured in `modules/dashboard_db.py`:

```python
DATABASE_PATH = "dashboard.db"  # SQLite database file
```

Session settings in `dashboard_server.py`:
- Session expiry: 7 days
- Cookie: httponly, samesite=lax

## 🔐 Security Features

1. **Password Hashing** - SHA-256 with salt
2. **Session Tokens** - Secure, random 48-byte tokens
3. **HTTP-only Cookies** - Prevent XSS attacks
4. **API Key Generation** - Cryptographically secure tokens
5. **Token Validation** - Automatic expiration checking

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login and get session
- `POST /api/auth/logout` - End session
- `GET /api/auth/me` - Get current user info

### Token Management
- `GET /api/tokens` - List all tokens
- `POST /api/tokens` - Create new token
- `DELETE /api/tokens/{id}` - Revoke token

### Usage Statistics
- `GET /api/usage/summary?days=30` - Get usage summary
- `GET /api/usage/logs?limit=100` - Get recent logs

### System Status
- `GET /api/status` - Check system health

### Admin
- `POST /api/admin/init` - Create first admin (one-time)

Full API documentation available at: http://127.0.0.1:5105/docs

## 🔄 Integration with Main API Server

To track usage from the main LMArena Bridge API, you need to integrate the logging functionality.

### Option 1: Modify api_server.py

Add this to your chat completion endpoint in `api_server.py`:

```python
from modules import dashboard_db as db
import time

# After successful API request
start_time = time.time()
# ... your API call ...
response_time_ms = int((time.time() - start_time) * 1000)

# Log the request (if using dashboard tokens)
if api_key:  # Your API key from request
    db.log_request(
        token_key=api_key,
        model_name=model_name,
        endpoint="/v1/chat/completions",
        response_time_ms=response_time_ms,
        status_code=200,
        tokens_used=0  # Calculate if available
    )
```

### Option 2: Use Dashboard Tokens for Main API

Configure your main `api_server.py` to validate tokens from the dashboard database instead of the simple `api_key` in `config.jsonc`:

```python
from modules import dashboard_db as db

# In your API endpoint
api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
user_id = db.validate_api_token(api_key)

if not user_id:
    raise HTTPException(status_code=401, detail="Invalid API key")
```

## 🗄️ Database Schema

The dashboard uses SQLite with these tables:

- **users** - User accounts
- **api_tokens** - Generated API keys
- **usage_logs** - Request history
- **sessions** - Active login sessions

Database location: `dashboard.db` (created automatically)

## 🎨 Customization

### Changing Colors

Edit the Tailwind CSS classes in the HTML files:
- Primary color: `purple-600`
- Success: `green-600`
- Warning: `yellow-600`
- Error: `red-600`

### Adding Features

The modular design makes it easy to extend:

1. **Add new endpoint** in `dashboard_server.py`
2. **Create UI** in `frontend/` directory
3. **Add navigation link** in the navbar

## 🐛 Troubleshooting

### Dashboard won't start
- Check if port 5105 is available
- Verify Python version (3.8+ required)
- Install missing dependencies

### Can't login
- Check if database file exists and is writable
- Verify admin user was created
- Check browser console for errors

### Tokens not working
- Ensure token is active (not expired or revoked)
- Check if token belongs to your user account
- Verify Authorization header format: `Bearer sk-lmarena-...`

### No usage data showing
- Verify usage logging is integrated in main API
- Check that requests are using dashboard tokens
- Review database for entries: `sqlite3 dashboard.db "SELECT * FROM usage_logs;"`

## 📝 Development

### File Structure
```
├── dashboard_server.py          # FastAPI dashboard server
├── modules/
│   └── dashboard_db.py          # Database operations
└── frontend/
    ├── login.html               # Login page
    ├── dashboard.html           # Main dashboard
    ├── tokens.html              # Token management
    ├── analytics.html           # Analytics page
    ├── css/                     # Custom styles
    └── js/
        ├── dashboard.js         # Dashboard logic
        ├── tokens.js            # Token management
        └── analytics.js         # Analytics charts
```

### Running in Development

```bash
# With auto-reload
uvicorn dashboard_server:app --reload --port 5105
```

### Running in Production

```bash
# With Gunicorn
gunicorn dashboard_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5105
```

## 🌐 Making it Public

See the main README for instructions on exposing the dashboard publicly using:
- Cloudflare Tunnel (recommended)
- Nginx reverse proxy
- Port forwarding
- VPN solutions

**Important:** Always use HTTPS in production!

## 📄 License

Same license as LMArena Bridge main project.

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- Security best practices maintained
- Documentation updated

## 📞 Support

For issues specific to the dashboard, please open an issue on the GitHub repository with the `dashboard` label.
