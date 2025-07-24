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
from functools import wraps
from pyngrok import ngrok
import os
from dotenv import load_dotenv, find_dotenv, set_key

# --- Environment and Logging Setup ---
# Find .env file
dotenv_path = find_dotenv()

# Load environment variables if .env exists
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # Create .env if it doesn't exist
    with open(".env", "w") as f:
        pass
    dotenv_path = find_dotenv()

# --- API Key Authentication Setup ---
API_KEY = secrets.token_urlsafe(32)

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.headers.get('X-API-Key') == API_KEY or \
           request.headers.get('Authorization', '').replace('Bearer ', '') == API_KEY:
            return func(*args, **kwargs)
        abort(401, description="Invalid or missing API key")
    return wrapper

import win32clipboard

def set_clipboard(text, retries=3, delay=0.2):
    for i in range(retries):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            try:
                win32clipboard.SetClipboardText(str(text))
            except Exception:
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, str(text).encode('utf-16le'))
            win32clipboard.CloseClipboard()
            return
        except pywintypes.error as e:
            if e.winerror == 5:
                print(f"Clipboard access denied. Retrying... (Attempt {i+1}/{retries})")
                time.sleep(delay)
            else:
                raise
        except Exception as e:
            raise
    print(f"Failed to set clipboard after {retries} attempts.")

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

def extract_base64_image(text):
    match = re.search(r'data:image/[^;]+;base64,[a-zA-Z0-9+/]+=*', text)
    return match.group(0) if match else None

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

app = Flask(__name__)
last_request_time = 0
MIN_REQUEST_INTERVAL = 5

def get_content_text(content: Union[str, List[Dict[str, str]], Dict[str, str]]) -> str:
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if item.get("type") == "text":
                parts.append(item["text"])
            elif item.get("type") == "image" and "image_url" in item:
                description = item.get("description", "An uploaded image")
                parts.append(f"[Image: {description}]")
        return "\\n".join(parts)
    return ""

def handle_llm_interaction(prompt):
    global last_request_time
    logger.info(f"Starting LLM interaction with prompt: {prompt}")
    current_time = time.time()
    time_since_last = current_time - last_request_time
    if time_since_last < MIN_REQUEST_INTERVAL:
        sleep(MIN_REQUEST_INTERVAL - time_since_last)
    last_request_time = time.time()

    request_json = request.get_json()
    image_list = []

    # Extract image data from the request for talktollm
    if 'messages' in request_json:
        for message in request_json['messages']:
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
    
    # Pass the extracted image data to talkto
    return talkto("gemini", full_prompt, imagedata=image_list, tabswitch=False)

@app.route('/', methods=['GET'])
@require_api_key
def home():
    return "Cline-X API Bridge"

@app.route('/chat/completions', methods=['POST'])
@require_api_key
def chat_completions():
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({'error': {'message': 'Invalid request format'}}), 400
        last_message = data['messages'][-1]
        prompt = get_content_text(last_message.get('content', ''))
        response = handle_llm_interaction(prompt)
        return jsonify({
            'id': f'chatcmpl-{int(time.time())}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': 'gpt-3.5-turbo',
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': response}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': len(prompt), 'completion_tokens': len(response), 'total_tokens': len(prompt) + len(response)}
        })
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({'error': {'message': str(e)}}), 500

if __name__ == '__main__':
    ngrok_authtoken = os.getenv("NGROK_AUTHTOKEN")
    if not ngrok_authtoken:
        print("NGROK_AUTHTOKEN not found.")
        ngrok_authtoken = input("Please enter your ngrok authtoken: ").strip()
        if ngrok_authtoken:
            set_key(dotenv_path, "NGROK_AUTHTOKEN", ngrok_authtoken)
            print("NGROK_AUTHTOKEN saved to .env file for future use.")
        else:
            logger.error("No NGROK_AUTHTOKEN provided. Exiting.")
            exit()
    
    try:
        ngrok.set_auth_token(ngrok_authtoken)
        ngrok_tunnel = ngrok.connect(3001)
        logger.info(f"Starting API Bridge server on port 3001")
        print("-------------------------------------------------")
        print(f"Public URL: {ngrok_tunnel.public_url}")
        print(f"API Key: {API_KEY}")
        print("-------------------------------------------------")
        app.run(host="0.0.0.0", port=3001)
    except Exception as e:
        logger.error(f"Failed to start ngrok or server: {e}")
        print(f"An error occurred: {e}")
        input("Press Enter to exit.")
