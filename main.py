from flask import Flask, jsonify, request, Response, abort
import time
import pywintypes
from time import sleep
import logging
import json
from typing import Union, List, Dict
import base64
import io
from PIL import Image
import re
from talktollm import talkto
import secrets
import webbrowser
from functools import wraps
from pyngrok import ngrok
import os
import sys
from dotenv import load_dotenv, set_key

# --- PATH HANDLING for frozen executables ---
def get_app_path():
    """Get the appropriate path for the application's data files."""
    if getattr(sys, 'frozen', False):
        # Path for the frozen application
        return os.path.dirname(sys.executable)
    else:
        # Path for the script
        return os.path.dirname(os.path.abspath(__file__))

APP_PATH = get_app_path()
DOTENV_PATH = os.path.join(APP_PATH, '.env')

# Load .env file from the application's directory
load_dotenv(dotenv_path=DOTENV_PATH)

# --- CONFIGURATION HANDLING ---
def get_config_path():
    """Returns the full path to the config file."""
    return os.path.join(APP_PATH, "config.txt")

def read_config():
    """Reads the configuration file and returns a dictionary."""
    config = {}
    config_path = get_config_path()
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        print(f"'{config_path}' not found. Creating with default settings.")
        default_config = {'model': 'gemini'}
        write_config(default_config)
        return default_config
    return config

def write_config(config_data):
    """Writes the configuration dictionary to the file."""
    with open(get_config_path(), 'w') as f:
        for key, value in config_data.items():
            f.write(f'{key} = "{value}"\\n')

# Load initial configuration
config = read_config()
current_model = config.get('model', 'gemini')

# --- LOGGING AND FLASK APP SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
app = Flask(__name__)
last_request_time = 0
MIN_REQUEST_INTERVAL = 5

# --- API Key and Clipboard ---
API_KEY = secrets.token_urlsafe(32)

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.headers.get('X-API-Key') == API_KEY or request.headers.get('Authorization', '').replace('Bearer ', '') == API_KEY:
            return func(*args, **kwargs)
        abort(401, description="Invalid or missing API key")
    return wrapper

import win32clipboard

def set_clipboard_image(image_data):
    try:
        binary_data = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(binary_data))
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"Error setting image to clipboard: {e}")
        return False

# --- CORE LOGIC ---
def get_content_text(content: Union[str, List[Dict[str, str]]]) -> str:
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = [item["text"] for item in content if item.get("type") == "text"]
        return "\\n".join(parts)
    return ""

def handle_llm_interaction(prompt):
    global last_request_time
    logger.info(f"Starting {current_model} interaction.")
    current_time = time.time()
    if current_time - last_request_time < MIN_REQUEST_INTERVAL:
        sleep(MIN_REQUEST_INTERVAL - (current_time - last_request_time))
    last_request_time = time.time()

    request_json = request.get_json()
    image_list = []
    if 'messages' in request_json:
        for message in request_json.get('messages', []):
            content = message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image_url':
                        image_url = item.get('image_url', {}).get('url', '')
                        if image_url.startswith('data:image'):
                            image_list.append(image_url)
    
    current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
    headers_log = f"{current_time_str} - INFO - Request data: {request_json}"
    full_prompt = "\\n".join([headers_log, 'Please follow these rules...', prompt])
    
    return talkto(current_model, full_prompt, imagedata=image_list)

# --- FLASK ROUTES ---
@app.route('/', methods=['GET'])
def home():
    """Serves the model selection GUI."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><title>AI Model Bridge</title></head>
    <body>
        <h1>Active Model: <span id="currentModel">{current_model.upper()}</span></h1>
        <button onclick="switchModel('gemini')">Gemini</button>
        <button onclick="switchModel('deepseek')">DeepSeek</button>
        <button onclick="switchModel('aistudio')">AIStudio</button>
        <div id="status"></div>
        <h3>API Key: {API_KEY}</h3>
        <script>
            function switchModel(model) {{
                fetch('/model', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{'model': model}})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        document.getElementById('currentModel').textContent = data.model.toUpperCase();
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """

@app.route('/model', methods=['GET', 'POST'])
def model_route():
    global current_model, config
    if request.method == 'GET':
        return jsonify({'model': current_model})
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            new_model = data['model'].lower()
            if new_model not in ['deepseek', 'gemini', 'aistudio']:
                return jsonify({'success': False, 'error': 'Invalid model'}), 400
            current_model = new_model
            config['model'] = current_model
            write_config(config)
            logger.info(f"Model switched to: {current_model}")
            return jsonify({'success': True, 'model': current_model})
        except Exception as e:
            logger.error(f"Error switching model: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat/completions', methods=['POST'])
@require_api_key
def chat_completions():
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({'error': {'message': 'Invalid request format'}}), 400
        prompt = get_content_text(data['messages'][-1].get('content', ''))
        response = handle_llm_interaction(prompt)
        return jsonify({
            'id': f'chatcmpl-{int(time.time())}', 'object': 'chat.completion', 'created': int(time.time()),
            'model': 'gpt-3.5-turbo', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': response}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': len(prompt), 'completion_tokens': len(response), 'total_tokens': len(prompt) + len(response)}
        })
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({'error': {'message': str(e)}}), 500

if __name__ == '__main__':
    ngrok_authtoken = os.getenv("NGROK_AUTHTOKEN")
    if not ngrok_authtoken:
        print("NGROK_AUTHTOKEN not found in .env file.")
        ngrok_authtoken = input("Please enter your ngrok authtoken: ").strip()
        if ngrok_authtoken:
            set_key(DOTENV_PATH, "NGROK_AUTHTOKEN", ngrok_authtoken)
            print(f"NGROK_AUTHTOKEN saved to {DOTENV_PATH} for future use.")
        else:
            logger.error("No NGROK_AUTHTOKEN provided. Exiting.")
            exit()
    try:
        ngrok.set_auth_token(ngrok_authtoken)
        ngrok_tunnel = ngrok.connect(3001)
        logger.info(f"Starting API Bridge server on port 3001")
        print("-------------------------------------------------")
        print(f"Server running at: http://127.0.0.1:3001")
        print(f"Public URL: {ngrok_tunnel.public_url}")
        print(f"API Key: {API_KEY}")
        print(f"Default Model: {current_model.upper()}")
        print("-------------------------------------------------")
        webbrowser.open_new_tab('http://127.0.0.1:3001')
        app.run(host="0.0.0.0", port=3001)
    except Exception as e:
        logger.error(f"Failed to start ngrok or server: {e}")
        print(f"An error occurred: {e}")
        input("Press Enter to exit.")
