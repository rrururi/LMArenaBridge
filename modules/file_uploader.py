# modules/file_uploader.py
import httpx
import logging

logger = logging.getLogger(__name__)

from typing import Tuple

async def upload_to_file_bed(file_name: str, file_data: str, upload_url: str, api_key: str | None = None) -> Tuple[str | None, str | None]:
    """
    Upload a base64 encoded file to the file hosting server.

    :param file_name: Original filename.
    :param file_data: Base64 data URI (e.g., "data:image/png;base64,...").
    :param upload_url: The file hosting server's /upload endpoint URL.
    :param api_key: (Optional) API Key for authentication.
    :return: A tuple (filename, error_message). On success, filename is a string and error_message is None;
             On failure, filename is None and error_message contains the error details.
    """
    payload = {
        "file_name": file_name,
        "file_data": file_data,
        "api_key": api_key
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(upload_url, json=payload)
            
            response.raise_for_status()  # Raises exception if status code is 4xx or 5xx
            
            result = response.json()
            if result.get("success") and result.get("filename"):
                logger.info(f"File '{file_name}' successfully uploaded to file hosting server, saved as: {result['filename']}")
                return result["filename"], None
            else:
                error_msg = result.get("error", "File hosting server returned an unknown error.")
                logger.error(f"Upload to file hosting server failed: {error_msg}")
                return None, error_msg
                
    except httpx.HTTPStatusError as e:
        error_details = f"HTTP error: {e.response.status_code} - {e.response.text}"
        logger.error(f"HTTP error occurred while uploading to file hosting server: {error_details}")
        return None, error_details
    except httpx.RequestError as e:
        error_details = f"Connection error: {e}"
        logger.error(f"Error connecting to file hosting server: {e}")
        return None, error_details
    except Exception as e:
        error_details = f"Unknown error: {e}"
        logger.error(f"Unknown error occurred while uploading file: {e}", exc_info=True)
        return None, error_details
