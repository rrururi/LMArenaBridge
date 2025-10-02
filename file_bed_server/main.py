# file_bed_server/main.py
import base64
import os
import uuid
import time
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
from apscheduler.schedulers.background import BackgroundScheduler

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Path Configuration ---
# Set upload directory to same level as main.py file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
API_KEY = "your_secret_api_key"  # Simple authentication key
CLEANUP_INTERVAL_MINUTES = 1 # Cleanup task run frequency (minutes)
FILE_MAX_AGE_MINUTES = 10 # Maximum file retention time (minutes)

# --- Cleanup Function ---
def cleanup_old_files():
    """Traverse upload directory and delete files older than specified time."""
    now = time.time()
    cutoff = now - (FILE_MAX_AGE_MINUTES * 60)
    
    logger.info(f"Running cleanup task, deleting files older than {datetime.fromtimestamp(cutoff).strftime('%Y-%m-%d %H:%M:%S')}...")
    
    deleted_count = 0
    try:
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff:
                        os.remove(file_path)
                        logger.info(f"Deleted expired file: {filename}")
                        deleted_count += 1
                except OSError as e:
                    logger.error(f"Error deleting file '{file_path}': {e}")
    except Exception as e:
        logger.error(f"Unknown error occurred while cleaning up old files: {e}", exc_info=True)

    if deleted_count > 0:
        logger.info(f"Cleanup task completed, deleted {deleted_count} file(s).")
    else:
        logger.info("Cleanup task completed, no files needed deletion.")


# --- FastAPI Lifecycle Events ---
scheduler = BackgroundScheduler(timezone="UTC")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks when server starts, stop when shutting down."""
    # Start scheduler and add tasks
    scheduler.add_job(cleanup_old_files, 'interval', minutes=CLEANUP_INTERVAL_MINUTES)
    scheduler.start()
    logger.info(f"Background file cleanup task started, running every {CLEANUP_INTERVAL_MINUTES} minute(s).")
    yield
    # Shutdown scheduler
    scheduler.shutdown()
    logger.info("Background file cleanup task stopped.")


app = FastAPI(lifespan=lifespan)

# --- Ensure Upload Directory Exists ---
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    logger.info(f"Upload directory '{UPLOAD_DIR}' created.")

# --- Mount Static Files Directory for File Access ---
app.mount(f"/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- Pydantic Model Definition ---
class UploadRequest(BaseModel):
    file_name: str
    file_data: str # Receive complete base64 data URI
    api_key: str | None = None

# --- API Endpoints ---
@app.post("/upload")
async def upload_file(request: UploadRequest, http_request: Request):
    """
    Receive base64 encoded file and save it, return accessible URL.
    """
    # Simple API Key authentication
    if API_KEY and request.api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        # 1. Parse base64 data URI
        header, encoded_data = request.file_data.split(',', 1)
        
        # 2. Decode base64 data
        file_data = base64.b64decode(encoded_data)
        
        # 3. Generate unique filename to avoid conflicts
        file_extension = os.path.splitext(request.file_name)[1]
        if not file_extension:
            # Try to guess extension from mime type in header
            import mimetypes
            mime_type = header.split(';')[0].split(':')[1]
            guessed_extension = mimetypes.guess_extension(mime_type)
            file_extension = guessed_extension if guessed_extension else '.bin'

        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # 4. Save file
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        # 5. Return success message and unique filename
        logger.info(f"File '{request.file_name}' successfully saved as '{unique_filename}'.")
        
        return JSONResponse(
            status_code=200,
            content={"success": True, "filename": unique_filename}
        )

    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing base64 data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid base64 data URI format: {e}")
    except Exception as e:
        logger.error(f"Unknown error occurred while processing file upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/")
def read_root():
    return {"message": "LMArena Bridge file hosting server is running."}

# --- Main Program Entry Point ---
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 File hosting server starting...")
    logger.info("   - Listening on: http://127.0.0.1:5180")
    logger.info(f"   - Upload endpoint: http://127.0.0.1:5180/upload")
    logger.info(f"   - File access path: /uploads")
    uvicorn.run(app, host="0.0.0.0", port=5180)
