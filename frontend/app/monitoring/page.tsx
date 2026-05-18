"use client";

import { useEffect, useState, startTransition } from "react";
import { 
  Activity, 
  RefreshCw, 
  AlertCircle, 
  ShieldAlert, 
  Zap, 
  Heart, 
  Cpu, 
  CheckCircle2, 
  XCircle, 
  GitBranch, 
  Server,
  Terminal,
  ExternalLink
} from "lucide-react";
import { fetchFromBackend } from "@/lib/api";

interface MonitoringSummary {
  pipeline_health: {
    success_rate: number;
    total_runs: number;
    success_count: number;
    failure_count: number;
    status: string;
  };
  security_telemetry: {
    total_vulnerabilities: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    sast_findings: number;
    status: string;
  };
  ai_telemetry: {
    active_diagnoses: number;
    last_diagnosis_status: string;
  };
  api_metrics: {
    status: string;
    total_requests: number;
    total_errors: number;
    error_rate: number;
    average_latency_ms: number;
    requests_in_progress: number;
  };
  recent_incidents: Array<{
    id: number;
    name: string;
    conclusion: string;
    created_at: string;
    url?: string;
  }>;
  deployment_status: {
    environment: string;
    status: string;
  };
}

export default function MonitoringPage() {
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchSummary = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    const res = await fetchFromBackend<MonitoringSummary>("/api/v1/monitoring/summary");
    if (res.success) {
      setSummary(res.data);
      setError(null);
    } else {
      setError(res.error || "Failed to retrieve monitoring summary.");
    }
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(() => fetchSummary(), 10000); // Auto-refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    startTransition(() => {
      fetchSummary(true);
    });
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-8 w-48 bg-zinc-800 rounded"></div>
            <div className="h-4 w-96 bg-zinc-800 rounded"></div>
          </div>
          <div className="h-9 w-28 bg-zinc-800 rounded"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-zinc-900 border border-zinc-800 rounded-xl"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-96 bg-zinc-900 border border-zinc-800 rounded-xl"></div>
          <div className="h-96 bg-zinc-900 border border-zinc-800 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Monitoring</h1>
            <p className="text-sm text-zinc-400">Exposing real-time cloud operational statistics.</p>
          </div>
          <button
            onClick={handleManualRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-lg border border-[#27272a] text-xs font-semibold transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span>Retry</span>
          </button>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 flex flex-col items-center justify-center text-center gap-3">
          <AlertCircle className="w-12 h-12 text-red-400" />
          <h3 className="text-lg font-semibold text-white">Unable to Load Telemetry Summary</h3>
          <p className="text-sm text-zinc-400 max-w-md">{error || "Connection timed out or backend API is unreachable."}</p>
        </div>
      </div>
    );
  }

  const { pipeline_health, security_telemetry, ai_telemetry, api_metrics, recent_incidents, deployment_status } = summary;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Monitoring</h1>
          <p className="text-sm text-zinc-400">Real-time cloud metrics, latency trackers, security telemetry, and pipeline health.</p>
        </div>
        <button
          onClick={handleManualRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-lg border border-[#27272a] text-xs font-semibold transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          <span>Force Refresh</span>
        </button>
      </div>

      {/* Top metrics grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Core Uptime / Environment */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Uptime & Status</span>
            <Heart className="w-4 h-4 text-rose-500 fill-rose-500 animate-pulse" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">{api_metrics.status}</span>
            <span className="text-xs text-zinc-500">API Gateway</span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-[10px] text-zinc-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>Env: {deployment_status.environment}</span>
          </div>
        </div>

        {/* Total API Requests */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Requests Total</span>
            <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">{api_metrics.total_requests.toLocaleString()}</span>
            <span className="text-xs text-zinc-500">Calls</span>
          </div>
          <div className="mt-2 text-[10px] text-zinc-500 flex justify-between">
            <span>In-Progress: {api_metrics.requests_in_progress}</span>
            <span>Real-time Scraped</span>
          </div>
        </div>

        {/* Avg Latency */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Average Latency</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">{api_metrics.average_latency_ms} ms</span>
            <span className="text-xs text-zinc-500">SLO 500ms</span>
          </div>
          <div className="mt-2 text-[10px] text-zinc-500">
            <span>Histogram percentile distribution</span>
          </div>
        </div>

        {/* Error Rate */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">API Error Rate</span>
            <AlertCircle className={`w-4 h-4 ${api_metrics.error_rate > 0 ? "text-red-400" : "text-emerald-400"}`} />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">{api_metrics.error_rate}%</span>
            <span className="text-xs text-zinc-500">5xx responses</span>
          </div>
          <div className="mt-2 text-[10px] text-zinc-500 flex justify-between">
            <span>Failures: {api_metrics.total_errors}</span>
            <span>Target &lt; 1%</span>
          </div>
        </div>
      </div>

      {/* Main Grid Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline & Incident Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pipeline Health */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-bold text-white">CI/CD Pipeline Operational State</h2>
              </div>
              <span className={`px-2.5 py-1 text-xs font-bold uppercase rounded-lg border ${
                pipeline_health.status === "Healthy" 
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                  : "bg-amber-500/10 text-amber-400 border-amber-500/20"
              }`}>
                {pipeline_health.status}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <span className="text-xs text-zinc-500">Workflow Success Rate</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">{pipeline_health.success_rate}%</span>
                </div>
                {/* Custom Progress Bar */}
                <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
                    style={{ width: `${pipeline_health.success_rate}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-xs text-zinc-500">Pipeline Execution Balance</span>
                <div className="flex gap-4 pt-1">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span className="text-sm font-semibold text-white">{pipeline_health.success_count} Passed</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <XCircle className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-semibold text-white">{pipeline_health.failure_count} Failed</span>
                  </div>
                </div>
                <div className="text-[10px] text-zinc-500 pt-1">
                  Out of {pipeline_health.total_runs} historical runs audited
                </div>
              </div>

              {/* Active AI Status Panel */}
              <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                ai_telemetry.active_diagnoses > 0 
                  ? "bg-red-500/5 border-red-500/10 animate-pulse" 
                  : "bg-emerald-500/5 border-emerald-500/10"
              }`}>
                <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">AI Analyzer Orchestrator</span>
                <span className="text-xs font-semibold text-zinc-200 mt-1">{ai_telemetry.last_diagnosis_status}</span>
                <div className="flex items-center gap-1 mt-2 text-[9px] text-zinc-500">
                  <span className={`w-1.5 h-1.5 rounded-full ${ai_telemetry.active_diagnoses > 0 ? "bg-red-500" : "bg-emerald-500"}`}></span>
                  <span>Sync active</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Incidents Table */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-red-400" />
                <h2 className="text-lg font-bold text-white">Recent Pipeline Failures & Incidents</h2>
              </div>
              <span className="text-xs text-zinc-500 font-mono">{recent_incidents.length} Detected</span>
            </div>

            {recent_incidents.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 border border-dashed border-zinc-900 rounded-lg text-center gap-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                <h4 className="text-sm font-bold text-white">No Incidents Detected</h4>
                <p className="text-xs text-zinc-500 max-w-sm">All recent pipeline builds have passed cleanly. AI auto-healer state is fully healthy.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-zinc-900 text-zinc-500 font-medium">
                      <th className="py-2.5">Workflow Name</th>
                      <th className="py-2.5">Incident Time</th>
                      <th className="py-2.5">Build Result</th>
                      <th className="py-2.5 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {recent_incidents.map((incident) => (
                      <tr key={incident.id} className="hover:bg-zinc-900/50 transition-colors">
                        <td className="py-3 font-semibold text-zinc-200 flex items-center gap-1.5">
                          <Terminal className="w-3.5 h-3.5 text-zinc-500" />
                          <span>{incident.name}</span>
                        </td>
                        <td className="py-3 text-zinc-400">
                          {new Date(incident.created_at).toLocaleString()}
                        </td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 text-[10px] font-bold uppercase text-red-400 bg-red-500/10 border border-red-500/20 rounded">
                            FAILED
                          </span>
                        </td>
                        <td className="py-3 text-right">
                          {incident.url ? (
                            <a 
                              href={incident.url} 
                              target="_blank" 
                              rel="noreferrer" 
                              className="inline-flex items-center gap-0.5 text-blue-400 hover:text-blue-300 font-medium transition-colors"
                            >
                              <span>View</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-zinc-600">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Security Scan Telemetry Area */}
        <div className="space-y-6">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
              <span className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-blue-400" />
                <span>Security Scans Telemetry</span>
              </span>
              <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded border ${
                security_telemetry.status === "Healthy"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-red-500/10 text-red-400 border-red-500/20"
              }`}>
                {security_telemetry.status}
              </span>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center bg-zinc-900/40 border border-zinc-900 p-3 rounded-lg">
                <span className="text-xs text-zinc-400">Total Vulnerabilities</span>
                <span className="text-xl font-black text-white">{security_telemetry.total_vulnerabilities}</span>
              </div>

              {/* Severity breakdown */}
              <div className="space-y-2.5 pt-1">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded bg-red-600"></span>
                    <span className="text-zinc-400">Critical Severity</span>
                  </div>
                  <span className="font-bold text-white font-mono">{security_telemetry.critical_count}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded bg-orange-500"></span>
                    <span className="text-zinc-400">High Severity</span>
                  </div>
                  <span className="font-bold text-white font-mono">{security_telemetry.high_count}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded bg-yellow-500"></span>
                    <span className="text-zinc-400">Medium Severity</span>
                  </div>
                  <span className="font-bold text-white font-mono">{security_telemetry.medium_count}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded bg-blue-500"></span>
                    <span className="text-zinc-400">Low Severity</span>
                  </div>
                  <span className="font-bold text-white font-mono">{security_telemetry.low_count}</span>
                </div>
              </div>

              <div className="border-t border-zinc-900 pt-4 flex justify-between items-center text-xs">
                <span className="text-zinc-500 flex items-center gap-1">
                  <GitBranch className="w-3.5 h-3.5 text-zinc-600" />
                  <span>Bandit SAST Findings:</span>
                </span>
                <span className="font-bold text-zinc-300 font-mono">{security_telemetry.sast_findings} Issues</span>
              </div>
            </div>
          </div>

          {/* Running Engine Host */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 space-y-3">
            <span className="text-xs font-bold text-zinc-400 flex items-center gap-2">
              <Server className="w-4 h-4 text-zinc-500" />
              <span>Container Telemetry context</span>
            </span>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              FastAPI core utilizes non-blocking system threads to scrape process metrics, collecting memory spikes and asynchronous socket pools natively.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
