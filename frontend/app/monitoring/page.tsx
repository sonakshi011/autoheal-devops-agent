"use client";

import { useState } from "react";
import { Activity, RefreshCw, AlertCircle, PlaySquare, Info, ShieldCheck, Heart, Terminal } from "lucide-react";

export default function MonitoringPage() {
  const grafanaUrl = process.env.NEXT_PUBLIC_GRAFANA_URL || "http://localhost:3001";
  
  // High-fidelity pre-configured AutoHeal dashboard embed path
  // Strips sidebar/header using Grafana's native 'kiosk' mode for seamless embedding!
  const embedUrl = `${grafanaUrl}/d/autoheal-overview-v1/autoheal-platform-overview?orgId=1&refresh=5s&theme=dark&kiosk`;

  const [iframeLoaded, setIframeLoaded] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<boolean>(false);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Monitoring</h1>
          <p className="text-sm text-zinc-400">Exposing real-time Prometheus statistics and embedded Grafana operational panels.</p>
        </div>
        <button
          onClick={() => {
            setIframeLoaded(false);
            setLoadError(false);
            setRefreshKey((prev) => prev + 1);
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-lg border border-[#27272a] text-xs font-semibold transition-all duration-150"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Reload Frames</span>
        </button>
      </div>

      {/* Main Monitoring Frame Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Informative Column */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-blue-400 text-xs font-bold uppercase tracking-wider">
              <Activity className="w-4 h-4 animate-pulse" />
              <span>Metrics & Telemetry</span>
            </div>
            
            <p className="text-xs text-zinc-400 leading-relaxed">
              AutoHeal tracks system operations by exporting real-time endpoint latency and memory metrics to Prometheus.
            </p>

            <div className="divide-y divide-[#27272a] space-y-3 pt-2">
              <div className="pt-2 flex items-center justify-between text-xs">
                <span className="text-zinc-500">Telemetry Port:</span>
                <span className="text-zinc-300 font-mono">9090 (Prom)</span>
              </div>
              <div className="pt-3 flex items-center justify-between text-xs">
                <span className="text-zinc-500">Visualization:</span>
                <span className="text-zinc-300 font-mono">3000 (Grafana)</span>
              </div>
              <div className="pt-3 flex items-center justify-between text-xs">
                <span className="text-zinc-500">Logs Collector:</span>
                <span className="text-zinc-300 font-mono">3100 (Loki)</span>
              </div>
            </div>
          </div>

          <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-5 space-y-3">
            <span className="text-xs font-bold text-zinc-400 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Security Telemetry</span>
            </span>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Vulnerability scans and code audit summaries are also integrated with Prometheus metric alerts.
            </p>
          </div>
        </div>

        {/* Embedded Iframe Area */}
        <div className="lg:col-span-3 bg-zinc-950 border border-[#27272a] rounded-xl p-2 h-[680px] relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between px-4 py-2 border-b border-[#27272a] bg-zinc-950/80">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></span>
              <span className="text-xs font-bold text-zinc-400">Live Grafana Telemetry Dashboard</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-semibold font-mono">{grafanaUrl}</span>
          </div>

          {/* Load Alert State if iframe fails or is loading */}
          {!iframeLoaded && !loadError && (
            <div className="absolute inset-0 bg-[#09090b] flex flex-col items-center justify-center gap-3 z-10">
              <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
              <p className="text-sm text-zinc-400">Mounting Grafana dashboard panels...</p>
            </div>
          )}

          {loadError && (
            <div className="absolute inset-0 bg-[#09090b] flex flex-col items-center justify-center gap-4 z-10 px-8 text-center">
              <AlertCircle className="w-12 h-12 text-zinc-500" />
              <h3 className="text-md font-bold text-white">Telemetry Integration Unavailable</h3>
              <p className="text-xs text-zinc-400 max-w-sm">
                Could not connect to the Grafana server. Verify that the Docker Compose stack is running and the Grafana service is exposed.
              </p>
            </div>
          )}

          <iframe
            key={refreshKey}
            src={embedUrl}
            className="w-full flex-1 border-0 rounded-b-lg"
            onLoad={() => setIframeLoaded(true)}
            onError={() => {
              setIframeLoaded(true);
              setLoadError(true);
            }}
          />
        </div>
      </div>
    </div>
  );
}
