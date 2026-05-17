# Resume & LinkedIn Project Guide

Highlight your work on the **AutoHeal DevOps Agent** in your resume and professional profiles using these ATS-optimized, high-impact technical statements.

---

## 📄 Resume Project Section

### **AutoHeal DevOps Agent | Full-Stack DevSecOps Platform**
*Self-Healing CI/CD Pipeline & Interactive AI Control Panel* | [Link to Project]

- **Designed and engineered** a responsive, dark-theme-first **Next.js 14 control panel** (App Router, Tailwind CSS, Lucide, and shadcn/ui) that integrates real-time pipeline telemetry, security gates, and AI-driven remediations.
- **Architected** a high-performance **FastAPI backend** utilizing strict route versioning (`/api/v1`) and centralized Success/Error response envelopes, eliminating client-side typing drift and decreasing API integration friction.
- **Developed** a lightweight, real-time **GitHub Actions state synchronization loop** that dynamically queries pipeline conclusions using PyGithub, automatically clearing stale file reports and rendering a green **"System Fully Healthy"** operational screen when builds pass.
- **Implemented** anonymous, secure **Grafana iframe telemetry** inside Next.js using custom container overrides (`GF_SECURITY_ALLOW_EMBEDDING=true` and `GF_AUTH_ANONYMOUS_ENABLED=true`), enabling login-free kiosk dashboards for tracking req/s and log streams.
- **Hardened** the container runtime utilizing multi-stage Docker builds running over shell-less **Chainguard Distroless Python** bases, neutralizing OS command-injection vectors and maintaining a 100% clean CVE profile.
- **Configured** a persistent **Docker bind volume mapping** (`./reports:/app/reports`) that securely exposes dynamically generated filesystem scans and Gemini analysis JSONs to the FastAPI runtime service layer.
- **Engineered** custom path normalizer middleware to convert dynamic routes into static placeholders (e.g., `{id}`), preventing Prometheus cardinality explosion and keeping time-series metrics memory-efficient.

---

## 💼 LinkedIn Project Description

**Project Name**: AutoHeal DevOps Agent  
**Keywords**: DevSecOps, Next.js 14, FastAPI, Docker, Prometheus, Grafana, Loki, Google Gemini AI, Trivy, Container Hardening.

I recently engineered **AutoHeal**, a production-ready, full-stack AI-native DevSecOps platform that bridges the gap between CI/CD failures and developer remediation through an interactive control panel.

### **Core Highlights:**
- **🧠 Interactive AI Control Panel**: Deployed a dark-themed **Next.js 14 App Router** dashboard that integrates real-time pipeline telemetry, security gates, and clipboard-ready AI code suggestions.
- **🔄 Dynamic GitHub Actions Sync**: Built a backend synchronization loop that dynamically queries branch conclusions, clearing out stale log files to show a clean "System Fully Healthy" operational screen when builds pass.
- **🛡️ Multi-Stage Security Gating**: Enforced strict vulnerability scans (Bandit SAST, pip-audit SCA, Trivy FS/Image) that immediately block pipeline progression on High/Critical CVEs.
- **📦 Stripped Distroless Containers**: Hardened the production environment using shell-less **Chainguard Distroless** base runtimes, running natively as a non-root user.
- **📊 Embedded Telemetry Kiosk**: Integrated pre-configured Grafana kiosk dashboards directly inside Next.js, allowing real-time request tracking and Loki log streams.

---

## 🎯 ATS Keywords (Applicant Tracking Systems)

DevSecOps, CI/CD Pipeline, Full-Stack Engineering, Next.js 14, React, Tailwind CSS, FastAPI, Python, PyGithub, Google Gemini AI, Prometheus, Grafana, Loki, Promtail, Docker Compose, Multi-stage Builds, Distroless, Container Hardening, Vulnerability Management, Static Application Security Testing (SAST), Software Composition Analysis (SCA), Path Normalization, Request Correlation, Traceability.

---

[Back to README](../README.md)
