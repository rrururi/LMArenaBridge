#!/usr/bin/env python3
"""
LMArena Bridge - Unified Entry Point
This server acts as a reverse proxy to route requests to the appropriate backend service.
Designed for deployment on platforms like Render.com that expose only one port.
"""

import asyncio
import logging
import os
import sys
import signal
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_SERVER_URL = os.getenv("API_SERVER_URL", "http://127.0.0.1:5102")
DASHBOARD_SERVER_URL = os.getenv("DASHBOARD_SERVER_URL", "http://127.0.0.1:5105")
MAIN_PORT = int(os.getenv("PORT", 10000))  # Render.com typically uses port 10000

# Store subprocess handles
api_server_process = None
dashboard_server_process = None

async def start_backend_servers():
    """Start the API and Dashboard servers as background processes."""
    global api_server_process, dashboard_server_process
    
    logger.info("Starting backend servers...")
    
    # Start API server
    api_server_process = await asyncio.create_subprocess_exec(
        sys.executable, "api_server.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    logger.info("✅ API Server process started")
    
    # Start Dashboard server
    dashboard_server_process = await asyncio.create_subprocess_exec(
        sys.executable, "dashboard_server.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    logger.info("✅ Dashboard Server process started")
    
    # Wait a moment for servers to initialize
    await asyncio.sleep(3)
    
    # Log output from subprocesses in background
    asyncio.create_task(log_subprocess_output(api_server_process, "API"))
    asyncio.create_task(log_subprocess_output(dashboard_server_process, "DASHBOARD"))

async def log_subprocess_output(process, name):
    """Log output from subprocess."""
    while True:
        try:
            line = await process.stdout.readline()
            if line:
                logger.info(f"[{name}] {line.decode().strip()}")
            else:
                break
        except Exception as e:
            logger.error(f"Error reading {name} output: {e}")
            break

async def stop_backend_servers():
    """Stop the backend servers gracefully."""
    logger.info("Stopping backend servers...")
    
    if api_server_process:
        try:
            if api_server_process.returncode is None:
                api_server_process.terminate()
                await asyncio.wait_for(api_server_process.wait(), timeout=5.0)
                logger.info("✅ API Server stopped")
        except asyncio.TimeoutError:
            try:
                api_server_process.kill()
                logger.warning("⚠️ API Server force killed")
            except ProcessLookupError:
                logger.info("API Server already terminated")
        except ProcessLookupError:
            logger.info("API Server already terminated")
    
    if dashboard_server_process:
        try:
            if dashboard_server_process.returncode is None:
                dashboard_server_process.terminate()
                await asyncio.wait_for(dashboard_server_process.wait(), timeout=5.0)
                logger.info("✅ Dashboard Server stopped")
        except asyncio.TimeoutError:
            try:
                dashboard_server_process.kill()
                logger.warning("⚠️ Dashboard Server force killed")
            except ProcessLookupError:
                logger.info("Dashboard Server already terminated")
        except ProcessLookupError:
            logger.info("Dashboard Server already terminated")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the application."""
    # Startup
    await start_backend_servers()
    logger.info("🚀 Unified server ready to accept connections")
    
    yield
    
    # Shutdown
    await stop_backend_servers()
    logger.info("👋 Unified server shutdown complete")

# Create the main FastAPI app
app = FastAPI(
    title="LMArena Bridge - Unified Entry Point",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create HTTP client for proxying
client = httpx.AsyncClient(timeout=360.0)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_request(request: Request, path: str):
    """
    Proxy all requests to the appropriate backend service based on path.
    
    Routing rules:
    - /ws -> API Server (WebSocket for browser script)
    - /v1/* -> API Server (OpenAI-compatible API)
    - /internal/* -> API Server (Internal endpoints)
    - /api/* -> Dashboard Server (Dashboard API)
    - /static/* -> Dashboard Server (Static files)
    - /* -> Dashboard Server (Frontend pages)
    """
    
    # Determine target server based on path
    if path.startswith("ws") or path.startswith("v1/") or path.startswith("internal/"):
        target_url = API_SERVER_URL
        backend_name = "API"
    else:
        target_url = DASHBOARD_SERVER_URL
        backend_name = "DASHBOARD"
    
    # Build the full URL
    url = f"{target_url}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    # Get request body
    body = await request.body()
    
    # Prepare headers (exclude host header to avoid conflicts)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Handle WebSocket upgrade requests specially
    if request.headers.get("upgrade", "").lower() == "websocket":
        from fastapi import WebSocket
        from fastapi.websockets import WebSocketDisconnect
        import websockets
        
        websocket = WebSocket(request.scope, receive=request.receive, send=request._send)
        await websocket.accept()
        
        # Connect to backend WebSocket
        ws_url = f"ws://127.0.0.1:5102/ws"
        
        try:
            async with websockets.connect(ws_url) as backend_ws:
                # Create bidirectional proxy
                async def forward_to_backend():
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await backend_ws.send(data)
                    except WebSocketDisconnect:
                        logger.info("Client WebSocket disconnected")
                    except Exception as e:
                        logger.error(f"Error forwarding to backend: {e}")
                
                async def forward_to_client():
                    try:
                        while True:
                            data = await backend_ws.recv()
                            await websocket.send_text(data)
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("Backend WebSocket disconnected")
                    except Exception as e:
                        logger.error(f"Error forwarding to client: {e}")
                
                # Run both forwarding tasks concurrently
                await asyncio.gather(
                    forward_to_backend(),
                    forward_to_client(),
                    return_exceptions=True
                )
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
        finally:
            await websocket.close()
        
        return
    
    # For regular HTTP requests
    try:
        # Make request to backend
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        
        # Handle streaming responses
        if response.headers.get("content-type", "").startswith("text/event-stream"):
            async def stream_response():
                async for chunk in response.aiter_bytes():
                    yield chunk
            
            return StreamingResponse(
                stream_response(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        
        # Return regular response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to {backend_name} server: {e}")
        return Response(
            content=f"Backend server ({backend_name}) unavailable",
            status_code=503
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for Render.com and other platforms."""
    try:
        # Check if both backend servers are responding
        api_health = await client.get(f"{API_SERVER_URL}/v1/models", timeout=5.0)
        dashboard_health = await client.get(f"{DASHBOARD_SERVER_URL}/api/status", timeout=5.0)
        
        return {
            "status": "healthy",
            "api_server": "online" if api_health.status_code == 200 else "degraded",
            "dashboard_server": "online" if dashboard_health.status_code == 200 else "degraded",
            "port": MAIN_PORT
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            content=f"Health check failed: {str(e)}",
            status_code=503
        )

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("="*60)
    logger.info("🚀 LMArena Bridge - Unified Entry Point Starting...")
    logger.info("="*60)
    logger.info(f"   Main Port: {MAIN_PORT}")
    logger.info(f"   API Server: {API_SERVER_URL}")
    logger.info(f"   Dashboard Server: {DASHBOARD_SERVER_URL}")
    logger.info("="*60)
    logger.info("")
    logger.info("   Routing:")
    logger.info("   - /ws → API Server (WebSocket)")
    logger.info("   - /v1/* → API Server (OpenAI API)")
    logger.info("   - /internal/* → API Server")
    logger.info("   - /api/* → Dashboard Server")
    logger.info("   - /static/* → Dashboard Server")
    logger.info("   - /* → Dashboard Server (Frontend)")
    logger.info("="*60)
    
    uvicorn.run(app, host="0.0.0.0", port=MAIN_PORT)
