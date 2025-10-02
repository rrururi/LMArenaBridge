# modules/dashboard_db.py
"""
Database models and operations for the LMArena Bridge dashboard.
Handles users, API tokens, and usage tracking.
"""

import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

DATABASE_PATH = "dashboard.db"

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # API tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_key TEXT UNIQUE NOT NULL,
            token_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Usage logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id INTEGER NOT NULL,
            model_name TEXT,
            endpoint TEXT NOT NULL,
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time_ms INTEGER,
            status_code INTEGER,
            tokens_used INTEGER DEFAULT 0,
            error_message TEXT,
            FOREIGN KEY (token_id) REFERENCES api_tokens(id) ON DELETE CASCADE
        )
    """)
    
    # Sessions table for JWT management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, pwd_hash = hashed.split('$')
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return test_hash == pwd_hash
    except:
        return False

def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"sk-lmarena-{secrets.token_urlsafe(32)}"

def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(48)

# User operations
def create_user(username: str, email: str, password: str, is_admin: bool = False) -> Optional[int]:
    """Create a new user account."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, is_admin)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user and return user info."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and verify_password(password, user['password_hash']):
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user['id'],)
        )
        conn.commit()
        conn.close()
        
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'is_admin': bool(user['is_admin'])
        }
    
    conn.close()
    return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user information by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, is_admin, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

# Session operations
def create_session(user_id: int) -> str:
    """Create a new session for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    session_token = generate_session_token()
    expires_at = datetime.now() + timedelta(days=7)  # 7 days expiry
    
    cursor.execute(
        "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
        (user_id, session_token, expires_at)
    )
    
    conn.commit()
    conn.close()
    return session_token

def validate_session(session_token: str) -> Optional[int]:
    """Validate a session token and return user_id if valid."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id FROM sessions 
        WHERE session_token = ? 
        AND is_active = 1 
        AND expires_at > CURRENT_TIMESTAMP
    """, (session_token,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['user_id'] if result else None

def invalidate_session(session_token: str):
    """Invalidate a session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
        (session_token,)
    )
    
    conn.commit()
    conn.close()

# Token operations
def create_api_token(user_id: int, token_name: str, expires_days: Optional[int] = None) -> str:
    """Create a new API token for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    token_key = generate_api_key()
    expires_at = None
    if expires_days:
        expires_at = datetime.now() + timedelta(days=expires_days)
    
    cursor.execute(
        "INSERT INTO api_tokens (user_id, token_key, token_name, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, token_key, token_name, expires_at)
    )
    
    conn.commit()
    conn.close()
    return token_key

def get_user_tokens(user_id: int) -> List[Dict[str, Any]]:
    """Get all tokens for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, token_key, token_name, created_at, last_used_at, is_active, expires_at
        FROM api_tokens 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    
    tokens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tokens

def validate_api_token(token_key: str) -> Optional[int]:
    """Validate an API token and return user_id if valid."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, id FROM api_tokens 
        WHERE token_key = ? 
        AND is_active = 1 
        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
    """, (token_key,))
    
    result = cursor.fetchone()
    
    if result:
        # Update last_used_at
        cursor.execute(
            "UPDATE api_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?",
            (result['id'],)
        )
        conn.commit()
        conn.close()
        return result['user_id']
    
    conn.close()
    return None

def revoke_token(token_id: int, user_id: int) -> bool:
    """Revoke a token (only if it belongs to the user)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE api_tokens SET is_active = 0 WHERE id = ? AND user_id = ?",
        (token_id, user_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# Usage logging
def log_request(token_key: str, model_name: str, endpoint: str, 
                response_time_ms: int, status_code: int, 
                tokens_used: int = 0, error_message: str = None):
    """Log an API request."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get token_id from token_key
    cursor.execute("SELECT id FROM api_tokens WHERE token_key = ?", (token_key,))
    result = cursor.fetchone()
    
    if result:
        cursor.execute("""
            INSERT INTO usage_logs 
            (token_id, model_name, endpoint, response_time_ms, status_code, tokens_used, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (result['id'], model_name, endpoint, response_time_ms, status_code, tokens_used, error_message))
        
        conn.commit()
    
    conn.close()

def get_usage_stats(user_id: int, days: int = 30) -> Dict[str, Any]:
    """Get usage statistics for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    since_date = datetime.now() - timedelta(days=days)
    
    # Total requests
    cursor.execute("""
        SELECT COUNT(*) as total_requests
        FROM usage_logs ul
        JOIN api_tokens at ON ul.token_id = at.id
        WHERE at.user_id = ? AND ul.request_time > ?
    """, (user_id, since_date))
    total_requests = cursor.fetchone()['total_requests']
    
    # Requests by model
    cursor.execute("""
        SELECT model_name, COUNT(*) as count
        FROM usage_logs ul
        JOIN api_tokens at ON ul.token_id = at.id
        WHERE at.user_id = ? AND ul.request_time > ?
        GROUP BY model_name
        ORDER BY count DESC
        LIMIT 10
    """, (user_id, since_date))
    by_model = [dict(row) for row in cursor.fetchall()]
    
    # Requests by day
    cursor.execute("""
        SELECT DATE(request_time) as date, COUNT(*) as count
        FROM usage_logs ul
        JOIN api_tokens at ON ul.token_id = at.id
        WHERE at.user_id = ? AND ul.request_time > ?
        GROUP BY DATE(request_time)
        ORDER BY date DESC
    """, (user_id, since_date))
    by_day = [dict(row) for row in cursor.fetchall()]
    
    # Average response time
    cursor.execute("""
        SELECT AVG(response_time_ms) as avg_response_time
        FROM usage_logs ul
        JOIN api_tokens at ON ul.token_id = at.id
        WHERE at.user_id = ? AND ul.request_time > ?
    """, (user_id, since_date))
    avg_response_time = cursor.fetchone()['avg_response_time'] or 0
    
    conn.close()
    
    return {
        'total_requests': total_requests,
        'by_model': by_model,
        'by_day': by_day,
        'avg_response_time_ms': round(avg_response_time, 2)
    }

# Initialize database on module import
init_database()
