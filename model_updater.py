# model_updater.py
import requests
import time
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
API_SERVER_URL = "http://127.0.0.1:5102" # Match the port in api_server.py

def trigger_model_update():
    """
    Notify the main server to start the model list update process.
    """
    try:
        logging.info("Sending model list update request to main server...")
        response = requests.post(f"{API_SERVER_URL}/internal/request_model_update")
        response.raise_for_status()
        
        if response.json().get("status") == "success":
            logging.info("✅ Successfully requested server to update model list.")
            logging.info("Please ensure LMArena page is open, the script will automatically extract the latest model list from the page.")
            logging.info("The server will save the results in the `available_models.json` file.")
        else:
            logging.error(f"❌ Server returned an error: {response.json().get('message')}")

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Unable to connect to main server ({API_SERVER_URL}).")
        logging.error("Please ensure `api_server.py` is running.")
    except Exception as e:
        logging.error(f"Unknown error occurred: {e}")

if __name__ == "__main__":
    trigger_model_update()
    # Script will automatically exit after completion
    time.sleep(2)
