"use client";

import { useEffect, useState } from "react";
import { fetchFindings } from "@/lib/api";

export default function CompliancePage() {
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      try {
        const data = await fetchFindings("COMPLIANCE");
        if (isMounted) {
          setFindings(data);
          setFetchError(null);
        }
      } catch {
        if (isMounted) {
          setFetchError("Failed to fetch compliance findings from the backend.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) return <div className="text-sm font-mono tracking-widest text-zinc-500 uppercase animate-pulse">Loading compliance data...</div>;

  return (
    <div className="space-y-12">
      <div className="space-y-4">
        <h1 className="text-3xl font-light tracking-wide text-white">Compliance Findings</h1>
        <p className="text-lg font-light text-zinc-400 max-w-2xl leading-relaxed">
          Automated evaluation against the CIS AWS Foundations Benchmark.
        </p>
      </div>

      {fetchError && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm font-mono flex items-center justify-between">
          <span>{fetchError}</span>
          <button 
            onClick={() => window.location.reload()}
            className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-xs transition-colors uppercase tracking-wider"
          >
            Retry
          </button>
        </div>
      )}

      <div className="rounded-2xl border border-zinc-800 bg-[#0a0a0a] overflow-x-auto shadow-2xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-zinc-900/80 border-b border-zinc-800 font-mono text-[10px] tracking-widest text-zinc-500 uppercase">
              <th className="p-6 font-medium">Severity</th>
              <th className="p-6 font-medium">Control ID</th>
              <th className="p-6 font-medium">Detail</th>
              <th className="p-6 font-medium">Resource</th>
            </tr>
          </thead>
          <tbody>
            {findings.length === 0 ? (
              <tr>
                <td colSpan={4} className="p-10 text-center text-zinc-500 font-light">
                  {fetchError ? "Unable to load compliance findings." : "No active compliance findings. Infrastructure is secure."}
                </td>
              </tr>
            ) : (
              findings.map((f, i) => (
                <tr key={f.findingId || `compliance-${i}`} className="border-b border-zinc-800 hover:bg-zinc-900/30 transition-colors">
                  <td className="p-6">
                    <span className={`inline-flex items-center justify-center px-3 py-1 rounded-full font-mono text-[10px] tracking-widest uppercase ${
                      f.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                      f.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                      'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                    }`}>
                      {f.severity || "MEDIUM"}
                    </span>
                  </td>
                  <td className="p-6 font-mono text-sm text-zinc-400">
                    {f.complianceDetails?.checkId || "N/A"}
                  </td>
                  <td className="p-6 max-w-md">
                    <p className="font-medium text-zinc-200">{f.title || "Untitled Finding"}</p>
                    <p className="text-sm font-light text-zinc-500 mt-2 leading-relaxed">{f.remediation || "No remediation specified."}</p>
                  </td>
                  <td className="p-6 font-mono text-xs text-zinc-500 truncate max-w-[200px]" title={f.complianceDetails?.resourceId}>
                    {f.complianceDetails?.resourceId || "N/A"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
