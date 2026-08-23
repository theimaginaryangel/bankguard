"use client";

import { useEffect, useState, useRef } from "react";
import { fetchFindings, uploadFileSecurely, checkJobStatus } from "@/lib/api";

export default function FraudPage() {
  const [findings, setFindings] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState("");
  const [jobId, setJobId] = useState("");

  useEffect(() => {
    async function load() {
      const data = await fetchFindings("FRAUD");
      setFindings(data);
      setLoading(false);
    }
    load();
  }, []);

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      const status = await checkJobStatus(jobId);
      if (status) {
        const processed = Number(status.processedBytes || 0);
        const total = Number(status.totalBytes || 1);
        const percent = Math.round((processed / total) * 100);
        setProcessingProgress(percent);
        
        if (status.status === "COMPLETED" || percent >= 100) {
          setProcessingStatus(`Backend Processing Complete! (100%)`);
          clearInterval(interval);
          setJobId("");
          
          // Reload the table so the user sees the new findings!
          const data = await fetchFindings("FRAUD");
          setFindings(data);
        } else {
          setProcessingStatus(`Backend Processing... ${percent}%`);
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    
    const file = e.target.files[0];
    if (!file.name.endsWith('.csv')) {
      setUploadStatus("Error: Only .csv files are allowed!");
      return;
    }
    if (file.size > 1073741824) {
      setUploadStatus("Error: File is too large (Max 1GB)!");
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadStatus("Getting secure ticket & uploading to S3...");
    
    const success = await uploadFileSecurely(file, (percent) => {
      setUploadProgress(percent);
      setUploadStatus(`Uploading... ${percent}%`);
    });
    
    if (success) {
      setUploadStatus("Upload successful! Triggering backend processor...");
      setUploadProgress(100);
      
      // Start polling the backend process!
      setProcessingStatus("Initializing backend processor...");
      setProcessingProgress(0);
      setJobId(file.name); // The S3 key is "uploads/filename", so the handler uses filename as Job ID

      if (fileInputRef.current) fileInputRef.current.value = "";
    } else {
      setUploadStatus("Error: Upload failed or rejected by S3.");
      setUploadProgress(0);
    }
    setUploading(false);
  };

  if (loading) return <div className="text-sm font-mono tracking-widest text-zinc-500 uppercase animate-pulse">Loading fraud data...</div>;

  return (
    <div className="space-y-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between space-y-4 md:space-y-0">
        <div className="space-y-4">
          <h1 className="text-3xl font-light tracking-wide text-white">Fraud Monitor</h1>
          <p className="text-lg font-light text-zinc-400 max-w-2xl leading-relaxed">
            Transactional anomaly detection powered by Isolation Forest.
          </p>
        </div>
        
        {/* Upload Zone */}
        <div className="bg-[#0a0a0a] border border-zinc-800 p-4 rounded-xl min-w-[300px]">
          <h3 className="text-[10px] font-mono text-zinc-500 tracking-widest uppercase mb-3">Upload Transaction Batch (CSV)</h3>
          <input 
            type="file" 
            accept=".csv"
            ref={fileInputRef}
            onChange={handleUpload}
            disabled={uploading}
            className="block w-full text-sm text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-mono file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 disabled:opacity-50 transition-colors"
          />
          {uploadProgress > 0 && (
            <div className="mt-3 w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
              <div 
                className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          )}
          {uploadStatus && (
            <p className={`mt-2 text-xs font-mono tracking-wide ${uploadStatus.includes("Error") ? "text-red-400" : "text-emerald-400"}`}>
              {uploadStatus}
            </p>
          )}

          {/* Backend Processing Status */}
          {jobId && (
            <div className="mt-4 pt-4 border-t border-zinc-800">
              <h3 className="text-[10px] font-mono text-zinc-500 tracking-widest uppercase mb-3">AI Processing Status</h3>
              <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${processingProgress}%` }}
                ></div>
              </div>
              <p className="mt-2 text-xs font-mono tracking-wide text-indigo-400">
                {processingStatus}
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-[#0a0a0a] overflow-x-auto shadow-2xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-zinc-900/80 border-b border-zinc-800 font-mono text-[10px] tracking-widest text-zinc-500 uppercase">
              <th className="p-6 font-medium">Severity</th>
              <th className="p-6 font-medium">Transaction ID</th>
              <th className="p-6 font-medium">Amount</th>
              <th className="p-6 font-medium">Risk Score</th>
              <th className="p-6 font-medium">Anomaly Context</th>
            </tr>
          </thead>
          <tbody>
            {findings.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-10 text-center text-zinc-500 font-light">
                  No anomalous activity detected.
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
                  <td className="p-6">
                    <div className="font-mono text-sm text-zinc-300 truncate max-w-[150px]" title={f.fraudDetails?.transactionId}>
                      {f.fraudDetails?.transactionId}
                    </div>
                    <div className="text-[10px] font-mono text-zinc-600 mt-2 uppercase tracking-wide">{new Date(f.createdAt).toLocaleString()}</div>
                  </td>
                  <td className="p-6 font-light text-zinc-200">
                    ${f.fraudDetails?.amount}
                  </td>
                  <td className="p-6">
                    <div className="flex items-center">
                      <div className="w-16 bg-zinc-800 rounded-full h-1.5 mr-3 overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            Number(f.fraudDetails?.riskScore) > 0.8 ? 'bg-red-500' : 
                            Number(f.fraudDetails?.riskScore) > 0.5 ? 'bg-orange-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, Number(f.fraudDetails?.riskScore) * 100)}%` }}
                        ></div>
                      </div>
                      <span className="font-mono text-xs text-zinc-400">{Number(f.fraudDetails?.riskScore).toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="p-6 max-w-sm">
                    {/* Triggered Rules */}
                    {f.fraudDetails?.triggeredRules && f.fraudDetails.triggeredRules.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {f.fraudDetails.triggeredRules.map((rule: string) => (
                          <span key={rule} className="px-2 py-1 bg-zinc-800 text-zinc-300 rounded-sm font-mono text-[10px] uppercase tracking-wider">
                            {rule}
                          </span>
                        ))}
                      </div>
                    )}
                    {/* Contributing Features from AI */}
                    {f.fraudDetails?.contributingFeatures && Object.keys(f.fraudDetails.contributingFeatures).length > 0 && (
                      <div className="text-xs text-zinc-500 font-light">
                        <span className="font-mono text-[10px] tracking-widest uppercase text-zinc-600 block mb-2">PCA Deviations</span>
                        <ul className="space-y-1.5">
                          {Object.entries(f.fraudDetails.contributingFeatures).map(([feature, val]) => (
                            <li key={feature} className="flex justify-between border-b border-zinc-800/50 pb-1.5">
                              <span className="font-mono text-zinc-400">{feature}</span>
                              <span className="text-zinc-500">{Number(val).toFixed(2)}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
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
