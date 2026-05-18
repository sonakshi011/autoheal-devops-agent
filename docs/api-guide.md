# REST API Endpoint Specifications

This guide covers the REST API endpoints exposed by the **AutoHeal DevOps Agent** platform core engine. All production API calls are securely processed through the stateless FastAPI gateway deployed on Render.

---

## 🌐 Production API Base URL
All requests must be directed to:
`https://autoheal-api.onrender.com`

*Access the interactive Swagger UI directly in your browser at [https://autoheal-api.onrender.com/docs](https://autoheal-api.onrender.com/docs).*

---

## 🔒 Standard Response Envelopes

To guarantee robust typing in Next.js 15 client models, all FastAPI versioned endpoints strictly return a unified enveloped JSON format.

### 1. Success Response Envelope (`200 OK`)
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-05-18T19:20:00Z"
}
```

### 2. Error Response Envelope (`4xx / 5xx`)
```json
{
  "success": false,
  "error": "Detailed error explanation or resource validation bounds message.",
  "timestamp": "2026-05-18T19:20:00Z"
}
```

---

## 🚦 Endpoints Directory

### 1. Unified Cloud-Native Telemetry Summary
*   **Route**: `GET /api/v1/monitoring/summary`
*   **Description**: Dynamically parses the local Prometheus `REGISTRY` in-memory to collect HTTP requests count, average latencies, and error rates. It also combines pipeline success rates, recent failures from GitHub actions, and Trivy/Bandit security scan vulnerability counts.
*   **Response Data Format**:
    ```json
    {
      "success": true,
      "data": {
        "pipeline_health": {
          "success_rate": 85.71,
          "total_runs": 10,
          "success_count": 6,
          "failure_count": 1,
          "status": "WARNING"
        },
        "security_telemetry": {
          "total_vulnerabilities": 1,
          "critical_count": 0,
          "high_count": 0,
          "medium_count": 1,
          "low_count": 0,
          "sast_findings": 2,
          "status": "WARNING"
        },
        "ai_telemetry": {
          "active_diagnoses": 0,
          "last_diagnosis_status": "System fully operational"
        },
        "api_metrics": {
          "status": "Healthy",
          "total_requests": 140,
          "total_errors": 0,
          "error_rate": 0.0,
          "average_latency_ms": 42.35,
          "requests_in_progress": 1
        },
        "recent_incidents": [
          {
            "id": 1002,
            "name": "CI Pipeline",
            "conclusion": "failure",
            "created_at": "2026-05-18T06:54:41Z",
            "url": "https://github.com/..."
          }
        ],
        "deployment_status": {
          "environment": "production",
          "status": "Active"
        }
      },
      "timestamp": "2026-05-18T19:20:00Z"
    }
    ```

---

### 2. Latest AI Diagnosis
*   **Route**: `GET /api/v1/ai/latest-diagnosis`
*   **Description**: Automatically checks if the latest workflow run on GitHub has succeeded. If yes, it clears the stale fail state and raises a `404 Not Found` (triggering green operational view). If failed, it fetches the raw `ai_diagnosis.json` from the repository's `reports` branch (cached 90s).
*   **Sample Response Data**:
    ```json
    {
      "success": true,
      "data": {
        "incident_details": {
          "logged_at": "2026-05-18T19:00:00Z",
          "severity": "CRITICAL",
          "ai_model": "gemini-2.5-flash",
          "confidence_score": "100%"
        },
        "analysis": "The CI pipeline failed because the 'pytest' module was not found in the Python environment...",
        "suggested_remediations": [
          "Ensure that 'pytest' is listed in requirements.txt",
          "Add 'pip install -r requirements.txt' step inside workflow definition."
        ],
        "suggested_patch": "To fix this, you would typically add 'pytest' to requirements.txt..."
      },
      "timestamp": "2026-05-18T19:20:00Z"
    }
    ```

---

### 3. Bandit SAST Scan Findings
*   **Route**: `GET /api/v1/scans/bandit`
*   **Description**: Fetches and parses the raw Bandit `bandit-results.sarif` report from the `reports` branch.
*   **Response Data**: Standard SARIF JSON document.

---

### 4. Trivy Vulnerability Scan Findings
*   **Route**: `GET /api/v1/scans/trivy`
*   **Description**: Fetches and parses the raw Trivy `trivy-results.json` report from the `reports` branch.
*   **Response Data**: Standard Trivy JSON scan result.
