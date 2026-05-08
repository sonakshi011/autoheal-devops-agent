# AutoHeal DevOps Agent

An AI-powered self-healing CI/CD pipeline and DevOps Agent.

## Overview

This project implements an intelligent DevOps agent using the Gemini API.
It integrates with GitHub Actions to provide:
- AI-powered PR Reviews
- AI Failure Diagnosis
- Automated remediation suggestions
- Security scanning and Log Analysis

## Setup

1. Install Python 3.12+
2. Install dependencies: `pip install -r requirements-dev.txt`
3. Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`
4. Run the app: `make dev`

## Deployment

Designed for Docker and free-tier compatibility (AWS Free Tier, Oracle Cloud Always Free).
