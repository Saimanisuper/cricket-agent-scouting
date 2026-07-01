# 🏏 Cricket AI Scouting Agent

An advanced, AI-powered cricket scouting and tactical analysis platform. This application leverages the **GitHub Models API (GPT-4o)** alongside an extensive historical cricket database to generate highly detailed, data-driven tactical playbooks for batting and bowling.

## ✨ Features
* **AI Tactical Playbooks**: Generate step-by-step master plans to dismiss specific batters or score against specific bowling attacks.
* **Historical Data Context**: Ingests massive amounts of Cricsheet CSV data into a local SQLite database for context-aware generations.
* **Modern UI**: A sleek, "Swoosh" themed UI built with React and Vite.
* **FastAPI Backend**: High-performance backend running Python and LangChain concepts.

## 🛠 Tech Stack
* **Frontend**: React, Vite, Vanilla CSS
* **Backend**: Python, FastAPI, Uvicorn, SQLite
* **AI Model**: GPT-4o (via GitHub Models & OpenAI SDK)
* **Deployment**: Configured for Replit, Render, and Vercel

## 🚀 Live Deployment
The easiest way to run and deploy this app for free is using [Replit](https://replit.com/):
1. Import this repository into Replit.
2. In the Replit Secrets (Environment Variables) panel, add `GITHUB_TOKEN` with your GitHub API Token.
3. Click **Run**. Replit will automatically install the requirements and serve both the FastAPI backend and the React frontend in one unified webview!

*(Alternative Docker deployment is available via the included `Dockerfile` for Hugging Face Spaces).*

## 💻 Local Setup
To run this project on your local machine:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Saimanisuper/cricket-agent-scouting.git
   cd cricket-agent-scouting
   ```

2. **Set up the backend environment**:
   Create a `.env` file in the root directory and add your GitHub token:
   ```env
   GITHUB_TOKEN=your_github_token_here
   ```
   Install the requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```
   Start the FastAPI server:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000
   ```

3. **Set up the frontend**:
   In a new terminal window, navigate to the frontend folder:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **View the app**:
   Open `http://localhost:5173` in your browser.

## 🗄️ Database Note
The repository contains a pre-built `cricket.db` SQLite database (`~51MB`) inside the `data/` folder, populated with historical data. To ingest new data, you can place raw Cricsheet CSVs into `data/temp_cricsheet` and run the `scripts/ingest_cricsheet.py` script.
