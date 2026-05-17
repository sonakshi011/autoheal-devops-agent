"use client";

import { useEffect, useState } from "react";
import { BrainCircuit, RefreshCw, AlertCircle, Calendar, ShieldAlert, Cpu, Sparkles, Check, Copy, ShieldCheck } from "lucide-react";
import { fetchFromBackend } from "@/lib/api";
import { AIDiagnosis } from "@/types/analysis";

export default function AIAnalysisPage() {
  const [diagnosis, setDiagnosis] = useState<AIDiagnosis | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    async function loadDiagnosis() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchFromBackend<AIDiagnosis>("/api/v1/ai/latest-diagnosis");
        setDiagnosis(data);
      } catch (err: any) {
        setError(err.message || "No AI diagnosis report is active in the reports directory.");
      } finally {
        setLoading(false);
      }
    }
    loadDiagnosis();
  }, [refreshKey]);

  const copyToClipboard = () => {
    if (diagnosis?.code_suggestion) {
      navigator.clipboard.writeText(diagnosis.code_suggestion);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">AI Analysis</h1>
          <p className="text-sm text-zinc-400">Gemini-driven root cause failure intelligence and code remediation steps.</p>
        </div>
        <button
          onClick={() => setRefreshKey((prev) => prev + 1)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-lg border border-[#27272a] text-xs font-semibold transition-all duration-150"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Analysis</span>
        </button>
      </div>

      {loading ? (
        <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-24 text-center text-zinc-500 flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-zinc-600 animate-spin" />
          <p className="text-sm">Connecting to Gemini AI diagnostic engine...</p>
        </div>
      ) : error ? (
        error.includes("No active failures detected") ? (
          <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-16 text-center text-zinc-500 flex flex-col items-center gap-3 border-dashed border-emerald-500/20 bg-emerald-500/5">
            <ShieldCheck className="w-10 h-10 text-emerald-400" />
            <h3 className="font-bold text-white text-sm">System Fully Healthy</h3>
            <p className="text-xs text-zinc-400 max-w-sm">{error}</p>
          </div>
        ) : (
          <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-16 text-center text-zinc-500 flex flex-col items-center gap-3 border-dashed border-red-500/20 bg-red-500/5">
            <AlertCircle className="w-10 h-10 text-red-400" />
            <h3 className="font-bold text-white text-sm">No Active Failure Log Inspected</h3>
            <p className="text-xs text-zinc-400 max-w-sm">{error}</p>
          </div>
        )
      ) : !diagnosis ? (
        <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-24 text-center text-zinc-500 flex flex-col items-center gap-2 border-dashed">
          <BrainCircuit className="w-8 h-8 text-zinc-600" />
          <p className="text-sm">No AI diagnosis report generated yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Root Cause and Remediation Steps */}
          <div className="lg:col-span-2 space-y-6">
            {/* Diagnosis Core Info */}
            <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-6 space-y-4">
              <div className="flex items-center gap-2 text-purple-400 text-xs font-bold uppercase tracking-wider">
                <Sparkles className="w-4 h-4" />
                <span>Gemini Root Cause Intelligence</span>
              </div>
              <h2 className="text-xl font-bold text-white leading-snug">
                {diagnosis.root_cause}
              </h2>
            </div>

            {/* Remediation Steps Card */}
            <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-6 space-y-4">
              <h3 className="text-lg font-bold text-white">Suggested Remediation Steps</h3>
              <div className="space-y-4">
                {diagnosis.remediation_steps.map((step, i) => (
                  <div key={i} className="flex gap-4 items-start">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono text-xs font-bold shrink-0">
                      {i + 1}
                    </span>
                    <p className="text-sm text-zinc-300 leading-relaxed pt-0.5">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Code Suggestion Panel */}
            {diagnosis.code_suggestion && (
              <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-white">Suggested Patch / Configuration</h3>
                  <button
                    onClick={copyToClipboard}
                    className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 bg-zinc-900 border border-[#27272a] px-3 py-1.5 rounded-lg transition-all duration-150"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Code</span>
                      </>
                    )}
                  </button>
                </div>
                <pre className="bg-black/50 border border-[#27272a] rounded-xl p-4 overflow-x-auto text-xs font-mono text-emerald-400 leading-relaxed">
                  <code>{diagnosis.code_suggestion}</code>
                </pre>
              </div>
            )}
          </div>

          {/* Diagnosis Metadata Sidebar */}
          <div className="space-y-6">
            <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-6 space-y-5">
              <h3 className="text-md font-bold text-white">Incident Details</h3>
              <div className="divide-y divide-[#27272a] space-y-4">
                <div className="pt-2 flex items-center justify-between text-xs">
                  <span className="text-zinc-500 font-semibold flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-zinc-600" />
                    <span>Logged At:</span>
                  </span>
                  <span className="text-zinc-300 font-mono">
                    {new Date(diagnosis.diagnosis_timestamp).toLocaleString()}
                  </span>
                </div>

                <div className="pt-4 flex items-center justify-between text-xs">
                  <span className="text-zinc-500 font-semibold flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-zinc-600" />
                    <span>Severity Status:</span>
                  </span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium uppercase tracking-wider ${
                    diagnosis.severity === "critical"
                      ? "bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse"
                      : diagnosis.severity === "high"
                      ? "bg-red-500/10 text-red-400 border border-red-500/20"
                      : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                  }`}>
                    {diagnosis.severity}
                  </span>
                </div>

                <div className="pt-4 flex items-center justify-between text-xs">
                  <span className="text-zinc-500 font-semibold flex items-center gap-1.5">
                    <Cpu className="w-4 h-4 text-zinc-600" />
                    <span>AI Model:</span>
                  </span>
                  <span className="text-zinc-300 font-semibold">{diagnosis.model_used}</span>
                </div>

                <div className="pt-4 flex items-center justify-between text-xs">
                  <span className="text-zinc-500 font-semibold flex items-center gap-1.5">
                    <BrainCircuit className="w-4 h-4 text-zinc-600" />
                    <span>Confidence Score:</span>
                  </span>
                  <span className="text-purple-400 font-bold">{diagnosis.confidence_score}%</span>
                </div>
              </div>
            </div>

            {/* Informational Warning Banner */}
            <div className="p-4 bg-zinc-950 border border-purple-500/20 rounded-xl bg-purple-500/5 space-y-2">
              <span className="text-xs font-bold text-purple-400 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>INFORMATIONAL ONLY</span>
              </span>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                These suggestions are AI-generated. AutoHeal reports remediations to developers for manual approval to keep workflows secure and fully audited.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
