# Technical Architecture Deep Dive

This document provides an exhaustive, under-the-hood technical breakdown of the **AutoHeal DevOps Agent's** component design, data flow patterns, security posture, and observability interfaces.

---

## 1. Component Map & Interface Topology

AutoHeal is designed as a modular, containerized full-stack platform. It acts as both an automated, CI/CD-linked failure diagnostic runner and a live, interactive engineering control panel:

```
  +-------------------------------------------------------------+
  |              Next.js 14 Frontend Control Panel              |
  |  - Dashboard  - Security Gate  - AI Analysis  - Monitoring  |
  +------------------------------+------------------------------+
                                 | (Standard Fetch Client / HTTP)
                                 v
  +-------------------------------------------------------------+
  |                FastAPI Backend (v1 Route layer)              |
  |  - /api/v1/pipelines/runs   - /api/v1/ai/latest-diagnosis    |
  |  - /api/v1/scans/trivy       - /api/v1/scans/bandit           |
  +------------------+-----------------------+------------------+
                     |                       |
                     v                       v
            [ReportsService]          [GitHubService]
                     |                       |
                     v (Bind Mount)          v (PyGithub)
            +--------+---------+      +------+-------+
            |  reports/        |      |  GitHub      |
            |  ai_diagnosis    |      |  Actions     |
            |  scan results    |      |  API         |
            +------------------+      +--------------+
```

### Component Architecture
1. **Next.js 14 Control Panel**: A highly-polished, dark-theme dashboard designed with the App Router, Lucide icons, and Tailwind CSS. It connects to the backend through a native Fetch Client using typed models, featuring dynamic visual cues like connection health pings, operational gauges, and automated code-remediation clipboard interfaces.
2. **FastAPI Backend (v1 API Engine)**: Exposed through strict versioned prefixes (`/api/v1/`), it processes requests using thin controller routes that delegate heavy lifting to isolated service layers. All responses conform to a unified Success/Error JSON envelope to ensure stable typing.
3. **Reports Service Layer (`ReportsService`)**: An isolated module responsible for safe report lookups. It implements strict validation policies, including a **5MB size guard** to protect memory heaps from resource exhaustion attacks.
4. **GitHub Integration Layer (`GitHubService`)**: Connects to the GitHub Actions REST API via PyGithub to retrieve recent pipeline runs. If credentials are not configured, it gracefully defaults to high-fidelity mock datasets, allowing offline frontend development.
5. **Observability Stack**: Deployed alongside the API as containerized sidecars:
   - **Prometheus** (pulls application performance metrics)
   - **Loki** (ingests application logs)
   - **Promtail** (scrapes Docker stdout and pushes to Loki)
   - **Grafana** (renders pre-provisioned kiosks embedded inside the control panel)

---

## 2. Dynamic Repository State Synchronization Loop

One of the platform's core innovations is its **real-time state synchronization loop**, keeping the frontend in lockstep with the actual branch health without relying on complex, latency-prone webhook infrastructures:

```
 Next.js Client             FastAPI Engine v1             GitHub API
      |                            |                         |
      |-- GET /ai/latest-diagnosis |                         |
      |--------------------------->|                         |
      |                            |-- get_workflow_runs() ->|
      |                            |------------------------>|
      |                            |<-- Return active runs --|
      |                            |-------------------------|
      |                            |                         |
      |                            |-- Is conclusion == "success"?
      |                            |-- YES: Clear old state & Raise 404
      v                            v                         v
[ShieldCheck Banner:               |                         |
 "System Fully Healthy"]           |<-- 404 (Success clear) -|
      |                            |                         |
      |                            |-- NO: conclusion == "failure"?
      |                            |-- Load reports/ai_diagnosis.json
      v                            v                         v
[Show Gemini Root Cause &          |                         |
 Suggested Remediations]           |<-- 200 (Active Failure)-|
```

### Loop Mechanics
1. **Request Ingestion**: When the user loads or refreshes the AI Analysis page, a request is made to `/api/v1/ai/latest-diagnosis`.
2. **Workflow Check**: The backend calls `GitHubService.get_workflow_runs()` to fetch the latest pipeline executions on GitHub (or mock datasets in dev).
3. **Synchronization Check**:
   - **Build Succeeded**: If the latest run's conclusion is `success`, the agent immediately knows the codebase is healthy. It suppresses and ignores any historical `ai_diagnosis.json` logs on the disk and returns `404 Not Found` with the detail: `"No active failures detected. The latest workflow run succeeded."` The frontend captures this and renders a beautiful green **"System Fully Healthy"** banner.
   - **Build Failed**: If the latest run did indeed fail, the agent reads `reports/ai_diagnosis.json` from the disk, serving the detailed Gemini root-cause analysis and code suggestion. The frontend renders the complete interactive AI diagnostic suite.

---

## 3. Hardened Security & Isolation Model

AutoHeal implements a "Defense in Depth" strategy inside the CI/CD pipeline and the running containers:

### CI/CD Security Gating
1. **SAST (Static Application Security Testing)**: Bandit scans the Python codebase for vulnerabilities like dangerous SQL/command concatenations, insecure defaults, or raw `assert` statements.
2. **SCA (Software Composition Analysis)**: `pip-audit` checks `requirements.txt` packages against active CVE databases to prevent supply-chain attacks.
3. **Container Scanning**: Trivy performs dual checks—scanning the filesystem pre-build and the final Docker image post-build. Pipeline execution terminates on any High or Critical vulnerability.

### Distroless Container Hardening
The production application container utilizes a shell-less **Chainguard Distroless Python** base runtime:
- **Zero OS binaries**: There is no `/bin/sh`, `/bin/bash`, or `/bin/ls` inside the runtime container, completely neutralizing whole categories of command injection attacks.
- **No Package Managers**: `apk`, `apt`, and `pip` are absent, making it impossible for unauthorized processes to fetch external payloads.
- **Non-Root Execution**: Runs under UID `65532` (`nonroot`), protecting the host kernel from potential namespace escape exploits.

---

## 4. High-Fidelity Observability & Cardinality Control

### Metric Collection
FastAPI exposes runtime performance data via Prometheus at `/metrics`:
- `http_requests_total`: Tracks raw throughput categorized by path, method, and HTTP status code.
- `http_request_duration_seconds`: Histogram of response times to spot latency degradations.

### Path Normalization (Preventing Cardinality Explosion)
To prevent dynamic endpoints (e.g. `/api/v1/scans/123`, `/api/v1/scans/456`) from generating thousands of unique timeseries metrics in Prometheus (known as **Cardinality Explosion**), custom middleware normalizes dynamic routes into a generic format (e.g. `/api/v1/scans/{id}`).

### Request Correlation
- Custom middleware injects a unique `X-Request-ID` UUID into every incoming request.
- This ID is automatically injected into all JSON logs printed to `stdout` and returned in HTTP headers.
- Developers can select a latency spike in Grafana, copy the `request_id`, and query Loki logs to instantly isolate the exact log trace across multi-container flows.

---

[Back to README](../README.md)
