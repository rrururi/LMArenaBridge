#!/usr/bin/env python3
"""
LMArena Bridge Dashboard Server
Provides web interface for token management and usage tracking.
"""

from fastapi import FastAPI, HTTPException, Depends, Cookie, Response, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uvicorn
import logging
import os
from datetime import datetime

from modules import dashboard_db as db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="LMArena Bridge Dashboard", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenCreate(BaseModel):
    token_name: str
    expires_days: Optional[int] = None

class TokenResponse(BaseModel):
    id: int
    token_key: str
    token_name: str
    created_at: str
    last_used_at: Optional[str]
    is_active: bool
    expires_at: Optional[str]

# Dependency to get current user from session cookie
async def get_current_user(session_token: Optional[str] = Cookie(None)) -> int:
    """Validate session and return user_id."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = db.validate_session(session_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return user_id

# Authentication endpoints
@app.post("/api/auth/register")
async def register(user: UserCreate):
    """Register a new user account."""
    user_id = db.create_user(user.username, user.email, user.password)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    logger.info(f"New user registered: {user.username}")
    return {"message": "User created successfully", "user_id": user_id}

@app.post("/api/auth/login")
async def login(user: UserLogin, response: Response):
    """Login and create a session."""
    user_data = db.authenticate_user(user.username, user.password)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create session
    session_token = db.create_session(user_data['id'])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 days
        samesite="lax"
    )
    
    logger.info(f"User logged in: {user.username}")
    return {
        "message": "Login successful",
        "user": {
            "id": user_data['id'],
            "username": user_data['username'],
            "email": user_data['email'],
            "is_admin": user_data['is_admin']
        }
    }

@app.post("/api/auth/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(None)
):
    """Logout and invalidate session."""
    if session_token:
        db.invalidate_session(session_token)
    
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_current_user_info(user_id: int = Depends(get_current_user)):
    """Get current user information."""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Token management endpoints
@app.get("/api/tokens")
async def list_tokens(user_id: int = Depends(get_current_user)):
    """Get all API tokens for the current user."""
    tokens = db.get_user_tokens(user_id)
    return {"tokens": tokens}

@app.post("/api/tokens")
async def create_token(
    token_data: TokenCreate,
    user_id: int = Depends(get_current_user)
):
    """Create a new API token."""
    token_key = db.create_api_token(
        user_id,
        token_data.token_name,
        token_data.expires_days
    )
    
    logger.info(f"New API token created for user {user_id}: {token_data.token_name}")
    return {
        "message": "Token created successfully",
        "token_key": token_key,
        "token_name": token_data.token_name
    }

@app.delete("/api/tokens/{token_id}")
async def revoke_token_endpoint(
    token_id: int,
    user_id: int = Depends(get_current_user)
):
    """Revoke an API token."""
    success = db.revoke_token(token_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Token not found or doesn't belong to you")
    
    logger.info(f"Token {token_id} revoked by user {user_id}")
    return {"message": "Token revoked successfully"}

# Usage statistics endpoints
@app.get("/api/usage/summary")
async def get_usage_summary(
    days: int = 30,
    user_id: int = Depends(get_current_user)
):
    """Get usage statistics summary."""
    stats = db.get_usage_stats(user_id, days)
    return stats

@app.get("/api/usage/logs")
async def get_usage_logs(
    limit: int = 100,
    user_id: int = Depends(get_current_user)
):
    """Get recent usage logs."""
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ul.model_name,
            ul.endpoint,
            ul.request_time,
            ul.response_time_ms,
            ul.status_code,
            ul.tokens_used,
            at.token_name
        FROM usage_logs ul
        JOIN api_tokens at ON ul.token_id = at.id
        WHERE at.user_id = ?
        ORDER BY ul.request_time DESC
        LIMIT ?
    """, (user_id, limit))
    
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"logs": logs}

# System status endpoints
@app.get("/api/status")
async def get_system_status():
    """Get system status information."""
    # Check if main API server is running (simplified check)
    return {
        "dashboard_server": "online",
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }

# Serve frontend pages
@app.get("/", response_class=HTMLResponse)
async def serve_login_page():
    """Serve the login page."""
    try:
        with open("frontend/login.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Frontend not found. Please build the frontend first.</h1>")

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard_page(user_id: int = Depends(get_current_user)):
    """Serve the dashboard page (requires authentication)."""
    try:
        with open("frontend/dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard page not found.</h1>")

@app.get("/tokens", response_class=HTMLResponse)
async def serve_tokens_page(user_id: int = Depends(get_current_user)):
    """Serve the tokens management page."""
    try:
        with open("frontend/tokens.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Tokens page not found.</h1>")

@app.get("/analytics", response_class=HTMLResponse)
async def serve_analytics_page(user_id: int = Depends(get_current_user)):
    """Serve the analytics page."""
    try:
        with open("frontend/analytics.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Analytics page not found.</h1>")

# Utility endpoint to create first admin user
@app.post("/api/admin/init")
async def create_first_admin(user: UserCreate):
    """Create the first admin user (only works if no users exist)."""
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    conn.close()
    
    if user_count > 0:
        raise HTTPException(status_code=400, detail="Admin user already exists")
    
    user_id = db.create_user(user.username, user.email, user.password, is_admin=True)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Failed to create admin user")
    
    logger.info(f"First admin user created: {user.username}")
    return {"message": "Admin user created successfully", "user_id": user_id}

def create_admin_from_env():
    """
    Create admin user from environment variables if they exist.
    Useful for initial setup in containerized/cloud environments.
    
    Environment variables:
    - ADMIN_USERNAME
    - ADMIN_EMAIL
    - ADMIN_PASSWORD
    """
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not all([admin_username, admin_email, admin_password]):
        logger.info("Admin credentials not provided in environment variables")
        return
    
    # Check if any users exist
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    conn.close()
    
    if user_count > 0:
        logger.info("Users already exist, skipping admin creation from environment")
        return
    
    # Create admin user
    user_id = db.create_user(admin_username, admin_email, admin_password, is_admin=True)
    
    if user_id:
        logger.info(f"✅ Admin user created from environment variables: {admin_username}")
    else:
        logger.error("❌ Failed to create admin user from environment variables")

if __name__ == "__main__":
    logger.info("🚀 LMArena Bridge Dashboard Server starting...")
    logger.info("   - Dashboard URL: http://127.0.0.1:5105")
    logger.info("   - API docs: http://127.0.0.1:5105/docs")
    
    # Try to create admin user from environment variables
    create_admin_from_env()
    
    uvicorn.run(app, host="0.0.0.0", port=5105)
