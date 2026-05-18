# Technical Architecture Deep Dive

This document provides a highly detailed, recruiter-ready systems engineering breakdown of the **AutoHeal DevOps Agent's** software component design, stateless branch synchronization, security policies, and high-fidelity serverless telemetry layers.

---

## 1. Cloud-Native Modular Component Topography

The platform is designed to operate completely stateless and database-free, leveraging external cloud APIs, event-driven CI/CD execution environments, and git-as-a-ledger storage mechanisms to remain fully compatible with free-tier resource limits (e.g., Render + Vercel):

```
  +--------------------------------------------------------------+
  |              Vercel Serverless Next.js 15 Client             |
  |  - Dashboard  - Security Gate  - AI Analysis  - Telemetry    |
  +-------------------------------|------------------------------+
                                  | (REST API Client / HTTPS)
                                  v
  +--------------------------------------------------------------+
  |         Render Stateless FastAPI v1 Core Gateway             |
  |  - /ai/latest-diagnosis       - /monitoring/summary          |
  |  - /scans/trivy               - /scans/bandit                |
  +-------------------+----------------------+-------------------+
                      |                      |
                      v                      v
             [ReportsService]         [GitHubService]
                      |                      |
                      v (REST / raw)         v (PyGithub)
             +--------+---------+     +------+-------+
             |  GitHub reports  |     |  GitHub      |
             |  branch storage  |     |  Actions     |
             |  (reports/      |     |  API         |
             |   latest/*)      |     |  (runs)      |
             +------------------+     +--------------+
```

### Component Breakdown
1.  **Vercel Serverless Next.js 15 Client**: An extremely polished, responsive dark-theme dashboard designed with Next.js 15 App Router, TypeScript, and Tailwind CSS. It communicates securely with the FastAPI backend through a typed REST client, featuring dynamic HSL status badges, loading states, and clipboard config helpers.
2.  **Render FastAPI ASGI Engine (v1 Router)**: Exposed under strict versioned prefixes (`/api/v1/`), it processes requests using thin controller routes that delegate resource lookups to isolated service layers. All responses conform to a unified enveloped Success/Error JSON model to guarantee stable type checking.
3.  **Dynamic Reports Service Layer (`ReportsService`)**: An isolated service layer responsible for safe report lookups. 
    *   *Local Mode*: Seamlessly reads local `reports/` folder JSONs for offline mock sandbox development.
    *   *Cloud Mode*: Hits the GitHub raw content REST API using authorization tokens to fetch security JSON/SARIF documents from the repository's `reports` branch inside `reports/latest/*`. Includes a **5MB size guard** to protect memory heaps from resource exhaustion attacks.
4.  **GitHub REST Integration Layer (`GitHubService`)**: Queries the GitHub Actions API via PyGithub to capture live pipeline runs, execution statuses, and links. If credentials are not configured, it gracefully defaults to structured mock runs.
5.  **In-Memory Metrics Registry**: Instead of running a persistent database sidecar (Prometheus server + Loki logger + Promtail collector + Grafana kiosk container) which eats over 1.5GB of RAM and crashes Render free tier containers, the core FastAPI engine utilizes a **direct in-memory Prometheus scraping parser** to serve metric durations and error rates in milliseconds with **zero database dependencies**.

---

## 2. Dynamic Git-As-A-Ledger Synchronization Loop

Instead of local file system persistency (which is ephemeral in Render container pods) or complex webhook triggers, the platform implements an **Event-Driven Git-As-A-Ledger Synchronization Loop**:

```
  Next.js 15 Client            FastAPI Engine v1               GitHub API
       |                               |                           |
       |-- GET /ai/latest-diagnosis -->|                           |
       |                               |-- get_workflow_runs() --->|
       |                               |<-- Return active runs ----|
       |                               |                           |
       |                               |-- Is conclusion == "success"?
       |                               |-- YES: Clear stale status
       v                               v                           v
 [System Fully Healthy                 |<-- 404 (No active failure)-|
  Green Shield Banner]                 |                           |
       |                               |-- NO: conclusion == "failure"
       |                               |-- Fetch reports/latest/ai_diagnosis.json
       |                               |   from 'reports' branch (cached 90s)
       v                               v                           v
 [Render Gemini Diagnosis &            |<-- 200 (Active incident) --|
  Copyable safe-patch code]            |
```

