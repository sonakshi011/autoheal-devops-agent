# Recruiter & Technical Interview Q&As

This document compiles high-level systems design and engineering Q&As covering the final deployed production architecture of the **AutoHeal DevOps Agent** platform. Use this guide to prepare for Senior DevOps, Cloud, and AI Platform Engineering portfolio reviews.

---

### Q1: How did you solve persistent storage limitations for report documents in ephemeral container environments?
**Answer**: 
*   **The Challenge**: In serverless edge (Vercel) and stateless container (Render) environments, the local filesystem is ephemeral. Any security report or AI diagnosis generated disappears instantly when the container scales or restarts.
*   **The Design**: We implemented a **Git-as-a-Ledger reports synchronization strategy**. We decoupled heavy audits into GitHub Actions runners and configured them to commit the generated scan JSONs/SARIFs directly to a dedicated, stateless `reports` git branch (`reports/latest/*`).
*   **The Ingestion**: The FastAPI backend dynamically fetches these JSON payloads directly via GitHub contents REST APIs. This completely eliminates database licensing, maintenance, or S3 bucket operational costs, while providing **native versioning, immutability, and 100% free persistence**.

---

### Q2: How does the platform avoid Out-Of-Memory (OOM) crashes on 512MB RAM free-tier cloud limits?
**Answer**:
*   **The Challenge**: Running standard Prometheus database servers, Loki log servers, Promtail daemons, and Grafana kiosks eats up over 1.5GB of RAM, immediately triggering container OOM (Out-Of-Memory) kills on free-tier limits.
*   **The Design**: We engineered an **In-Memory Prometheus Registry Scraper** inside FastAPI using `prometheus_client`. The backend tracks HTTP request counts, durations, and status codes directly inside FastAPI memory space.
*   **The Scraper**: When the client fetches `/api/v1/monitoring/summary`, the backend queries `REGISTRY.collect()` on-demand, doing a sub-second calculation and returning real-time latency stats in milliseconds with **absolutely zero disk operations or running database sidecars**.

---

### Q3: How do you prevent hitting GitHub Actions API rate-limits during rapid client refreshes?
**Answer**:
*   **The Design**: We implemented a **Memory TTL Cache (90 Seconds)** inside our `ReportsService`. 
*   **The Cache**: When a client requests a security scan or AI diagnosis report, the FastAPI backend checks if an active cache entry exists and is less than 90 seconds old. If yes, it serves the cached JSON instantly. 
*   **The Fallback**: If the cache expires but a GitHub API lookup temporarily fails or rate-limits, the backend gracefully serves the **last successfully cached response (stale-while-revalidate degraded mode)** instead of crashing with unhandled exceptions.

---

### Q4: How is the backend container secured against interactive terminal attacks?
**Answer**:
*   **The Design**: The API Docker image is compiled using a multi-stage build, launching on a hardened **Chainguard Shell-less Distroless Python** base runtime.
*   **The Posture**: Distroless images strip out **100% of standard OS shells (`/bin/sh`, `/bin/bash`), core utils, and package managers (`apk`, `apt`, `pip`)**. If an attacker gains unauthorized endpoint access, there is no shell available to execute commands or download malicious payloads. The container also runs under UID `65532` (`nonroot`), protecting host kernels from potential namespace exploits.

---

### Q5: Why did you split frontend and backend deployments across Vercel and Render?
**Answer**:
*   **The Design**: We optimized for specialized cloud runtimes. 
*   **Frontend (Vercel)**: Leverages Serverless Edge delivery for instantaneous, globally-cached React client rendering.
*   **Backend (Render)**: Runs a persistent, multi-threaded FastAPI web service, which allows the ASGI event loop to handle continuous traffic, manage backend memory TTL caches, and expose Swagger API controllers securely.
