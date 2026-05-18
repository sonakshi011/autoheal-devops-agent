# Technical Troubleshooting Guide

This guide documents the real-world operational issues, debugging workflows, and mitigation steps for the **AutoHeal DevOps Agent** platform running in production or local environments.

---

## 🛡️ 1. GitHub CI/CD "Permissions Denied" on Pushes

### Symptoms
During security scans or AI diagnostic phases, the GitHub Action workflow fails with an error:
```bash
fatal: unable to access 'https://github.com/...': The requested URL returned error: 403
Error: Process completed with exit code 128.
```

### Root Cause
GitHub Actions default to read-only permissions for `GITHUB_TOKEN` on newer repositories, blocking the CI/CD runners from committing and pushing reports dynamically to the `reports` branch storage ledger.

### Resolution
Ensure that the workflow files (**[security-scan.yml](file:///d:/projects/autoheal-devops-agent/.github/workflows/security-scan.yml)** and **[ai-failure-analyzer.yml](file:///d:/projects/autoheal-devops-agent/.github/workflows/ai-failure-analyzer.yml)**) have explicit write permissions configured:
```yaml
permissions:
  contents: write
```
Also, confirm inside your GitHub Repository settings:
1.  Navigate to **Settings > Actions > General**.
2.  Scroll down to **Workflow permissions**.
3.  Ensure **Read and write permissions** is selected.

---

## 🧠 2. Gemini API Key Mismatches or Rate Limiting

### Symptoms
*   AI Analysis page displays an error: `Failed to retrieve AI diagnosis: API Key not found or invalid.`
*   AI Diagnosis script logs: `google.api_core.exceptions.ResourceExhausted: 429 Resource has been exhausted (e.g. API rate limits).`

### Diagnosis & Resolution
1.  **Environment Variable Check**:
    Ensure `GEMINI_API_KEY` is set inside the `.env` file for local development or configured as an active Environment Variable inside your Render Web Service.
2.  **API Rate Limiting**:
    Free-tier keys are limited to 15 Requests Per Minute (RPM) for Google Gemini. The platform includes a **90-second in-memory TTL cache** to completely prevent the FastAPI engine from recursively calling GitHub or triggering unnecessary diagnostic fetches on rapid dashboard refreshes. If you hit a rate-limit during local testing, wait 60 seconds before triggering another failure run.

---

## 📊 3. Out-Of-Memory (OOM) Container Crashes on Render Free Tier

### Symptoms
Render service logs show `Container exited with code 137 (OOM Killed)` or the API Gateway becomes temporarily unreachable on rapid requests.

### Root Cause
Older deployments assumed a local, multi-container sidecar stack (Prometheus database + Loki log engine + Promtail daemon + Grafana server) running alongside the API container. Running these memory-heavy engines quickly exceeds the 512MB RAM free-tier thresholds of Render.

### Resolution & Prevention
We completely eliminated persistent datastores by implementing a **direct In-Memory Prometheus Scraper**. 
*   Ensure that you are **not** trying to run the full Docker Compose stack on Render.
*   Confirm that your Render Web Service environment is configured to run the FastAPI app natively (using `docker/Dockerfile.backend` path) rather than launching resource-intensive database services.

---

## 🔒 4. CORS Errors on Next.js Control Panel Fetch Actions

### Symptoms
The Next.js browser console shows:
```
Access to fetch at 'https://autoheal-api.onrender.com/api/v1/...' from origin 'https://autoheal-devops-agent.vercel.app' has been blocked by CORS policy.
```

### Diagnosis & Resolution
FastAPI uses dynamic CORS middleware that maps incoming client origins. In **[app/main.py](file:///d:/projects/autoheal-devops-agent/app/main.py)**, ensure your allowed origins matches the production Vercel domain correctly:
```python
origins = [
    "http://localhost:3000",
    "https://autoheal-devops-agent.vercel.app"
]
```
If you ever deploy the frontend to a custom domain, add that specific domain to this list and redeploy the Render FastAPI engine.
