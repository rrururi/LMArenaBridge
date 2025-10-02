#!/usr/bin/env python3
"""
Script to translate Chinese comments and strings in api_server.py to English.
Processes the file and replaces Chinese text with English translations.
"""

import re

# Comprehensive translation dictionary
translations = {
    # File header
    "# api_server.py\n# 新一代 LMArena Bridge 后端服务": "# api_server.py\n# Next-generation LMArena Bridge backend service",
    
    # Section headers
    "# --- 内部模块导入 ---": "# --- Internal Module Imports ---",
    "# --- 基础配置 ---": "# --- Basic Configuration ---",
    "# --- 全局状态与配置 ---": "# --- Global State and Configuration ---",
    "# --- 模型映射 ---": "# --- Model Mapping ---",
    "# --- 公告处理 ---": "# --- Announcement Handling ---",
    "# --- 更新检查 ---": "# --- Update Check ---",
    "# --- 模型更新 ---": "# --- Model Update ---",
    "# --- 自动重启逻辑 ---": "# --- Auto-Restart Logic ---",
    "# --- FastAPI 生命周期事件 ---": "# --- FastAPI Lifecycle Events ---",
    "# --- CORS 中间件配置 ---": "# --- CORS Middleware Configuration ---",
    "# --- 辅助函数 ---": "# --- Helper Functions ---",
    "# --- OpenAI 格式化辅助函数": "# --- OpenAI Formatting Helper Functions",
    "# --- WebSocket 端点 ---": "# --- WebSocket Endpoint ---",
    "# --- OpenAI 兼容 API 端点 ---": "# --- OpenAI Compatible API Endpoints ---",
    "# --- 内部通信端点 ---": "# --- Internal Communication Endpoints ---",
    "# --- 主程序入口 ---": "# --- Main Program Entry Point ---",
    
    # Common phrases in comments
    "存储从 config.jsonc 加载的配置": "Store configuration loaded from config.jsonc",
    "用于存储与单个油猴脚本的 WebSocket 连接": "Used to store WebSocket connection with single Tampermonkey script",
    "注意：此架构假定只有一个浏览器标签页在工作": "Note: This architecture assumes only one browser tab is working",
    "如果需要支持多个并发标签页，需要将此扩展为字典管理多个连接": "To support multiple concurrent tabs, this needs to be extended to a dictionary managing multiple connections",
    "用于存储每个 API 请求的响应队列": "Used to store response queue for each API request",
    "键是 request_id，值是 asyncio.Queue": "Key is request_id, value is asyncio.Queue",
    "记录最后一次活动的时间": "Record the time of last activity",
    "空闲监控线程": "Idle monitoring thread",
    "主事件循环": "Main event loop",
    "新增：用于跟踪是否因人机验证而刷新": "New: Used to track if refreshing due to human verification",
    "现在将存储更丰富的对象": "Now will store richer objects",
    "新增：用于存储模型到 session/message ID 的映射": "New: Used to store mapping of models to session/message IDs",
    "默认模型id": "Default model id",
    
    # Function docstrings and comments
    '"""从 model_endpoint_map.json 加载模型到端点的映射。"""': '"""Load model-to-endpoint mapping from model_endpoint_map.json."""',
    '"""稳健地解析 JSONC 字符串，移除注释。"""': '"""Robustly parse JSONC string, removing comments."""',
    '"""从 config.jsonc 加载配置，并处理 JSONC 注释。"""': '"""Load configuration from config.jsonc and handle JSONC comments."""',
    '"""从 models.json 加载模型映射，支持 \'id:type\' 格式。"""': '"""Load model mapping from models.json, supporting \'id:type\' format."""',
    '"""检查并显示一次性公告。"""': '"""Check and display one-time announcement."""',
    '"""从 GitHub 检查新版本。"""': '"""Check for new version from GitHub."""',
    '"""下载并解压最新版本到临时文件夹。"""': '"""Download and extract latest version to temporary folder."""',
    '"""从 HTML 内容中提取完整的模型JSON对象，使用括号匹配确保完整性。"""': '"""Extract complete model JSON objects from HTML content, using bracket matching to ensure completeness."""',
    '"""将提取到的完整模型对象列表保存到指定的JSON文件中。"""': '"""Save extracted complete model object list to specified JSON file."""',
    '"""优雅地通知客户端刷新，然后重启服务器。"""': '"""Gracefully notify client to refresh, then restart server."""',
    '"""在后台线程中运行，监控服务器是否空闲。"""': '"""Run in background thread, monitor if server is idle."""',
    '"""在服务器启动时运行的生命周期函数。"""': '"""Lifecycle function that runs when server starts."""',
    '"""将当前的 CONFIG 对象写回 config.jsonc 文件，保留注释。"""': '"""Write current CONFIG object back to config.jsonc file, preserving comments."""',
    '"""处理OpenAI消息，分离文本和附件。"""': '"""Process OpenAI message, separate text and attachments."""',
    '"""将 OpenAI 请求体转换为油猴脚本所需的简化载荷"""': '"""Convert OpenAI request body to simplified payload required by Tampermonkey script"""',
    '"""格式化为 OpenAI 流式块。"""': '"""Format as OpenAI streaming chunk."""',
    '"""格式化为 OpenAI 结束块。"""': '"""Format as OpenAI finish chunk."""',
    '"""格式化为 OpenAI 错误块。"""': '"""Format as OpenAI error chunk."""',
    '"""构建符合 OpenAI 规范的非流式响应体。"""': '"""Build non-streaming response body compliant with OpenAI specification."""',
    '"""核心内部生成器：处理来自浏览器的原始数据流，并产生结构化事件。"""': '"""Core internal generator: Process raw data stream from browser and generate structured events."""',
    '"""将内部事件流格式化为 OpenAI SSE 响应。"""': '"""Format internal event stream as OpenAI SSE response."""',
    '"""聚合内部事件流并返回单个 OpenAI JSON 响应。"""': '"""Aggregate internal event stream and return single OpenAI JSON response."""',
    '"""处理来自油猴脚本的 WebSocket 连接。"""': '"""Handle WebSocket connection from Tampermonkey script."""',
    '"""提供兼容 OpenAI 的模型列表。"""': '"""Provide OpenAI-compatible model list."""',
    '"""处理聊天补全请求。"""': '"""Handle chat completion request."""',
    '"""接收来自 model_updater.py 的请求"""': '"""Receive request from model_updater.py"""',
    '"""接收来自油猴脚本的页面 HTML，提取并更新 available_models.json。"""': '"""Receive page HTML from Tampermonkey script, extract and update available_models.json."""',
    '"""接收来自 id_updater.py 的通知"""': '"""Receive notification from id_updater.py"""',
}

def translate_file(input_path, output_path):
    """Translate Chinese content in the file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply all translations
    for chinese, english in translations.items():
        content = content.replace(chinese, english)
    
    # Additional regex-based translations for common patterns
    # Translate logger messages
    content = re.sub(r'logger\.info\(f?"成功', lambda m: m.group(0).replace('成功', 'Successfully'), content)
    content = re.sub(r'logger\.info\(f?"正在', lambda m: m.group(0).replace('正在', 'Processing'), content)
    content = re.sub(r'logger\.error\(f?"加载', lambda m: m.group(0).replace('加载', 'Loading'), content)
    content = re.sub(r'logger\.error\(f?"无法', lambda m: m.group(0).replace('无法', 'Unable to'), content)
    content = re.sub(r'logger\.warning\(f?"', lambda m: m.group(0), content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Translation complete. Output saved to {output_path}")

if __name__ == "__main__":
    translate_file("api_server.py", "api_server_translated.py")
    print("\nPlease review api_server_translated.py and then replace api_server.py with it if satisfactory.")
