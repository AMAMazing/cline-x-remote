# Cline x (Remote)

This project provides a simple Flask API that acts as a bridge to interact with an LLM (Language Learning Model). It uses ngrok to expose the API publicly, allowing access from any network.

## Prerequisites

1.  **Python:** Make sure you have Python installed on your system.
2.  **pip:** You'll need pip, the Python package installer.
3.  **ngrok:** Download and install ngrok from [https://ngrok.com/download](https://ngrok.com/download).
4. **Connect your ngrok account.** Go to your ngrok Dashboard and get your authtoken, then in your terminal, run:
```
ngrok authtoken YOUR_AUTHTOKEN
```
## Installation

1.  **Clone the repository:**
 ```
 git clone https://github.com/AMAMazing/cline-x-remote
 cd cline-x-remote
 ```
2. **Install dependencies:** You may need to add `sudo` before running `pip install` in some systems.
```
pip install -r requirements.txt
```
This installs Flask, pyngrok, and other required libraries. If you run into an error about requirements.txt not existing, install them manually by running:
```
pip install flask pyngrok pywin32 pillow requests
```
## Running the API

1.  **Start the Flask server:**
```
python main.py
```
This will:
    *   Start the Flask application on port 3001.
    *   Start an ngrok tunnel to expose the local server.
    *   Print the **Base URL** and **API Key** to the console.

2. **Keep the terminal open.** The server needs to keep running to access the API.

## Accessing the API via Cline

1.  **API Proviver & Model ID**
    *   Go to the Cline settings in VS Code.
    *   Set API Provider to **OpenAI Compatible**
    *   Set Model ID to **gpt-3.5-turbo**
2. **Base URL & API Key**
    *   Set the "Base URL" to the ngrok-provided URL printed in the console when you start the server.
    *   Set the "API Key" to the key printed in the console when you started the server.


