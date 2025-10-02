# 🚀 LMArena Bridge - AI Model Arena API Proxy 🌉

Welcome to the next generation of LMArena Bridge! 🎉 This is a high-performance toolkit based on FastAPI and WebSocket that allows you to seamlessly access the vast array of large language models provided on the [LMArena.ai](https://lmarena.ai/) platform through any OpenAI API-compatible client or application.

This refactored version aims to provide a more stable, maintainable, and extensible experience.

## 📖 Table of Contents

- [Key Features](#-key-features)
- [Quick Start](#-installation-and-usage)
- [Configuration Guide](#️-configuration-file-description)
- [File Hosting Server](#-new-file-hosting-server)
- [How It Works](#-how-does-it-work)
- [Additional Documentation](#-additional-documentation)
- [Environment Variables](#-environment-variables-for-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## 📚 Additional Documentation

- **[Dashboard Guide](DASHBOARD_README.md)** - Complete guide for the web dashboard
- **[Dashboard Token System](DASHBOARD_TOKEN_INTEGRATION.md)** - Token management and authentication
- **[Quick Start Dashboard](QUICK_START_DASHBOARD.md)** - Get started with the dashboard quickly
- **[Cloud Deployment](#-advanced-cloud-deployment-topics)** - Deploy on cloud servers with local workers as the executor
- **[Worker Configuration](worker_config.jsonc)** - Configure cloud workers

## ✨ Key Features

*   **🚀 High-Performance Backend**: Built on **FastAPI** and **Uvicorn**, providing asynchronous, high-performance API services.
*   **🔌 Stable WebSocket Communication**: Uses WebSocket instead of Server-Sent Events (SSE) for more reliable, low-latency bidirectional communication.
*   **🤖 OpenAI-Compatible Interface**: Fully compatible with OpenAI `v1/chat/completions`, `v1/models`, and `v1/images/generations` endpoints.
*   **📋 Manual Model List Updates**: New `model_updater.py` script can manually trigger extraction of the latest available model list from LMArena pages, saving it as `available_models.json` for easy reference and updating the core `models.json`.
*   **📎 Universal File Upload**: Supports uploading any type of file (images, audio, PDF, code, etc.) via Base64, with support for multiple file uploads at once.
*   **🎨 Native Streaming Text-to-Image**: Text-to-image functionality is now fully unified with text generation. Simply request an image model in the `/v1/chat/completions` endpoint to receive images in Markdown format via streaming, just like text.
*   **🗣️ Complete Conversation History Support**: Automatically injects conversation history into LMArena for contextual continuous dialogue.
*   **🌊 Real-time Streaming Responses**: Receive text responses from models in real-time, just like the native OpenAI API.
*   **🔄 Automatic Program Updates**: Automatically checks the GitHub repository on startup and can automatically download and update the program when a new version is found.
*   **🆔 One-Click Session ID Update**: Provides `id_updater.py` script that automatically captures and updates session IDs in `config.jsonc` with just one browser operation.
*   **⚙️ Browser Automation**: The included Tampermonkey script (`LMArenaApiBridge.js`) handles communication with the backend server and executes all necessary operations in the browser.
*   **🍻 Tavern Mode**: Designed for applications like SillyTavern, intelligently merges `system` prompts to ensure compatibility.
*   **🤫 Bypass Mode**: Attempts to bypass platform sensitive word censorship by injecting an additional empty user message into requests. When attaching images, manually add `--bypass` at the end of your prompt to construct a fake AI response and bypass arena image external review.
*   **🔐 API Key Protection**: Can set API Keys in the configuration file to add a layer of security to your service.
*   **🎯 Advanced Model-Session Mapping**: Supports configuring independent session ID pools for different models and specifying specific working modes (such as `battle` or `direct_chat`) for each session, enabling more granular request control.
*   **🖼️ Optional External File Hosting**: New standalone FastAPI file hosting server. When enabled, all attachments are first uploaded to this server and converted to direct URLs, bypassing LMArena's Base64 size and type restrictions, allowing you to upload larger files or videos.

## 📂 New: File Hosting Server

To solve LMArena's Base64 attachment size limitations (typically around 5MB) and support more file types, this project now includes a standalone file hosting server.

### How It Works

1.  When you enable `file_bed_enabled` in `config.jsonc`.
2.  `api_server.py` intercepts all `data:` URI format attachments when processing your requests.
3.  It calls the file hosting server's `/upload` API to upload the file.
4.  The file hosting server saves the file locally in the `file_bed_server/uploads/` directory and returns a publicly accessible URL (e.g., `http://127.0.0.1:5104/uploads/xxxx.png`).
5.  `api_server.py` then inserts this URL as plain text into your message content instead of sending it as an attachment.
6.  This way, even videos, large images, or archives that LMArena doesn't directly support can be sent to the model as links.

### How to Use

1.  **Install Dependencies**
    Enter the `file_bed_server` directory and install its specific dependencies:
    ```bash
    cd file_bed_server
    pip install -r requirements.txt
    cd ..
    ```

2.  **Start the File Hosting Server**
    In **a new terminal**, run the file hosting server:
    ```bash
    python file_bed_server/main.py
    ```
    The server runs on `http://127.0.0.1:5104` by default.

3.  **Modify Main Configuration**
    Open the `config.jsonc` file and make the following settings:
    *   `"file_bed_enabled": true,`  // Enable file hosting
    *   `"file_bed_upload_url": "http:\/\/127.0.0.1:5180/upload",` // Ensure the address and port are correct. Note: For maximum compatibility, it's recommended to escape `//` as `\/\/` in the URL.
    *   `"file_bed_api_key": "your_secret_api_key"` // (Optional) If you modified `API_KEY` in `file_bed_server/main.py`, synchronize it here.

4.  **Run Main Service Normally**
    Start `api_server.py` as usual. Now, when you send requests with multimedia attachments through the client, they will be automatically processed through the file hosting server.

## ⚙️ Configuration File Description

The project's main behavior is controlled through `config.jsonc`, `models.json`, and `model_endpoint_map.json`.

### `models.json` - Core Model Mapping
This file contains the mapping of LMArena platform model names to their internal IDs and supports specifying model types through a specific format.

*   **Important**: This is a **required** core file for the program to run. You need to manually maintain this list.
*   **Format**:
    *   **Standard Text Models**: `"model-name": "model-id"`
    *   **Image Generation Models**: `"model-name": "model-id:image"`
*   **Description**:
    *   The program identifies image models by checking if the model ID string contains `:image`.
    *   This format maintains maximum compatibility with old configuration files; models without a specified type will default to `"text"`.
*   **Example**:
    ```json
    {
      "gemini-1.5-pro-flash-20240514": "gemini-1.5-pro-flash-20240514",
      "dall-e-3": "null:image"
    }
    ```

### `available_models.json` - Available Models Reference (Optional)
*   This is a **reference file** generated by the new `model_updater.py` script.
*   It contains complete information (ID, name, organization, etc.) for all models extracted from LMArena pages.
*   You can run `model_updater.py` to generate or update this file, then copy the model information you want to use from it into `models.json`.

### `config.jsonc` - Global Configuration

This is the main configuration file containing the server's global settings.

*   `session_id` / `message_id`: Global default session IDs. These IDs are used when a model doesn't have a specific mapping in `model_endpoint_map.json`.
*   `id_updater_last_mode` / `id_updater_battle_target`: Global default request mode. Similarly, these settings are used when a specific session hasn't specified a mode.
*   `use_default_ids_if_mapping_not_found`: A very important switch (defaults to `true`).
    *   `true`: If a requested model is not found in `model_endpoint_map.json`, use the global default ID and mode.
    *   `false`: If no mapping is found, return an error directly. This is very useful when you need strict control over each model's session.
*   For other configuration items like `api_key`, `tavern_mode_enabled`, etc., please refer to the comments in the file.

### `model_endpoint_map.json` - Model-Specific Configuration

This is a powerful advanced feature that allows you to override global configuration and set one or more dedicated sessions for specific models.

**Core Advantages**:
1.  **Session Isolation**: Use independent sessions for different models to avoid context confusion.
2.  **Improved Concurrency**: Configure an ID pool for popular models; the program will randomly select an ID for each request, simulating round-robin to reduce the risk of frequent requests to a single session.
3.  **Mode Binding**: Bind a session ID with the mode it was captured in (`direct_chat` or `battle`), ensuring the request format is always correct.

**Configuration Example**:
```json
{
  "claude-3-opus-20240229": [
    {
      "session_id": "session_for_direct_chat_1",
      "message_id": "message_for_direct_chat_1",
      "mode": "direct_chat"
    },
    {
      "session_id": "session_for_battle_A",
      "message_id": "message_for_battle_A",
      "mode": "battle",
      "battle_target": "A"
    }
  ],
  "gemini-1.5-pro-20241022": {
      "session_id": "single_session_id_no_mode",
      "message_id": "single_message_id_no_mode"
  }
}
```
*   **Opus**: Configured with an ID pool. Requests will randomly select one and strictly send requests according to its bound `mode` and `battle_target`.
*   **Gemini**: Uses a single ID object (old format, still compatible). Since it doesn't specify a `mode`, the program will automatically use the global mode defined in `config.jsonc`.

## 🛠️ Installation and Usage

You need to have a Python environment ready and a browser that supports Tampermonkey scripts (such as Chrome, Firefox, Edge).

### 1. Preparation

*   **Install Python Dependencies**
    Open a terminal, navigate to the project root directory, and run:
    ```bash
    pip install -r requirements.txt
    ```

*   **Install Tampermonkey Extension**
    Install the [Tampermonkey](https://www.tampermonkey.net/) extension for your browser.

*   **Install This Project's Tampermonkey Script**
    1.  Open the Tampermonkey extension's management panel.
    2.  Click "Add new script" or "Create a new script".
    3.  Copy all the code from the [`TampermonkeyScript/LMArenaApiBridge.js`](TampermonkeyScript/LMArenaApiBridge.js) file and paste it into the editor.
    4.  Save the script.

### 2. Run Main Program

1.  **Start Local Server**
    In the project root directory, run the main service program:
    ```bash
    python api_server.py
    ```
    When you see a message that the server has started on `http://127.0.0.1:5102`, the server is ready.

2.  **Keep LMArena Page Open**
    Ensure you have at least one LMArena page open and the Tampermonkey script has successfully connected to the local server (the page title will start with `✅`). You don't need to stay on the conversation page; any page under the domain, including the LeaderBoard, works.

### 3. Update Available Model List (Optional but Recommended)
This step generates the `available_models.json` file, letting you know which models are currently available on LMArena, making it easier to update `models.json`.
1.  **Ensure the main server is running**.
2.  Open **a new terminal** and run the model updater:
    ```bash
    python model_updater.py
    ```
3.  The script will automatically request the browser to fetch the model list and generate the `available_models.json` file in the root directory.
4.  Open `available_models.json`, find the models you want to use, and copy their `"publicName"` and `"id"` key-value pairs into the `models.json` file (format: `"publicName": "id"`).

### 4. Configure Session ID (When Needed, Generally Only Configured Once Unless Switching Models or Original Conversation Becomes Invalid)

This is the **most important** step. You need to obtain a valid session ID and message ID so the program can correctly communicate with the LMArena API.

1.  **Ensure the main server is running**
    `api_server.py` must be running because the ID updater needs to activate the browser's capture function through it.

2.  **Run ID Updater**
    Open **a new terminal** and run the `id_updater.py` script in the project root directory:
    ```bash
    python id_updater.py
    ```
    *   The script will prompt you to select a mode (DirectChat / Battle).
    *   After selection, it will notify the running main server.

3.  **Activate and Capture**
    *   At this point, you should see a crosshair icon (🎯) appear at the very beginning of the LMArena page title in your browser, indicating **ID capture mode is activated**.
    *   In the browser, open an LMArena arena **page with a message sent to the target model**. Note: If it's a Battle page, do not view model names, keep it anonymous, and ensure the last message in the current interface is a response from the target model; if it's Direct Chat, ensure the last message in the current interface is a response from the target model.
    *   **Click the Retry button in the upper right corner of the target model's response card**.
    *   The Tampermonkey script will capture the `sessionId` and `messageId` and send them to `id_updater.py`.

4.  **Verify Results**
    *   Return to the terminal running `id_updater.py`, and you'll see it print the successfully captured IDs and indicate they've been written to the `config.jsonc` file.
    *   The script will automatically close upon success. Your configuration is now complete!

### 5. Configure Your OpenAI Client
Point your client or application's OpenAI API address to the local server:
*   **API Base URL**: `http://127.0.0.1:5102/v1`
*   **API Key**: If `api_key` in `config.jsonc` is empty, you can enter anything; if it's set, you must provide the correct Key.
*   **Model Name**: Specify the model name you want to use in your client (**must exactly match the name in `models.json`**). The server will look up the corresponding model ID based on this name.

### 6. Start Chatting! 💬
Now you can use your client normally, and all requests will be proxied to LMArena through the local server!

## 🤔 How Does It Work?

This project consists of two parts: a local Python **FastAPI** server and a **Tampermonkey script** running in the browser. They work together via **WebSocket**.

```mermaid
sequenceDiagram
    participant C as OpenAI Client 💻
    participant S as Local FastAPI Server 🐍
    participant MU as Model Update Script (model_updater.py) 📋
    participant IU as ID Update Script (id_updater.py) 🆔
    participant T as Tampermonkey Script 🐵 (on LMArena page)
    participant L as LMArena.ai 🌐

    alt Initialization
        T->>+S: (Page Load) Establish WebSocket connection
        S-->>-T: Confirm connection
    end

    alt Manually Update Model List (Optional)
        MU->>+S: (User runs) POST /internal/request_model_update
        S->>T: (WebSocket) Send 'send_page_source' command
        T->>T: Fetch page HTML
        T->>S: (HTTP) POST /internal/update_available_models (with HTML)
        S->>S: Parse HTML and extract model list
        S->>S: Save to available_models.json
    end

    alt Capturing Session ID (Optional)
        IU->>+S: (User runs) POST /internal/activate_id_update
        S->>T: (WebSocket) Send 'activate_id_update' command
        T->>T: Show 🎯 indicator in page title
        Note over T: User clicks Retry button on LMArena
        T->>T: Intercept WebSocket request, extract sessionId & messageId
        T->>S: (HTTP) POST /internal/update_session_id (with IDs)
        S->>S: Write IDs to config.jsonc
        S-->>-IU: Return success
    end

    alt Normal Chat Request
        C->>+S: POST /v1/chat/completions (OpenAI-compatible request)
        S->>S: Parse request, lookup model ID from models.json
        S->>S: Get sessionId/messageId (from model_endpoint_map.json or config.jsonc)
        S->>+T: (WebSocket) Send 'lmarena_request' command (with prompt, model, session, etc.)
        T->>T: Construct LMArena API request
        T->>+L: (WebSocket) Send request to LMArena API
        L-->>T: (WebSocket) Stream response chunks
        T->>-S: (WebSocket) Forward response chunks
        S-->>-C: (Server-Sent Events) Stream response in OpenAI format
    end
```

**Explanation**:
1.  **Client** sends a standard OpenAI API request to the **local server**.
2.  **Local server** parses the request, looks up the model configuration, and forwards the task to the **Tampermonkey script** via WebSocket.
3.  **Tampermonkey script** constructs a request conforming to LMArena's API format and sends it directly to **LMArena** via WebSocket in the browser environment.
4.  **LMArena** streams responses back to the **Tampermonkey script**.
5.  **Tampermonkey script** forwards the response to the **local server**, which then streams it back to the **client** in OpenAI-compatible format.

## ☁️ Cloud Deployment with Workers

LMArena Bridge supports a distributed cloud architecture where you can deploy the API server to platforms like Render.com while running browser-based workers on your local machines or other devices.

### Architecture Overview

```
┌─────────────────────┐
│   OpenAI Client     │
│   (Any App)         │
└──────────┬──────────┘
           │ HTTP/HTTPS
           ▼
┌─────────────────────────────┐
│  Cloud API Server           │
│  (Render.com/Heroku/etc.)   │
│  - Receives API requests    │
│  - Manages request queue    │
│  - Distributes to workers   │
└──────────┬──────────────────┘
           │ WebSocket (wss://)
           ▼
    ┌──────┴──────┬──────────┐
    │             │           │
┌───▼────┐   ┌───▼────┐  ┌──▼─────┐
│Worker 1│   │Worker 2│  │Worker 3│
│(Local) │   │(Local) │  │(VPS)   │
└───┬────┘   └───┬────┘  └──┬─────┘
    │            │           │
    ▼            ▼           ▼
┌────────────────────────────────┐
│      LMArena.ai                │
│   (Browser Automation)         │
└────────────────────────────────┘
```

### Why Use Cloud Deployment?

- **🌍 Public Access**: Access your LMArena proxy from anywhere
- **📱 Multiple Devices**: Connect workers from different machines
- **⚖️ Load Distribution**: Handle multiple requests concurrently across workers
- **🔒 Centralized Control**: Manage all workers from a single API server
- **💰 Cost Effective**: Free hosting on platforms like Render.com

## 🚀 Deploying to Render.com

### Prerequisites

- A [Render.com](https://render.com) account (free tier works!)
- Git repository with your code (fork this repo)
- At least one local machine with a browser to run as a worker

### Step 1: Prepare Your Repository

1. **Fork this repository** to your GitHub account
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/LMArenaBridge.git
   cd LMArenaBridge
   ```

### Step 2: Create Render.com Service

1. **Log in to Render.com** and click "New +"
2. Select **"Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service**:
   - **Name**: `lmarena-bridge` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api_server.py`
   - **Plan**: Free (or paid for better performance)

### Step 3: Configure Environment Variables

In Render.com dashboard, add these environment variables:

#### Required Variables:

```bash
# Worker Authentication Tokens (comma-separated)
WORKER_TOKENS=your-secret-token-1,your-secret-token-2,your-secret-token-3

# Admin Dashboard Credentials (for first-time setup)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-secure-password-here
```

#### Optional Variables:

```bash
# Enable specific features
ENABLE_AUTO_UPDATE=false
BYPASS_ENABLED=true
TAVERN_MODE_ENABLED=false
```

### Step 4: Modify config.jsonc for Cloud Mode

Before deploying, update your `config.jsonc`:

```jsonc
{
  // Change deployment mode to cloud
  "deployment_mode": "cloud",
  
  // Worker settings
  "worker_settings": {
    "require_authentication": true,
    "heartbeat_interval_seconds": 30,
    "max_workers": 10,
    "worker_timeout_seconds": 120,
    // Leave empty - will use environment variable WORKER_TOKENS
    "valid_tokens": []
  },
  
  // Queue settings
  "queue_settings": {
    "max_wait_seconds": 60,
    "reject_when_no_workers": true
  },
  
  // Cloud settings - update with your actual Render URL
  "cloud_settings": {
    "public_ws_url": "wss://your-app-name.onrender.com/ws/worker",
    "cors_allowed_origins": ["*"]
  }
}
```

**Important**: Replace `your-app-name` with your actual Render service name!

### Step 5: Deploy to Render

1. **Commit your changes**:
   ```bash
   git add config.jsonc
   git commit -m "Configure for cloud deployment"
   git push origin main
   ```

2. **Render will automatically build and deploy** your service

3. **Wait for deployment** to complete (check Render logs)

4. **Note your service URL**: `https://your-app-name.onrender.com`

### Step 6: Set Up Local Workers

Now you need to set up browser-based workers that connect to your cloud server.

#### A. Install Dependencies on Worker Machine

```bash
cd LMArenaBridge
pip install -r requirements.txt
```

#### B. Configure worker_config.jsonc

Edit `worker_config.jsonc` on your **local worker machine**:

```jsonc
{
  // Unique worker identifier
  "worker_id": "worker-home-pc",
  
  // Must match one of the tokens in WORKER_TOKENS environment variable
  "worker_auth_token": "your-secret-token-1",
  
  // Your Render.com WebSocket URL (use wss:// for secure connection)
  "cloud_server_url": "wss://your-app-name.onrender.com/ws/worker",
  
  // Connection settings
  "auto_reconnect": true,
  "reconnect_delay_seconds": 5,
  "max_reconnect_attempts": 0,
  
  // Heartbeat settings
  "send_heartbeat": true,
  "heartbeat_interval_seconds": 30,
  
  // LMArena session settings (configure after capturing IDs)
  "session_id": "YOUR_SESSION_ID_HERE",
  "message_id": "YOUR_MESSAGE_ID_HERE",
  "id_updater_last_mode": "direct_chat",
  "id_updater_battle_target": "A"
}
```

#### C. Capture Session IDs for Worker

Each worker needs its own LMArena session:

1. **Start the worker**:
   ```bash
   python api_server.py --worker
   ```

2. **Install Tampermonkey script** in your browser (see setup instructions above)

3. **Open LMArena.ai** in your browser

4. **Run ID updater** (in a new terminal):
   ```bash
   python id_updater.py
   ```

5. **Follow the prompts** to capture session IDs

6. **Verify** that `worker_config.jsonc` has been updated with session IDs

#### D. Start the Worker

```bash
python api_server.py --worker
```

You should see:
```
✅ Worker connected to cloud server
🔄 Heartbeat started
📡 Waiting for requests from cloud server...
```

### Step 7: Test Your Cloud Deployment

1. **Get your Render API URL**: `https://your-app-name.onrender.com`

2. **Test with curl**:
   ```bash
   curl https://your-app-name.onrender.com/v1/models \
     -H "Authorization: Bearer sk-lmarena-your-dashboard-token"
   ```

3. **Test chat completion**:
   ```bash
   curl https://your-app-name.onrender.com/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-lmarena-your-dashboard-token" \
     -d '{
       "model": "gpt-4",
       "messages": [{"role": "user", "content": "Hello!"}],
       "stream": false
     }'
   ```

4. **Configure your OpenAI client**:
   - **Base URL**: `https://your-app-name.onrender.com/v1`
   - **API Key**: Your dashboard token (starts with `sk-lmarena-`)

### Step 8: Access the Dashboard

1. **Navigate to**: `https://your-app-name.onrender.com`
2. **Login** with the admin credentials you set in environment variables
3. **Create API tokens** for your applications
4. **Monitor usage** and worker status

## 🔧 Advanced Cloud Deployment Topics

### Running Multiple Workers

You can run multiple workers from different machines:

1. **On Worker Machine 1**:
   ```jsonc
   {
     "worker_id": "worker-home-pc",
     "worker_auth_token": "token-1",
     "cloud_server_url": "wss://your-app.onrender.com/ws/worker"
   }
   ```

2. **On Worker Machine 2**:
   ```jsonc
   {
     "worker_id": "worker-laptop",
     "worker_auth_token": "token-2",
     "cloud_server_url": "wss://your-app.onrender.com/ws/worker"
   }
   ```

3. **Each worker** maintains its own LMArena session and processes requests independently

### Load Balancing

The cloud server automatically distributes requests across healthy workers:

- **Round-robin** selection of available workers
- **Health checking** via heartbeat system
- **Automatic failover** if a worker disconnects
- **Queue management** when all workers are busy

### Monitoring Workers

Check worker status via the dashboard or API:

```bash
# Get worker status
curl https://your-app-name.onrender.com/api/workers/status \
  -H "Authorization: Bearer your-admin-token"
```

### Scaling Workers

**Horizontal Scaling**:
- Add more worker machines as needed
- Each worker can handle 1 concurrent request
- 5 workers = 5 concurrent requests

**Vertical Scaling**:
- Run multiple worker instances on same machine
- Use different session IDs for each instance
- Use different worker IDs in config

### Security Best Practices

1. **Use Strong Tokens**:
   ```bash
   # Generate secure tokens
   openssl rand -hex 32
   ```

2. **Rotate Tokens Regularly**:
   - Update `WORKER_TOKENS` in Render environment variables
   - Update `worker_config.jsonc` on all workers
   - Restart workers after token change

3. **Use HTTPS/WSS**:
   - Render provides HTTPS by default
   - Always use `wss://` for worker connections

4. **Restrict CORS** (Optional):
   ```jsonc
   "cloud_settings": {
     "cors_allowed_origins": ["https://yourdomain.com"]
   }
   ```

### Troubleshooting Cloud Deployment

#### Workers Not Connecting

1. **Check WebSocket URL**:
   - Must use `wss://` (not `ws://`)
   - Must include `/ws/worker` path
   - Example: `wss://your-app.onrender.com/ws/worker`

2. **Verify Authentication Token**:
   - Token in `worker_config.jsonc` must match one in `WORKER_TOKENS`
   - Tokens are case-sensitive

3. **Check Render Logs**:
   ```bash
   # View real-time logs
   render logs -f
   ```

#### Requests Timing Out

1. **Increase Timeout**:
   ```jsonc
   "stream_response_timeout_seconds": 600
   ```

2. **Check Worker Status**:
   - Ensure browser is open on worker machine
   - Verify Tampermonkey script is active (✅ in title)

3. **Review Queue Settings**:
   ```jsonc
   "queue_settings": {
     "max_wait_seconds": 120,  // Increase if needed
     "reject_when_no_workers": false  // Queue requests instead
   }
   ```

#### Render Free Tier Limitations

- **Spins down after 15 minutes** of inactivity
- **Cold starts** take 30-60 seconds to wake up
- Consider using a **cron job** to ping your service every 10 minutes to keep it warm:
  ```bash
  # Add to crontab (crontab -e)
  */10 * * * * curl https://your-app-name.onrender.com/health
  ```

## 🔐 Environment Variables for Deployment

For easier deployment to cloud platforms like Render.com, Heroku, or Docker, you can use environment variables instead of configuration files for sensitive credentials.

### Dashboard Admin Credentials

Set these environment variables to automatically create an admin user on first startup:

```bash
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password
```

The dashboard server will:
- Check if any users exist in the database
- If no users exist, create an admin user with the provided credentials
- If users already exist, skip creation to avoid conflicts

### Worker Authentication Tokens

For cloud worker architecture, set worker tokens via environment variable:

```bash
WORKER_TOKENS="token1,token2,token3"
```

**Format**: Comma-separated list of tokens

**Priority**: Environment variable takes precedence over `config.jsonc`

**Example for Render.com**:
1. Go to your service settings
2. Add environment variables in the "Environment" section
3. Set `WORKER_TOKENS` with your comma-separated tokens
4. Workers can now authenticate using these tokens

### All Available Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WORKER_TOKENS` | Comma-separated worker auth tokens | - | For cloud mode |
| `ADMIN_USERNAME` | Initial admin username | - | For first setup |
| `ADMIN_EMAIL` | Initial admin email | - | For first setup |
| `ADMIN_PASSWORD` | Initial admin password | - | For first setup |
| `ENABLE_AUTO_UPDATE` | Enable auto-update checks | `true` | No |
| `BYPASS_ENABLED` | Enable bypass mode | `true` | No |
| `TAVERN_MODE_ENABLED` | Enable Tavern mode | `false` | No |
| `FILE_BED_ENABLED` | Enable file hosting | `false` | No |
| `FILE_BED_UPLOAD_URL` | File hosting server URL | - | If file bed enabled |
| `FILE_BED_API_KEY` | File hosting API key | - | If file bed enabled |

### Configuration Priority

The system uses the following priority order:

1. **Environment Variables** (highest priority)
   - `WORKER_TOKENS` for worker authentication
   - `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` for admin creation
   - Feature flags like `BYPASS_ENABLED`, `TAVERN_MODE_ENABLED`, etc.

2. **Configuration Files** (fallback)
   - `config.jsonc` for all settings (if environment variables not set)
   - `worker_config.jsonc` for worker-specific settings
   - Manual user creation via API or web interface (if admin env vars not set)

### Example: Complete Render.com Setup

In your Render.com service environment variables section, add:

```bash
# Worker Authentication
WORKER_TOKENS=abc123def456,xyz789uvw012,pqr345stu678

# Admin Account (auto-created on first run)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-very-secure-password-here

# Feature Toggles
ENABLE_AUTO_UPDATE=false
BYPASS_ENABLED=true
TAVERN_MODE_ENABLED=false

# Optional: File Hosting (if using)
FILE_BED_ENABLED=false
```

### Security Best Practices

✅ **DO**:
- Use environment variables for production deployments
- Generate strong, unique tokens for each worker (32+ characters)
- Use Render's "Generate Value" feature for passwords
- Rotate tokens periodically (every 90 days recommended)
- Use secrets management services (AWS Secrets Manager, Vault, etc.) for enterprise
- Keep different tokens for development/staging/production

❌ **DON'T**:
- Commit tokens or passwords to version control
- Share tokens between environments (dev/staging/prod)
- Use simple or predictable token values (e.g., "token1", "password123")
- Store tokens in plain text files in production
- Reuse the same admin password across multiple deployments

### Generating Secure Tokens

Use these methods to generate secure tokens:

```bash
# Method 1: OpenSSL (recommended)
openssl rand -hex 32

# Method 2: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## 📊 Using the Dashboard

The integrated web dashboard provides a user-friendly interface for managing API tokens, monitoring usage, and viewing analytics.

### Dashboard Features

- **🔐 User Authentication** - Secure login system with session management
- **🔑 Token Management** - Create, view, and revoke API tokens
- **📈 Usage Analytics** - Track requests, response times, and model usage
- **👥 Multi-User Support** - Multiple users with individual token management
- **📊 Visual Charts** - Real-time charts showing usage trends
- **🔄 Auto-Refresh** - Dashboard auto-updates every 30 seconds

### Accessing the Dashboard

**Local Deployment**:
- Navigate to `http://127.0.0.1:5102` (same port as API server)
- Or start separately on port 5105: `python dashboard_server.py`

**Cloud Deployment** (Render.com):
- Navigate to `https://your-app-name.onrender.com`
- Login with the credentials from environment variables

### First-Time Setup

1. **If using environment variables** (recommended for cloud):
   - Admin user is auto-created on first startup
   - Login with `ADMIN_USERNAME` and `ADMIN_PASSWORD`

2. **If setting up manually**:
   ```bash
   curl -X POST http://127.0.0.1:5102/api/admin/init \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "email": "admin@example.com",
       "password": "your_secure_password"
     }'
   ```

### Creating API Tokens

1. **Login to dashboard**
2. **Navigate to "Tokens" page**
3. **Click "Create New Token"**
4. **Set optional expiration date**
5. **Copy the generated token** (starts with `sk-lmarena-`)
6. **Use in your OpenAI client**:
   ```python
   from openai import OpenAI
   
   client = OpenAI(
       api_key="sk-lmarena-your-token-here",
       base_url="https://your-app.onrender.com/v1"
   )
   ```

### Monitoring Usage

The dashboard provides comprehensive usage statistics:

- **Total Requests** - Count of all API calls
- **Active Tokens** - Number of valid tokens
- **Average Response Time** - Performance metrics
- **Request Trends** - 7-day chart of request volume
- **Top Models** - Most frequently used models
- **Recent Activity** - Latest API requests with details

See **[DASHBOARD_README.md](DASHBOARD_README.md)** for complete dashboard documentation.

## 🎯 Example Use Cases

### Use Case 1: Personal AI Assistant

**Setup**: Deploy to Render.com with 1 worker at home

**Configuration**:
- Cloud server on Render.com (free tier)
- 1 local worker on home PC
- Dashboard for token management

**Benefits**:
- Access from phone, tablet, laptop anywhere
- Use with ChatGPT-compatible apps
- Monitor usage and costs

### Use Case 2: Team Development

**Setup**: Shared deployment with multiple workers

**Configuration**:
- Cloud server on Render.com (paid tier for better performance)
- 3-5 workers across team members' machines
- Individual dashboard accounts for each developer
- Separate tokens for different projects

**Benefits**:
- Load distributed across team
- Higher concurrency (multiple simultaneous requests)
- Usage tracking per developer
- Centralized token management

### Use Case 3: Production Service

**Setup**: High-availability deployment

**Configuration**:
- Cloud server on paid hosting (Render.com Pro or AWS)
- 10+ dedicated workers on VPS instances
- Monitoring and alerting
- Token rotation schedule
- Backup workers for failover

**Benefits**:
- High reliability and uptime
- Handles many concurrent users
- Professional monitoring
- Scalable architecture

## 🔍 Debugging and Logging

### Enable Debug Logging

In `config.jsonc`:
```jsonc
{
  "log_level": "DEBUG"  // Options: DEBUG, INFO, WARNING, ERROR
}
```

In `worker_config.jsonc`:
```jsonc
{
  "enable_logging": true,
  "log_level": "DEBUG"
}
```

### Common Issues and Solutions

#### Issue: "No healthy workers available"

**Symptoms**: API returns 503 error

**Solutions**:
1. Check if any workers are running
2. Verify worker authentication tokens match
3. Check worker logs for connection errors
4. Ensure browser is open with LMArena page
5. Verify Tampermonkey script is active (✅ in title)

#### Issue: "Session ID invalid"

**Symptoms**: Requests fail with session errors

**Solutions**:
1. Re-run `id_updater.py` to capture new session IDs
2. Ensure LMArena page is logged in
3. Check if session expired (LMArena sessions can expire)
4. Verify session IDs in config files match captured IDs

#### Issue: "Worker keeps disconnecting"

**Symptoms**: Worker shows reconnection messages

**Solutions**:
1. Check network stability
2. Verify cloud server is running (Render may have spun down)
3. Check firewall isn't blocking WebSocket connections
4. Increase `reconnect_delay_seconds` in worker config
5. Review cloud server logs for errors

#### Issue: "Slow response times"

**Symptoms**: Requests take very long to complete

**Solutions**:
1. Check if worker machine has good internet connection
2. Verify LMArena.ai is responding quickly (test directly)
3. Increase `stream_response_timeout_seconds`
4. Add more workers to distribute load
5. Use paid Render tier for better server performance

#### Issue: "Dashboard not accessible"

**Symptoms**: Cannot access dashboard UI

**Solutions**:
1. Verify server is running on correct port
2. Check if `use_dashboard_tokens` is `true` in config
3. Try accessing `/health` endpoint first
4. Review server logs for startup errors
5. Ensure port is not blocked by firewall

### Viewing Logs

**Local Deployment**:
```bash
# API Server logs (stdout)
python api_server.py

# Worker logs (stdout)
python api_server.py --worker
```

**Cloud Deployment (Render)**:
```bash
# Install Render CLI
npm install -g render

# View live logs
render logs -f
```

**Dashboard Logs**:
```bash
# Check SQLite database
sqlite3 dashboard.db "SELECT * FROM usage_logs ORDER BY created_at DESC LIMIT 10;"
```

## 🤝 Contributing

We welcome contributions to LMArena Bridge! Whether it's bug fixes, new features, documentation improvements, or examples, your help is appreciated.

### How to Contribute

1. **Fork the repository** on GitHub
2. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and commit:
   ```bash
   git commit -m "Add: description of your changes"
   ```
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** on the main repository

### Contribution Guidelines

- **Code Style**: Follow existing code style and conventions
- **Documentation**: Update documentation for any new features
- **Testing**: Test your changes thoroughly before submitting
- **Commit Messages**: Use clear, descriptive commit messages
- **One Feature Per PR**: Keep pull requests focused on a single feature or fix

### Areas for Contribution

- 🐛 **Bug Fixes**: Report and fix bugs
- ✨ **New Features**: Add new capabilities
- 📚 **Documentation**: Improve guides and examples
- 🌐 **Translations**: Translate documentation to other languages
- 🎨 **UI Improvements**: Enhance the dashboard interface
- 🧪 **Testing**: Add unit tests and integration tests
- 🔧 **DevOps**: Improve deployment scripts and CI/CD

### Reporting Issues

When reporting issues, please include:
- Your operating system and Python version
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant logs or error messages
- Configuration files (with sensitive data removed)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### What This Means

✅ **You can**:
- Use this software for personal or commercial purposes
- Modify the source code
- Distribute copies of the software
- Sublicense the software

❌ **You must**:
- Include the original copyright notice
- Include the license text

⚠️ **Disclaimer**:
- This software is provided "as is", without warranty of any kind
- The authors are not liable for any damages arising from its use

## 🙏 Acknowledgments

- **LMArena.ai** - For providing access to a wide variety of language models
- **FastAPI** - For the excellent web framework
- **OpenAI** - For the API specification we're compatible with
- **Contributors** - Thanks to all who have contributed to this project
- **Community** - For bug reports, feature requests, and feedback

## 📞 Support and Contact

### Getting Help

- 📖 **Documentation**: Check the README and additional docs first
- 🐛 **Bug Reports**: Open an issue on GitHub with details
- 💡 **Feature Requests**: Open an issue describing your idea
- 💬 **Discussions**: Use GitHub Discussions for questions and ideas

### Important Notes

⚠️ **Disclaimer**: This project is not affiliated with or endorsed by LMArena.ai. It's an independent community project that provides an interface to their platform.

⚠️ **Usage Policy**: Please respect LMArena's terms of service and rate limits when using this proxy.

⚠️ **Security**: Never share your session IDs, API keys, or worker tokens publicly. Keep them secure.

## 🚀 Quick Links

- **[GitHub Repository](https://github.com/Lianues/LMArenaBridge)** - Source code and releases
- **[Issues](https://github.com/Lianues/LMArenaBridge/issues)** - Bug reports and feature requests
- **[Discussions](https://github.com/Lianues/LMArenaBridge/discussions)** - Community Q&A
- **[LMArena.ai](https://lmarena.ai/)** - The platform we interface with
- **[Render.com](https://render.com)** - Recommended cloud hosting platform

## 🎉 Getting Started Checklist

Ready to deploy? Use this checklist:

### Local Setup
- [ ] Install Python dependencies (`pip install -r requirements.txt`)
- [ ] Install Tampermonkey extension and script
- [ ] Start API server (`python api_server.py`)
- [ ] Open LMArena.ai in browser (verify ✅ in title)
- [ ] Update model list (`python model_updater.py`)
- [ ] Capture session IDs (`python id_updater.py`)
- [ ] Configure OpenAI client with API base URL
- [ ] Test with a chat request

### Cloud Deployment (Render.com)
- [ ] Fork repository to your GitHub account
- [ ] Create Render.com web service
- [ ] Set environment variables (`WORKER_TOKENS`, admin credentials)
- [ ] Update `config.jsonc` with deployment mode "cloud"
- [ ] Update `cloud_settings.public_ws_url` with your Render URL
- [ ] Deploy to Render (push to GitHub)
- [ ] Wait for deployment to complete
- [ ] Set up local worker machine(s)
- [ ] Configure `worker_config.jsonc` with cloud server URL
- [ ] Capture session IDs on worker machine
- [ ] Start worker(s) (`python api_server.py --worker`)
- [ ] Access cloud dashboard and create API tokens
- [ ] Test API with cloud URL
- [ ] Monitor worker status and usage

### Optional Enhancements
- [ ] Set up file hosting server (if needed)
- [ ] Configure model-specific sessions in `model_endpoint_map.json`
- [ ] Set up cron job to keep Render service warm
- [ ] Configure custom CORS origins
- [ ] Set up monitoring and alerting
- [ ] Document your deployment for team members

---

**Made with ❤️ by the community | Happy Bridging! 🌉**
