# Gemini DeepResearch Assistant

This project is a web-based application built with Gradio that leverages the Google Cloud Discovery Engine's `streamAssist` API to create a powerful, interactive research assistant.

## Features

-   **Interactive, Multi-Step Workflow**: Instead of a one-off report, the application first generates a research plan. The user can then provide feedback and adjustments in a chat interface before committing to the final report generation.
-   **Streaming Responses**: All interactions with the API (plan generation, adjustments, and final report) are streamed back to the UI, providing real-time feedback.
-   **Stateful UI**: The application intelligently manages the UI state, disabling buttons during API calls, showing loading messages, and guiding the user through the workflow.
-   **Reference Parsing**: Automatically extracts and formats citation links from the API response, making them clickable in the final report.
-   **Clean Reset**: After a report is generated, the UI presents a "Start New Research" button to cleanly reset the interface for a new task, while preserving the completed report for review.

## How It Works

The application follows a three-stage process:

1.  **Get Plan**: The user provides a research topic. The app calls the `streamAssist` API to generate a preliminary research plan.
2.  **Adjust Plan**: The UI reveals a chatbot where the user can send natural language feedback (e.g., "Remove the section on history," "Add more details about clinical trials"). Each message is sent to the API, which returns a newly adjusted plan.
3.  **Generate Final Report**: Once the user is satisfied with the plan, they click "Generate Final Report." The app sends a final instruction to the API, which then performs the deep research and streams back the complete report.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd gradio-gemini-deepresearch
    ```

2.  **Create a Python virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your environment variables:**
    *   Rename the `.env.example` file to `.env`.
    *   Open the `.env` file and fill in the required values.

## Authentication

This application uses the Application Default Credentials (ADC) strategy to authenticate with Google Cloud. Before running the app, you must authenticate your local environment.

1.  **Install the Google Cloud CLI**: If you haven't already, [install the gcloud CLI](https://cloud.google.com/sdk/docs/install).

2.  **Log in with your user account**: Run the following command and follow the instructions in your browser to log in to your Google account.

    ```bash
    gcloud auth application-default login
    ```

This command will create a credential file on your local machine that the Python `google-auth` library (used in this project) will automatically detect and use to generate access tokens.

## Finding Your Environment Variable Values

To use the application, you need to provide your Google Cloud `PROJECT_ID`, `LOCATION`, and `APP_ID` in the `.env` file.

### 1. Finding Your `PROJECT_ID`

Your Project ID is a unique string that identifies your project in Google Cloud.

*   **Via the Google Cloud Console**: Navigate to the [Google Cloud Console dashboard](https://console.cloud.google.com/home/dashboard). Your Project ID will be visible in the "Project info" card.
*   **Via the `gcloud` CLI**:
    ```bash
    gcloud config get-value project
    ```

### 2. Finding Your `LOCATION`

This is the location of your Discovery Engine app. It will typically be a multi-region like `global`, `us`, or `eu`, or a specific region like `us-central1`.

*   **Via the Google Cloud Console**: Navigate to the [Discovery Engine page](https://console.cloud.google.com/gen-app-builder/engines) in your project. The location of your apps will be listed in the table.

### 3. Finding Your `APP_ID` (Engine ID)

This is the unique ID for the specific Discovery Engine App (or "Engine") you want to use.

*   **Via the Google Cloud Console**: 
    1.  Go to the [Discovery Engine page](https://console.cloud.google.com/gen-app-builder/engines).
    2.  Click on the name of the App you want to use.
    3.  The **Engine ID** is displayed on the configuration page. This is your `APP_ID`.
*   **Via the `gcloud` CLI**:
    ```bash
    gcloud discoveryengine engines list --location=YOUR_LOCATION --project=YOUR_PROJECT_ID
    ```
    Replace `YOUR_LOCATION` and `YOUR_PROJECT_ID` with the values from the previous steps. The output will list your available engines and their IDs.

## Running the Application

Once your `.env` file is configured, you can run the application with the following command:

```bash
python app.py
```

The application will be available at `http://127.0.0.1:7888`.

## Running Tests

To ensure all components are working correctly, you can run the suite of unit tests:

```bash
python test_app.py
```
