import os
import json
import time
import requests
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.config import settings

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB safety limit
CACHE_TTL_SECONDS = 90  # 1.5 minutes cache TTL


class MemoryCache:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
        return None

    def get_stale(self, key: str) -> Optional[Any]:
        """Gracefully returns the last successfully cached response even if expired."""
        if key in self.cache:
            return self.cache[key]["data"]
        return None

    def set(self, key: str, data: Any):
        self.cache[key] = {"data": data, "timestamp": time.time()}


# Single global instance for lightweight, zero-dependency in-memory caching
reports_cache = MemoryCache()


class ReportsService:
    @staticmethod
    def read_and_validate_report(file_path: str) -> dict:
        """
        Safely validates, parses, and caches JSON/SARIF documents.
        - Under live mode (GitHub settings configured): fetches dynamically from the repository's
          'reports' branch under 'reports/latest/*' using the contents REST API.
        - Under local/mock mode: reads from the local filesystem reports/ directory.
        - Graceful Fallback: returns last successfully cached response if GitHub API rate-limits or fails.
        """
        filename = os.path.basename(file_path)
        token = settings.github_token
        repo_name = settings.github_repository

        # --- LOCAL DEVELOPMENT FALLBACK MODE ---
        if not token or not repo_name:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"Report file {filename} not found.")

            if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Report file {filename} exceeds 5MB size limit.",
                )

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=500,
                    detail=f"Report file {filename} contains malformed JSON.",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to read local report: {str(e)}"
                )

        # --- DEPLOYED CLOUD/LIVE MODE WITH CACHING & GRACEFUL FALLBACK ---
        cache_key = f"github_report:{filename}"

        # 1. Try to serve from active TTL cache to prevent GitHub rate-limiting
        cached_data = reports_cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # 2. Cache expired or missing -> Fetch dynamically from GitHub contents API
        url = f"https://api.github.com/repos/{repo_name}/contents/reports/latest/{filename}?ref=reports"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3.raw"}

        try:
            response = requests.get(url, headers=headers, timeout=10)

            # Handle 404 cleanly (e.g. no scan run has happened yet)
            if response.status_code == 404:
                # If we have a stale version in memory, return it with a warning log,
                # otherwise raise a clean HTTP exception.
                stale_data = reports_cache.get_stale(cache_key)
                if stale_data is not None:
                    return stale_data
                raise HTTPException(
                    status_code=404,
                    detail=f"Report file {filename} not found in repository's reports branch.",
                )

            # Handle other HTTP errors gracefully
            if response.status_code != 200:
                stale_data = reports_cache.get_stale(cache_key)
                if stale_data is not None:
                    return stale_data
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch report {filename} from GitHub (Status {response.status_code}).",
                )

            # Limit dynamic payload size to 5MB
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Report file {filename} exceeds 5MB size limit.",
                )

            parsed_data = response.json()

            # Cache successfully fetched response
            reports_cache.set(cache_key, parsed_data)
            return parsed_data

        except HTTPException:
            # Re-raise explicit HTTP exceptions if no stale fallback is available
            raise
        except json.JSONDecodeError:
            stale_data = reports_cache.get_stale(cache_key)
            if stale_data is not None:
                return stale_data
            raise HTTPException(
                status_code=500,
                detail=f"Report file {filename} fetched from GitHub contains malformed JSON.",
            )
        except Exception as e:
            # Graceful Fallback: Use last successfully cached response if network fails
            stale_data = reports_cache.get_stale(cache_key)
            if stale_data is not None:
                return stale_data
            raise HTTPException(
                status_code=500,
                detail=f"Failed to dynamically fetch report {filename} from GitHub: {str(e)}",
            )
