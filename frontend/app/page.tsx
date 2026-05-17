"use client";

import { useEffect, useState } from "react";
import { Terminal, ShieldCheck, Activity, BrainCircuit, AlertCircle, RefreshCw, ExternalLink } from "lucide-react";
import { fetchFromBackend } from "@/lib/api";
import { PipelineRunsData } from "@/types/github";

export default function Dashboard() {
  const [pipelineData, setPipelineData] = useState<PipelineRunsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchFromBackend<PipelineRunsData>("/api/v1/pipelines/runs");
        if (res.success) {
          setPipelineData(res.data);
        } else {
          setError(res.error || "Failed to connect to AutoHeal core backend.");
        }
      } catch (err: any) {
        setError(err.message || "Failed to connect to AutoHeal core backend.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [refreshKey]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Dashboard</h1>
          <p className="text-sm text-zinc-400">System overview, metrics, and latest active pipeline status.</p>
        </div>
        <button
          onClick={() => setRefreshKey((prev) => prev + 1)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-lg border border-[#27272a] text-xs font-semibold transition-all duration-150"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Pipeline integration status banner */}
      {pipelineData?.is_mock && (
        <div className="flex items-center gap-2 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 p-4 rounded-xl">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
          <span>
            <strong>Local Dev Mock Mode:</strong> GitHub environment credentials are not active. Displaying high-fidelity local pipeline mock data.
          </span>
        </div>
      )}

      {/* Metrics/Stats Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { title: "Health Status", value: "Operational", desc: "API Gateway & Services", icon: ShieldCheck, color: "text-emerald-400" },
          { title: "System Throughput", value: "14.2 req/s", desc: "Last 5m average", icon: Activity, color: "text-blue-400" },
          { title: "AI Diagnostic Readiness", value: "Ready", desc: "Model: gemini-2.5-flash", icon: BrainCircuit, color: "text-purple-400" },
          { title: "Scans Tracked", value: "Bandit & Trivy", desc: "Zero vulnerability gate active", icon: Terminal, color: "text-amber-400" }
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} className="bg-zinc-950 border border-[#27272a] rounded-xl p-6 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">{stat.title}</span>
                <Icon className={`w-4 h-4 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-[11px] text-zinc-500">{stat.desc}</div>
            </div>
          );
        })}
      </div>

      {/* Main Content Area Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Runs Table Card */}
        <div className="lg:col-span-2 bg-zinc-950 border border-[#27272a] rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-bold text-white">Active Runs</h2>
          
          {loading ? (
            <div className="py-24 text-center text-zinc-500 flex flex-col items-center gap-3">
              <RefreshCw className="w-8 h-8 text-zinc-600 animate-spin" />
              <p className="text-sm">Fetching pipeline runs from the backend service...</p>
            </div>
          ) : error ? (
            <div className="py-16 text-center text-zinc-500 flex flex-col items-center gap-3 border border-dashed border-red-500/20 rounded-xl bg-red-500/5">
              <AlertCircle className="w-10 h-10 text-red-400" />
              <h3 className="font-bold text-white text-sm">Failed to Load Runs</h3>
              <p className="text-xs text-zinc-400 max-w-sm">{error}</p>
            </div>
          ) : !pipelineData || pipelineData.runs.length === 0 ? (
            <div className="py-24 text-center text-zinc-500 flex flex-col items-center gap-2 border border-dashed border-[#27272a] rounded-lg">
              <Terminal className="w-8 h-8 text-zinc-600" />
              <p className="text-sm">No workflow runs found in this repository.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-zinc-400">
                <thead>
                  <tr className="border-b border-[#27272a] text-xs font-semibold uppercase text-zinc-500">
                    <th className="pb-3 pl-4">Workflow Name</th>
                    <th className="pb-3">Event</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">Date</th>
                    <th className="pb-3 pr-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#27272a]/50">
                  {pipelineData.runs.map((run) => (
                    <tr key={run.id} className="hover:bg-zinc-900/50 transition-colors">
                      <td className="py-4 pl-4 font-medium text-white flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>{run.name}</span>
                      </td>
                      <td className="py-4 capitalize">{run.event}</td>
                      <td className="py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          run.conclusion === "success"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : run.conclusion === "failure"
                            ? "bg-red-500/10 text-red-400 border border-red-500/20"
                            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                        }`}>
                          {run.conclusion || run.status}
                        </span>
                      </td>
                      <td className="py-4 text-xs text-zinc-500">
                        {run.created_at ? new Date(run.created_at).toLocaleString() : "N/A"}
                      </td>
                      <td className="py-4 pr-4 text-right">
                        <a
                          href={run.html_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
                        >
                          <span>Logs</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* System Health / Summary Sidebar Card */}
        <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-bold text-white">System Security Gate</h2>
          <div className="p-4 bg-zinc-900 rounded-lg border border-[#27272a] space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-400">SAST Scan:</span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
                Active
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-400">Vulnerability Gate:</span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
                Enforced
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-400">AI Self-Healing:</span>
              <span className="text-purple-400 font-semibold">Active</span>
            </div>
          </div>
          <p className="text-xs text-zinc-500 leading-relaxed">
            AutoHeal uses Bandit and Trivy to capture and check codebase violations before triggering the Gemini diagnostic model.
          </p>
        </div>
      </div>
    </div>
  );
}
