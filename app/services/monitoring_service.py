import logging
from typing import Dict, Any, List
from prometheus_client import REGISTRY
from app.services.github_service import GitHubService
from app.services.reports_service import ReportsService
from app.config import settings

logger = logging.getLogger("autoheal.monitoring")


class MonitoringService:
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """
        Parses direct in-memory Prometheus telemetry metrics.
        Returns live request counts, error rates, average latency, and in-progress requests.
        """
        total_requests = 0
        total_errors = 0
        latency_sum = 0.0
        latency_count = 0
        requests_inprogress = 0

        # Iterate over all registered Prometheus collectors
        for metric in REGISTRY.collect():
            if metric.name == "http_requests_total":
                for sample in metric.samples:
                    total_requests += int(sample.value)
            elif metric.name == "http_errors_total":
                for sample in metric.samples:
                    total_errors += int(sample.value)
            elif metric.name == "http_requests_inprogress":
                for sample in metric.samples:
                    requests_inprogress += int(sample.value)
            elif metric.name == "http_request_duration_seconds":
                for sample in metric.samples:
                    if sample.name.endswith("_sum"):
                        latency_sum += sample.value
                    elif sample.name.endswith("_count"):
                        latency_count += int(sample.value)

        avg_latency_ms = 0.0
        if latency_count > 0:
            avg_latency_ms = (latency_sum / latency_count) * 1000.0

        error_rate = 0.0
        if total_requests > 0:
            error_rate = (total_errors / total_requests) * 1000.0 / 10.0  # Percentage

        return {
            "status": "Healthy" if total_requests == 0 or error_rate < 5.0 else "Degraded",
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(error_rate, 2),
            "average_latency_ms": round(avg_latency_ms, 2),
            "requests_in_progress": requests_inprogress,
        }

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """
        Aggregates cloud-native monitoring metrics:
        - GitHub Pipeline Health
        - Security Scans Telemetry (Trivy + Bandit)
        - AI Incident Telemetry
        - API Request Performance (Prometheus)
        - Deployment Context
        """
        # 1. Pipeline Health & Incidents from GitHub Workflow runs
        runs_data = GitHubService.get_workflow_runs()
        runs = runs_data.get("runs", [])
        
        total_runs = len(runs)
        success_count = 0
        failure_count = 0
        incidents: List[Dict[str, Any]] = []

        for run in runs:
            conclusion = run.get("conclusion")
            if conclusion == "success":
                success_count += 1
            elif conclusion == "failure":
                failure_count += 1
                incidents.append({
                    "id": run.get("id"),
                    "name": run.get("name"),
                    "conclusion": conclusion,
                    "created_at": run.get("created_at") or run.get("run_started_at"),
                    "url": run.get("html_url")
                })

        success_rate = 100.0
        if (success_count + failure_count) > 0:
            success_rate = (success_count / (success_count + failure_count)) * 100.0

        # 2. Security Scan Telemetry (Trivy + Bandit)
        total_vulnerabilities = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        sast_findings = 0

        # Parse Trivy fs results
        try:
            trivy_data = ReportsService.read_and_validate_report("reports/trivy-results.json")
            if trivy_data and "Results" in trivy_data:
                for target in trivy_data["Results"]:
                    if "Vulnerabilities" in target:
                        for vuln in target["Vulnerabilities"]:
                            total_vulnerabilities += 1
                            sev = str(vuln.get("Severity", "")).upper()
                            if "CRITICAL" in sev:
                                critical_count += 1
                            elif "HIGH" in sev:
                                high_count += 1
                            elif "MEDIUM" in sev:
                                medium_count += 1
                            else:
                                low_count += 1
        except Exception as e:
            logger.debug(f"Could not load Trivy report for monitoring metrics: {str(e)}")

        # Parse Bandit SAST results
        try:
            bandit_data = ReportsService.read_and_validate_report("reports/bandit-results.sarif")
            if bandit_data and "runs" in bandit_data and len(bandit_data["runs"]) > 0:
                results = bandit_data["runs"][0].get("results", [])
                sast_findings = len(results)
        except Exception as e:
            logger.debug(f"Could not load Bandit report for monitoring metrics: {str(e)}")

        # 3. AI Incident Telemetry
        active_diagnoses = 1 if failure_count > 0 and len(incidents) > 0 and incidents[0]["id"] == (runs[0].get("id") if runs else None) else 0
        
        # 4. Aggregated Prometheus request metrics
        api_metrics = cls.get_system_metrics()

        # 5. Pipeline overall status
        pipeline_status = "Healthy"
        if failure_count > 0:
            pipeline_status = "Action Required" if runs and runs[0].get("conclusion") == "failure" else "Warning"

        return {
            "pipeline_health": {
                "success_rate": round(success_rate, 2),
                "total_runs": total_runs,
                "success_count": success_count,
                "failure_count": failure_count,
                "status": pipeline_status,
            },
            "security_telemetry": {
                "total_vulnerabilities": total_vulnerabilities,
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count,
                "sast_findings": sast_findings,
                "status": "Healthy" if total_vulnerabilities == 0 and sast_findings == 0 else "Action Required" if critical_count + high_count > 0 else "Warning",
            },
            "ai_telemetry": {
                "active_diagnoses": active_diagnoses,
                "last_diagnosis_status": "Active failure analysis running" if active_diagnoses > 0 else "System fully operational",
            },
            "api_metrics": api_metrics,
            "recent_incidents": incidents[:5],  # Limit to latest 5 failures
            "deployment_status": {
                "environment": settings.environment,
                "status": "Active",
            }
        }
