# Deployment & Setup Guide

This guide covers setting up the **AutoHeal DevOps Agent** in two distinct environments:
1.  **Local Development Sandbox (Offline Mock Mode)** — Ideal for rapid local additions, testing, and sandbox validation.
2.  **Production Cloud Deployment (Vercel + Render)** — Deployed production environment utilizing stateless architectures.

---

## 1. Local Development Sandbox (Mock Mode)

Highly recommended for local extensions. In mock mode, the system does not require active GitHub credentials or dynamic network calls, gracefully serving high-fidelity local datasets.

### Prerequisites
*   Node.js 18+ (with `npm`)
*   Python 3.12+
*   Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Step A: Backend Setup
1.  **Clone and Enter**:
    ```bash
    git clone https://github.com/sonakshi011/autoheal-devops-agent.git
    cd autoheal-devops-agent
    ```
2.  **Create and Activate Virtual Environment**:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # On macOS/Linux: source .venv/bin/activate
    ```
3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Local Environment Variables**:
    Create a `.env` file in the project root:
    ```env
    GEMINI_API_KEY=your_gemini_api_key_here
    ENVIRONMENT=development
    LOG_LEVEL=DEBUG
    
    # Leave these empty to automatically enable Mock Fallback Mode
    GITHUB_TOKEN=
    GITHUB_REPOSITORY=
    ```
5.  **Run FastAPI Backend Server**:
    ```bash
    python -m uvicorn app.main:app --reload --port 8000
    ```
    *Access the interactive API Swagger Documentation at [http://localhost:8000/docs](http://localhost:8000/docs).*

### Step B: Frontend Setup
1.  **Enter Frontend Folder**:
    ```bash
    cd frontend
    ```
2.  **Install Node Dependencies**:
    ```bash
    npm install
    ```
3.  **Configure Frontend Environment**:
    Create a `frontend/.env.local` file:
    ```env
    NEXT_PUBLIC_API_URL=http://localhost:8000
    ```
4.  **Run Next.js Dev Server**:
    ```bash
    npm run dev
    ```
    *Open the Control Panel at [http://localhost:3000](http://localhost:3000).*

---

## 2. Production Cloud Deployment (Vercel + Render)

In production, the platform is deployed in a stateless split architecture: the frontend client on Vercel Edge Serverless functions, and the FastAPI API gateway on Render's stateless container services.

### Core Architecture Specifications
*   **Persistent Storage Ledger**: Dedicated, stateless GitHub branch named `reports` (rather than local disk directories).
*   **Workflow Integration**: GitHub Actions dynamically commit security scan files (`trivy-results.json`, `bandit-results.sarif`) and Gemini diagnostics (`ai_diagnosis.json`) directly to `reports/latest/*` under `[skip ci]` commit messages.

### Step 1: Deploy Backend FastAPI Core (Render)
1.  Sign in to [Render](https://render.com) and click **New > Web Service**.
2.  Connect your GitHub repository and specify:
    *   **Environment**: `Docker`
    *   **Dockerfile Path**: `docker/Dockerfile.backend` (Chainguard hardened Distroless base)
3.  Add the following **Environment Variables**:
    *   `GEMINI_API_KEY`: *Your Google Gemini API Key*
    *   `ENVIRONMENT`: `production`
    *   `LOG_LEVEL`: `INFO`
    *   `GITHUB_TOKEN`: *Your GitHub Personal Access Token (PAT with repo permissions)*
    *   `GITHUB_REPOSITORY`: `your-username/your-repository-name`
4.  Launch the Web Service. Note your assigned Render URL (e.g. `https://autoheal-api.onrender.com`).

### Step 2: Deploy Frontend Control Panel (Vercel)
1.  Sign in to [Vercel](https://vercel.com) and click **Add New > Project**.
2.  Select your repository and configure:
    *   **Framework Preset**: `Next.js`
    *   **Root Directory**: `frontend`
3.  Add the following **Environment Variables**:
    *   `NEXT_PUBLIC_API_URL`: `https://autoheal-api.onrender.com` (Your deployed Render API URL)
4.  Click **Deploy**. Once successfully compiled, Vercel gives you your live production domain (e.g. `https://autoheal-devops-agent.vercel.app`).

---

## 3. Production Health Check Checklist

Execute this quick verification sequence to ensure all systems are fully operational:

1.  **FastAPI Core Health**:
    ```bash
    curl https://autoheal-api.onrender.com/health/
    # Expected: {"status":"healthy","version":"0.1.0"}
    ```
2.  **In-Memory Telemetry Check**:
    ```bash
    curl https://autoheal-api.onrender.com/api/v1/monitoring/summary
    # Expected: Enveloped JSON response containing request counts, latencies, and security findings.
    ```
3.  **Swagger API Documentation Access**:
    Visit `https://autoheal-api.onrender.com/docs` to verify that ASGI endpoints are securely exposed.
