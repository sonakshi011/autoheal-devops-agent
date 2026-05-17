# Deployment & Setup Guide

This guide covers setting up the **AutoHeal DevOps Agent** in various environments, including full-stack local development and production-grade Docker Compose multi-container stack deployments.

---

## 1. Local Full-Stack Development

Recommended for adding new features, modifying frontend pages, or extending the AI diagnosis engine.

### Prerequisites
- Python 3.12+
- Node.js 18+ (with `npm`)
- Google Gemini API Key

### Step A: Backend Setup
1.  **Clone and Enter**:
    ```bash
    git clone https://github.com/your-username/autoheal-devops-agent.git
    cd autoheal-devops-agent
    ```
2.  **Create Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables**:
    Create a `.env` file in the project root:
    ```env
    GEMINI_API_KEY=your_gemini_api_key_here
    ENVIRONMENT=development
    LOG_LEVEL=DEBUG
    GITHUB_TOKEN=your_github_personal_access_token
    GITHUB_REPOSITORY=your_username/your_repository
    GRAFANA_ADMIN_PASSWORD=autoheal
    ```
5.  **Run FastAPI Backend**:
    ```bash
    python -m uvicorn app.main:app --reload --port 8000
    ```

### Step B: Frontend Setup
1.  **Enter Frontend Folder**:
    ```bash
    cd frontend
    ```
2.  **Install Node Modules**:
    ```bash
    npm install
    ```
3.  **Configure Frontend Environment**:
    Create a `frontend/.env.local` file:
    ```env
    NEXT_PUBLIC_API_URL=http://localhost:8000
    NEXT_PUBLIC_GRAFANA_URL=http://localhost:3001
    NEXT_PUBLIC_LOKI_URL=http://localhost:3100
    ```
4.  **Run Next.js Dev Server**:
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 2. Docker Compose Deployment (Recommended)

This compiles and boots the entire full-stack observability and security pipeline in a single, isolated execution.

### Multi-Container Topology
Docker Compose deploys 5 active services on the shared `autoheal-net` bridge network:
- `autoheal-api` (FastAPI backend listening on host port `8000`)
- `prometheus` (Metrics scraping engine listening on host port `9090`)
- `loki` (Logs ingestor listening on host port `3100`)
- `promtail` (System daemon scraper pushing logs to Loki)
- `grafana` (Visualization suite listening on host port `3001`)

### Step 1: Launch the Stack
From the project root directory, run:
```bash
docker compose up -d --build
```

### Step 2: Runtime Architecture Details

#### A. Persistent Reports Bind Mount
To ensure that reports dynamically generated on the host (e.g. via scripts or CI pipelines) appear instantly in the running API container without rebuilds, we bind-mount the `./reports` directory:
```yaml
    volumes:
      - ./reports:/app/reports
```
This maps host `./reports` directly to container `/app/reports`, preventing `404 Not Found` page errors.

#### B. Grafana iframe Integration Overrides
To allow Grafana to be embedded seamlessly as a kiosk inside the Next.js control panel, the container environment overrides three security settings:
```yaml
      - GF_SECURITY_ALLOW_EMBEDDING=true  # Bypasses X-Frame-Options blockages
      - GF_AUTH_ANONYMOUS_ENABLED=true    # Bypasses username/password login prompts
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer  # Assigns secure, read-only permissions
```

#### C. GitHub Token Injection
GitHub Action runs are fetched dynamically from the container. The host's `.env` values are passed directly into the container's environment:
```yaml
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_REPOSITORY=${GITHUB_REPOSITORY}
```

---

## 3. Deployment Health Check Sequence

Once the containers are running, execute this health sequence to verify integration:

1.  **FastAPI Health Check**:
    ```bash
    curl http://localhost:8000/health/
    # Expected: {"status":"healthy","version":"0.1.0"}
    ```
2.  **Prometheus Metrics Check**:
    ```bash
    curl http://localhost:8000/metrics
    # Expected: Plaintext Prometheus OpenMetrics output containing http_requests_total...
    ```
3.  **Prometheus Scraping Target Status**:
    Visit [http://localhost:9090/targets](http://localhost:9090/targets). Ensure the `autoheal-api` target is **UP**.
4.  **Grafana Server Reachability**:
    Visit [http://localhost:3001](http://localhost:3001). It should immediately load the pre-provisioned Grafana home screen without prompting for credentials.

---

[Back to README](../README.md)
