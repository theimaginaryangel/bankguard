"use client";

import { useEffect, useState } from "react";
import { fetchFindings } from "@/lib/api";

export default function CompliancePage() {
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const data = await fetchFindings("COMPLIANCE");
      setFindings(data);
      setLoading(false);
    }
    load();
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
                  No active compliance findings. Infrastructure is secure.
                </td>
              </tr>
            ) : (
              findings.map((f, i) => (
                <tr key={f.findingId || i} className="border-b border-zinc-800 hover:bg-zinc-900/30 transition-colors">
                  <td className="p-6">
                    <span className={`inline-flex items-center justify-center px-3 py-1 rounded-full font-mono text-[10px] tracking-widest uppercase ${
                      f.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                      f.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                      'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                    }`}>
                      {f.severity}
                    </span>
                  </td>
                  <td className="p-6 font-mono text-sm text-zinc-400">
                    {f.complianceDetails?.checkId}
                  </td>
                  <td className="p-6 max-w-md">
                    <p className="font-medium text-zinc-200">{f.title}</p>
                    <p className="text-sm font-light text-zinc-500 mt-2 leading-relaxed">{f.remediation}</p>
                  </td>
                  <td className="p-6 font-mono text-xs text-zinc-500 truncate max-w-[200px]" title={f.complianceDetails?.resourceId}>
                    {f.complianceDetails?.resourceId}
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
