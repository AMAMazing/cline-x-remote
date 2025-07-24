# Cline-X (Remote)

This project provides a simple Flask API that acts as a bridge to interact with an LLM (Language Learning Model). It uses ngrok to expose the API publicly, allowing access from any network.

**Important Note on Authentication**: This application requires an `ngrok` authtoken to function correctly. Please follow the setup instructions for your chosen method carefully.

## How to Use

There are two methods to run this application.

### Method 1: Using the Executable

This is the simplest method. The application will guide you through setting up your `ngrok` authtoken on the first run.

#### Running the Application

1.  **Download the Executable**: Go to the [**Releases**](https://github.com/AMAMazing/cline-x-remote/releases) page and download the `Cline-X-App.exe` file.
2.  **Run the Application**: Double-click the `.exe` file. A terminal window will open.
3.  **First-Time Setup**: If you are running the application for the first time, it will prompt you to enter your `ngrok` authtoken. Paste your token from the [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken) and press Enter. The token will be saved in a `.env` file in the same directory as the executable for future use.
4.  **Get Credentials**: The terminal will display the **Public URL** and **API Key**.
5.  **Keep it Running**: Do not close the terminal window, as that will shut down the server.

### Method 2: Running from Python Source

This method gives you the latest version of the application and is ideal for development.

#### Prerequisites

1.  **Python**: Make sure you have Python installed.
2.  **pip**: The Python package installer.

#### Installation

1.  **Clone the repository**:
    ```
    git clone https://github.com/AMAMazing/cline-x-remote
    cd cline-x-remote
    ```
2.  **Create and activate a virtual environment** (recommended):
    ```
    python -m venv .venv
    .\\.venv\\Scripts\\activate
    ```
3.  **Install dependencies**:
    ```
    pip install -r requirements.txt
    ```

#### Running the API

1.  **Start the Flask server**:
    ```
    python main.py
    ```
2.  **First-Time Setup**: The script will prompt you for your `ngrok` authtoken if it's not already in a `.env` file.
3.  **Get Credentials**: The terminal will display the **Public URL** and **API Key**.
4.  **Keep the terminal open**: The server needs to keep running to access the API.

### Connecting with Cline

Once the server is running, follow these steps to connect it to the Cline VS Code extension:

1.  **API Provider & Model ID**:
    *   Go to the Cline settings in VS Code.
    *   Set **API Provider** to `OpenAI Compatible`.
    *   Set **Model ID** to `gpt-3.5-turbo`.
2.  **Base URL & API Key**:
    *   Set the **Base URL** to the ngrok-provided URL from the terminal.
    *   Set the **API Key** to the key from the terminal.

