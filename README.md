# Cline-X (Remote)

This project provides a simple Flask API that acts as a bridge to interact with an LLM (Language Learning Model). It uses ngrok to expose the API publicly, allowing access from any network.

## How to Use

There are two methods to run this application. The recommended method is to use the pre-built executable from the GitHub Releases page.

### Method 1: Using the Executable (Recommended)

1.  **Download the Executable**: Go to the [**Releases**](https://github.com/AMAMazing/cline-x-remote/releases) page of this repository and download the `Cline-X-App.exe` file from the latest release.
2.  **Run the Application**: Double-click the `Cline-X-App.exe` file to run it. A terminal window will open.
3.  **Get Credentials**: The terminal will display the **Base URL** and **API Key**. You will need these to connect with Cline.
4.  **Keep it Running**: Do not close the terminal window, as this will shut down the server.

### Method 2: Running from Python Source

This method is for users who want to run the application from the source code.

#### Prerequisites

1.  **Python**: Make sure you have Python installed on your system.
2.  **pip**: You'll need pip, the Python package installer.
3.  **ngrok**: Download and install ngrok from [https://ngrok.com/download](https://ngrok.com/download).
4.  **Connect your ngrok account**: Go to your ngrok Dashboard and get your authtoken, then in your terminal, run:
    ```
    ngrok authtoken YOUR_AUTHTOKEN
    ```

#### Installation

1.  **Clone the repository**:
    ```
    git clone https://github.com/AMAMazing/cline-x-remote
    cd cline-x-remote
    ```
2.  **Install dependencies**:
    ```
    pip install -r requirements.txt
    ```

#### Running the API

1.  **Start the Flask server**:
    ```
    python main.py
    ```
2.  **Get Credentials**: The terminal will display the **Base URL** and **API Key**.
3.  **Keep the terminal open**: The server needs to keep running to access the API.

### Connecting with Cline

Once the server is running (using either method), follow these steps to connect it to the Cline VS Code extension:

1.  **API Provider & Model ID**
    *   Go to the Cline settings in VS Code.
    *   Set **API Provider** to `OpenAI Compatible`.
    *   Set **Model ID** to `gpt-3.5-turbo`.
2.  **Base URL & API Key**
    *   Set the **Base URL** to the ngrok-provided URL from the terminal.
    *   Set the **API Key** to the key from the terminal.