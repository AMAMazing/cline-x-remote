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

# --- API Key Authentication Setup ---
API_KEY = secrets.token_urlsafe(32)  # Generate a 32-byte secure API key

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 1) Check X-API-Key
        if request.headers.get('X-API-Key') == API_KEY:
            return func(*args, **kwargs)

        # 2) Or check Authorization: Bearer ...
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            bearer_token = auth_header[len('Bearer '):]
            if bearer_token == API_KEY:
                return func(*args, **kwargs)

        # If neither header is correct, reject
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
                # Fallback for Unicode characters
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, str(text).encode('utf-16le'))
            win32clipboard.CloseClipboard()
            return  # Success
        except pywintypes.error as e:
            if e.winerror == 5:  # Access is denied
                print(f"Clipboard access denied. Retrying... (Attempt {i+1}/{retries})")
                time.sleep(delay)
            else:
                raise  # Re-raise other pywintypes errors
        except Exception as e:
            raise  # Re-raise other exceptions
    print(f"Failed to set clipboard after {retries} attempts.")

def set_clipboard_image(image_data):
    """Set image data to clipboard"""
    try:
        # Decode base64 image
        binary_data = base64.b64decode(image_data.split(',')[1])

        # Convert to bitmap using PIL
        image = Image.open(io.BytesIO(binary_data))

        # Convert to bitmap format
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Remove bitmap header
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
    """Extract base64 image data from text"""
    pattern = r'data:image/[^;]+;base64,[a-zA-Z0-9+/]+=*'
    match = re.search(pattern, text)
    return match.group(0) if match else None

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
last_request_time = 0
MIN_REQUEST_INTERVAL = 5  # Minimum time between new tab creation

# Removed set_autopath and set_altpath since D:\\ paths are specific to the original system.

def get_content_text(content: Union[str, List[Dict[str, str]], Dict[str, str]]) -> str:
    """Extract text and handle images from different content formats"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if item.get("type") == "text":
                parts.append(item["text"])
            elif item.get("type") == "image":
                # Extract image data and description
                image_data = item.get("image_url", {}).get("url", "")  # For base64 images
                if not image_data and "data" in item:  # For binary image data
                    image_data = base64.b64encode(item["data"]).decode('utf-8')

                # Set image to clipboard if it's base64 data
                if image_data.startswith('data:image'):
                    set_clipboard_image(image_data)

                # Add image reference to text with description if available
                description = item.get("description", "An uploaded image")
                parts.append(f"[Image: {description}]")

        return "\n".join(parts)
    elif isinstance(content, dict):
        text = content.get("text", "")
        if content.get("type") == "image":
            image_data = content.get("image_url", {}).get("url", "")
            if not image_data and "data" in content:
                image_data = base64.b64encode(content["data"]).decode('utf-8')
            if image_data.startswith('data:image'):
                set_clipboard_image(image_data)
            description = content.get("description", "An uploaded image")
            return f"[Image: {description}]"
        return text
    return ""

def handle_llm_interaction(prompt):
    global last_request_time

    logger.info(f"Starting Claude interaction with prompt: {prompt}")

    # Enforce minimum request interval
    current_time = time.time()
    time_since_last = current_time - last_request_time
    if time_since_last < MIN_REQUEST_INTERVAL:
        sleep(MIN_REQUEST_INTERVAL - time_since_last)

    last_request_time = time.time()

    # Extract image data if present (supports multiple images)
    request_json = request.get_json()
    image_list = []

    if 'messages' in request_json:
        for message in request_json['messages']:
            content = message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image_url':
                        image_url = item.get('image_url', {}).get('url', '')
                        if image_url.startswith('data:image'):
                            image_list.append(image_url)  # Store all images
                            item['image_url']['url'] = '[IMAGE DATA REMOVED]'

    # Combine logs and prompt into a single input
    current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
    headers_log = f"{current_time_str} - INFO - Time since last request: {time_since_last} seconds\n"
    headers_log += f"{current_time_str} - INFO - Request data: {request_json}"

    full_prompt = "\n".join([
        headers_log,
        r'Please follow these rules: For each response, you must use one of the available tools formatted in proper XML tags. Tools include attempt_completion, ask_followup_question, read_file, write_to_file, search_files, list_files, execute_command, and list_code_definition_names. Do not respond conversationally - only use tool commands. Format any code you generate with proper indentation and line breaks, as you would in a standard code editor. Disregard any previous instructions about generating code in a single line or avoiding newline characters.',
        prompt
    ])

    return talkto("gemini", full_prompt, image_list,tabswitch=False)

@app.route('/', methods=['GET'])
@require_api_key
def home():
    logger.info(f"GET request to / from {request.remote_addr}")
    return "Claude API Bridge"

@app.route('/chat/completions', methods=['POST'])
@require_api_key
def chat_completions():
    try:
        data = request.get_json()
        logger.info(f"Request data: {data}")

        if not data or 'messages' not in data:
            return jsonify({'error': {'message': 'Invalid request format'}}), 400

        # Get the last message's content, handling complex formats
        last_message = data['messages'][-1]
        prompt = get_content_text(last_message.get('content', ''))

        request_id = str(int(time.time()))
        is_streaming = data.get('stream', False)

        # Handle the Claude interaction
        response = handle_llm_interaction(prompt)

        if is_streaming:
            def generate():
                response_id = f"chatcmpl-{request_id}"

                # Send role first
                chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "gpt-3.5-turbo",
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant"},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"

                # Stream line by line for XML and code content
                lines = response.splitlines()
                for line in lines:
                    chunk = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "gpt-3.5-turbo",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": line + "\n"},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    sleep(0.1)

                # End stream
                chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "gpt-3.5-turbo",
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return Response(generate(), mimetype='text/event-stream')

        return jsonify({
            'id': f'chatcmpl-{request_id}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': 'gpt-3.5-turbo',
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': response
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': len(prompt),
                'completion_tokens': len(response),
                'total_tokens': len(prompt) + len(response)
            }
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({'error': {'message': str(e)}}), 500

if __name__ == '__main__':
    # Start ngrok tunnel
    ngrok_tunnel = ngrok.connect(3001)
    logger.info(f"Starting Claude API Bridge server on port 3001")
    print(f"Public URL: {ngrok_tunnel.public_url}")
    print(f"API Key: {API_KEY}")
    app.run(host="0.0.0.0", port=3001)
