"use client";

import { useEffect, useState } from "react";
import { Shield, ShieldAlert, ShieldCheck, RefreshCw, AlertCircle, ExternalLink, Terminal, Code } from "lucide-react";
import { fetchFromBackend } from "@/lib/api";
import { BanditFinding, TrivyVulnerability } from "@/types/security";

export default function SecurityPage() {
  const [activeTab, setActiveTab] = useState<"trivy" | "bandit">("trivy");
  
  const [trivyData, setTrivyData] = useState<TrivyVulnerability[]>([]);
  const [banditData, setBanditData] = useState<BanditFinding[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  useEffect(() => {
    async function loadScans() {
      setLoading(true);
      setError(null);
      try {
        // Fetch both scans in parallel using Promise.allSettled to be extremely resilient!
        const [trivyRes, banditRes] = await Promise.allSettled([
          fetchFromBackend<any>("/api/v1/scans/trivy"),
          fetchFromBackend<any>("/api/v1/scans/bandit"),
        ]);

        const parsedVulnerabilities: TrivyVulnerability[] = [];
        if (trivyRes.status === "fulfilled" && trivyRes.value.success) {
          const data = trivyRes.value.data;
          if (data?.Results) {
            for (const target of data.Results) {
              if (target.Vulnerabilities) {
                for (const vuln of target.Vulnerabilities) {
                  parsedVulnerabilities.push({
                    id: vuln.VulnerabilityID,
                    pkgName: vuln.PkgName,
                    installedVersion: vuln.InstalledVersion,
                    fixedVersion: vuln.FixedVersion,
                    severity: vuln.Severity,
                    title: vuln.Title,
                    description: vuln.Description,
                    url: vuln.PrimaryURL,
                  });
                }
              }
            }
          }
        }
        setTrivyData(parsedVulnerabilities);

        const parsedFindings: BanditFinding[] = [];
        if (banditRes.status === "fulfilled" && banditRes.value.success) {
          const data = banditRes.value.data;
          if (data?.runs?.[0]?.results) {
            for (const result of data.runs[0].results) {
              const loc = result.locations?.[0]?.physicalLocation;
              parsedFindings.push({
                ruleId: result.ruleId,
                message: result.message?.text || "",
                file: loc?.artifactLocation?.uri || "Unknown",
                line: loc?.region?.startLine || 0,
                severity: result.properties?.issue_severity || "MEDIUM",
                confidence: result.properties?.issue_confidence || "HIGH",
                code: loc?.region?.snippet?.text || "",
              });
            }
          }
        }
        setBanditData(parsedFindings);

        // If both failed (rejected or returned success=false), show global error
        const trivyFailed = trivyRes.status === "rejected" || !trivyRes.value.success;
        const banditFailed = banditRes.status === "rejected" || !banditRes.value.success;
        if (trivyFailed && banditFailed) {
          const trivyErr = (trivyRes.status === "fulfilled" && !trivyRes.value.success) ? trivyRes.value.error : "";
          const banditErr = (banditRes.status === "fulfilled" && !banditRes.value.success) ? banditRes.value.error : "";
          const errMsg = trivyErr || banditErr || "Both Trivy and Bandit scan reports are missing from the reports directory.";
          throw new Error(errMsg);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load security scan details.");
      } finally {
        setLoading(false);
      }
    }
    loadScans();
  }, [refreshKey]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Security Gate</h1>
          <p className="text-sm text-zinc-400">Vulnerability and static analysis audit reports (Trivy & Bandit).</p>
        </div>
        <button
          onClick={() => setRefreshKey((prev) => prev + 1)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-lg border border-[#27272a] text-xs font-semibold transition-all duration-150"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Scan Logs</span>
        </button>
      </div>

      {/* Main security dashboard container */}
      <div className="bg-zinc-950 border border-[#27272a] rounded-xl p-8 space-y-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400 border border-emerald-500/20">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Zero-Vulnerability Enforcement</h2>
            <p className="text-sm text-zinc-400 max-w-xl">
              AutoHeal safeguards build pipelines by auditing containers (Trivy) and python script executions (Bandit) at the PR level.
            </p>
          </div>
        </div>

        {/* Dynamic Tab Filter Bar */}
        <div className="flex border-b border-[#27272a] gap-6 text-sm text-zinc-500">
          <button
            onClick={() => setActiveTab("trivy")}
            className={`pb-3 font-semibold transition-all duration-150 ${
              activeTab === "trivy"
                ? "text-white border-b-2 border-emerald-400"
                : "hover:text-zinc-300 border-b-2 border-transparent"
            }`}
          >
            Trivy Container ({trivyData.length})
          </button>
          <button
            onClick={() => setActiveTab("bandit")}
            className={`pb-3 font-semibold transition-all duration-150 ${
              activeTab === "bandit"
                ? "text-white border-b-2 border-emerald-400"
                : "hover:text-zinc-300 border-b-2 border-transparent"
            }`}
          >
            Bandit SAST ({banditData.length})
          </button>
        </div>

        {loading ? (
          <div className="py-24 text-center text-zinc-500 flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-zinc-600 animate-spin" />
            <p className="text-sm">Retrieving security reports from dedicated backend directory...</p>
          </div>
        ) : error ? (
          <div className="py-16 text-center text-zinc-500 flex flex-col items-center gap-3 border border-dashed border-red-500/20 rounded-xl bg-red-500/5">
            <AlertCircle className="w-10 h-10 text-red-400" />
            <h3 className="font-bold text-white text-sm">Failed to Load Scan Reports</h3>
            <p className="text-xs text-zinc-400 max-w-sm">{error}</p>
          </div>
        ) : activeTab === "trivy" ? (
          trivyData.length === 0 ? (
            <div className="py-24 text-center text-zinc-500 flex flex-col items-center gap-3 border border-dashed border-[#27272a] rounded-lg">
              <ShieldCheck className="w-10 h-10 text-emerald-400" />
              <h3 className="font-bold text-white text-sm">Debian Container Image Clean</h3>
              <p className="text-xs text-zinc-500 max-w-xs">No container vulnerability packages detected by Trivy scanner.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-zinc-400">
                <thead>
                  <tr className="border-b border-[#27272a] text-xs font-semibold uppercase text-zinc-500">
                    <th className="pb-3 pl-4">Vulnerability ID</th>
                    <th className="pb-3">Package</th>
                    <th className="pb-3">Severity</th>
                    <th className="pb-3">Fixed Version</th>
                    <th className="pb-3 pr-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#27272a]/50">
                  {trivyData.map((vuln, i) => (
                    <tr key={i} className="hover:bg-zinc-900/50 transition-colors">
                      <td className="py-4 pl-4 font-semibold text-white flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
                        <span>{vuln.id}</span>
                      </td>
                      <td className="py-4 text-zinc-300">
                        <strong>{vuln.pkgName}</strong> ({vuln.installedVersion})
                      </td>
                      <td className="py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          vuln.severity === "CRITICAL"
                            ? "bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse"
                            : vuln.severity === "HIGH"
                            ? "bg-red-500/10 text-red-400 border border-red-500/20"
                            : vuln.severity === "MEDIUM"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                        }`}>
                          {vuln.severity}
                        </span>
                      </td>
                      <td className="py-4 text-xs font-mono text-zinc-500">{vuln.fixedVersion || "N/A"}</td>
                      <td className="py-4 pr-4 text-right">
                        {vuln.url ? (
                          <a
                            href={vuln.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
                          >
                            <span>Advisory</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        ) : (
                          <span className="text-xs text-zinc-600">No URI</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : (
          banditData.length === 0 ? (
            <div className="py-24 text-center text-zinc-500 flex flex-col items-center gap-3 border border-dashed border-[#27272a] rounded-lg">
              <ShieldCheck className="w-10 h-10 text-emerald-400" />
              <h3 className="font-bold text-white text-sm">Static Python Source Safe</h3>
              <p className="text-xs text-zinc-500 max-w-xs">No raw python issues or security holes identified by Bandit parser.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {banditData.map((finding, i) => (
                <div key={i} className="bg-zinc-900 border border-[#27272a] rounded-xl p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm font-bold text-white">
                      <Terminal className="w-4 h-4 text-amber-400" />
                      <span>{finding.ruleId}</span>
                    </span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      finding.severity === "HIGH"
                        ? "bg-red-500/10 text-red-400 border border-red-500/20"
                        : finding.severity === "MEDIUM"
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                    }`}>
                      {finding.severity} Severity
                    </span>
                  </div>

                  <p className="text-xs text-zinc-400 leading-relaxed">{finding.message}</p>

                  <div className="text-[11px] text-zinc-500 font-semibold flex items-center gap-1">
                    <Code className="w-3.5 h-3.5 text-zinc-600" />
                    <span>File:</span>
                    <span className="text-zinc-300 font-mono">{finding.file}#L{finding.line}</span>
                  </div>

                  {finding.code && (
                    <pre className="bg-black/40 border border-[#27272a] rounded-lg p-3 overflow-x-auto text-[10px] font-mono text-emerald-400">
                      <code>{finding.code}</code>
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
