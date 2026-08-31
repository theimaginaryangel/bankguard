"use client";

import { useEffect, useState } from "react";
import { fetchSummary } from "@/lib/api";
import Link from "next/link";

export default function OverviewPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadStats() {
      try {
        const data = await fetchSummary();
        if (isMounted) {
          if (data) {
            setStats(data);
            setFetchError(null);
          } else {
            setFetchError("Unable to load summary statistics from API.");
          }
        }
      } catch {
        if (isMounted) {
          setFetchError("Connection error while loading telemetry data.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadStats();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center text-zinc-500">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-800 border-t-red-600"></div>
          <p className="text-sm font-mono tracking-widest uppercase">Loading System Data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      
      <div className="space-y-4">
        <h1 className="text-3xl font-light tracking-wide text-white">System Overview</h1>
        <p className="text-lg font-light text-zinc-400 max-w-2xl leading-relaxed">
          Unified telemetry covering cloud configuration state and transactional anomaly detection.
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Card 1 - Critical Fraud (Red = Danger) */}
        <div className="relative flex flex-col h-full p-6 overflow-hidden rounded-2xl bg-[#0a0a0a] border border-zinc-800 transition-all duration-500 hover:border-red-500/50 hover:shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:-translate-y-1">
          <h3 className="font-mono text-[10px] tracking-widest text-zinc-500 uppercase">Critical Frauds</h3>
          <p className="text-4xl font-light text-red-500 mt-4">
            {stats ? (stats?.FRAUD?.CRITICAL || 0) : "-"}
          </p>
        </div>

        {/* Card 2 - Critical Compliance (Red = Danger) */}
        <div className="relative flex flex-col h-full p-6 overflow-hidden rounded-2xl bg-[#0a0a0a] border border-zinc-800 transition-all duration-500 hover:border-red-500/50 hover:shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:-translate-y-1">
          <h3 className="font-mono text-[10px] tracking-widest text-zinc-500 uppercase">Critical Misconfigs</h3>
          <p className="text-4xl font-light text-red-500 mt-4">
            {stats ? (stats?.COMPLIANCE?.CRITICAL || 0) : "-"}
          </p>
        </div>

        {/* Card 3 - High Risk Fraud (Orange = Warning) */}
        <div className="relative flex flex-col h-full p-6 overflow-hidden rounded-2xl bg-[#0a0a0a] border border-zinc-800 transition-all duration-500 hover:border-orange-500/50 hover:shadow-[0_0_15px_rgba(249,115,22,0.1)] hover:-translate-y-1">
          <h3 className="font-mono text-[10px] tracking-widest text-zinc-500 uppercase">High Risk Frauds</h3>
          <p className="text-4xl font-light text-orange-400 mt-4">
            {stats ? (stats?.FRAUD?.HIGH || 0) : "-"}
          </p>
        </div>

        {/* Card 4 - High Risk Compliance (Orange = Warning) */}
        <div className="relative flex flex-col h-full p-6 overflow-hidden rounded-2xl bg-[#0a0a0a] border border-zinc-800 transition-all duration-500 hover:border-orange-500/50 hover:shadow-[0_0_15px_rgba(249,115,22,0.1)] hover:-translate-y-1">
          <h3 className="font-mono text-[10px] tracking-widest text-zinc-500 uppercase">High Risk Misconfigs</h3>
          <p className="text-4xl font-light text-orange-400 mt-4">
            {stats ? (stats?.COMPLIANCE?.HIGH || 0) : "-"}
          </p>
        </div>

      </div>

      {/* Explanation Area */}
      <div className="border border-zinc-800 p-8 rounded-2xl mt-12 bg-zinc-900/30">
        <h2 className="text-xl font-light text-white">System Architecture</h2>
        <div className="w-8 h-[1px] bg-zinc-700 mt-4 mb-6"></div>
        <p className="text-zinc-400 font-light leading-relaxed mb-6">
          This dashboard converges two distinct backend pipelines into a single pane of glass:
        </p>
        <ul className="list-disc list-inside text-zinc-400 space-y-3 font-light">
          <li><span className="text-zinc-200 font-medium">Compliance Auditor:</span> Serverless execution validating AWS configuration against CIS benchmarks.</li>
          <li><span className="text-zinc-200 font-medium">Fraud Monitor:</span> High-throughput batch processing utilizing Isolation Forest anomaly detection.</li>
        </ul>
        <div className="mt-10 flex space-x-4">
          <Link href="/architecture" className="group relative inline-flex items-center justify-center px-8 py-3 text-sm font-medium tracking-widest uppercase transition-all duration-300 border border-zinc-700 hover:bg-white hover:text-black rounded-sm">
            View Architecture
          </Link>
        </div>
      </div>
      
    </div>
  );
}