### Loop Architecture & Caching Strategy
1.  **Request Ingestion**: When the user loads the AI Analysis or Security pages, the Next.js client requests the respective versioned endpoints.
2.  **Workflow Check**: The backend fetches the latest workflow execution state from the GitHub Actions REST API to verify if the latest build has succeeded or failed.
3.  **Synchronization Checks**:
    *   **Build Passed**: If the latest run's conclusion is `success`, the agent immediately knows the code is fully operational. It suppresses and ignores any stale reports in the storage ledger and raises a clean `404 Not Found` with detail `"No active failures detected. The latest workflow run succeeded."` The frontend captures this and transitions into a beautiful, green **"System Fully Healthy"** operational screen.
    *   **Build Failed**: If the latest run is a failure, the backend fetches `ai_diagnosis.json` (or the scan reports) from the repository's dedicated `reports` branch.
4.  **90-Second Cache TTL & Stale Fallback**:
    *   To prevent hitting GitHub API rate-limits during dashboard refreshes, the backend caches report fetches in a lightweight in-memory TTL cache (90 seconds).
    *   If the GitHub API is temporarily unreachable or rate-limited, the backend gracefully serves the **last successfully cached response (degraded mode)** instead of throwing raw exceptions.

---

## 3. Cloud-Native Observability & Metric Scraping

### Direct In-Memory Prometheus Scraper
The FastAPI backend utilizes the `prometheus_client` to record telemetry:
*   `http_requests_total`: Tracks overall throughput categorized by endpoint path, HTTP method, and status codes.
*   `http_request_duration_seconds`: SLO-aligned histogram measuring latency percentiles.

When the monitoring endpoint `GET /api/v1/monitoring/summary` is requested, the **`MonitoringService`** loops through the local `REGISTRY.collect()` collectors in memory, parsing total request values, average durations, and error rates dynamically:
```python
for metric in REGISTRY.collect():
    if metric.name == "http_requests_total":
        for sample in metric.samples:
            total_requests += int(sample.value)
```
This enables **real-time sub-second metrics reporting with absolutely zero storage or database sidecar overhead**.

### Path Normalization (Cardinality Protection)
To prevent dynamic paths (e.g. `/api/v1/scans/trivy`, `/api/v1/scans/bandit`) from generating an infinite number of unique timeseries metrics inside the Prometheus registry (known as **Cardinality Explosion**), a dynamic path normalizer middleware converts dynamic path parameters into a generic placeholder format (e.g. `/api/v1/scans/{id}`).

---

## 4. Multi-Stage CI/CD Security Gating

The platform enforces rigorous container and application security checks within the GitHub Actions runner environments:

### CI/CD Security Gates
1.  **SAST (Static Application Security Testing)**: Bandit scans the Python backend codebase for dangerous concatenations, raw SQL strings, and shell execution vulnerabilities.
2.  **SCA (Software Composition Analysis)**: `pip-audit` cross-checks all backend requirements against active national vulnerability databases.
3.  **Container Scans (Trivy)**: Scans the target filesystem and final Docker image post-build. Workflow execution terminates on any high or critical severity CVE, and generated reports are pushed automatically to the `reports` branch.

### Chainguard Shell-less Hardening
The production API container runs on a shell-less, package manager-free **Chainguard Distroless Python** base image:
*   **No shell `/bin/sh` or `/bin/bash`**: Prevents terminal session hijacking.
*   **No `apk` / `apt` / `pip` packages**: Bypasses dynamic remote execution downloads.
*   **Non-Root Namespace**: Executes strictly as UID `65532` (`nonroot`), protecting host kernels from namespace escape vulnerabilities.
