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
- **[Cloud Deployment](docs/CLOUD_DEPLOYMENT.md)** - Deploy to cloud platforms (Coming Soon)
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
        S->>S: Parse HTML an
