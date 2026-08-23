export default function ArchitecturePage() {
  return (
    <div className="space-y-12 max-w-3xl">
      <div className="space-y-4">
        <h1 className="text-3xl font-light tracking-wide text-white">System Architecture</h1>
        <p className="text-lg font-light text-zinc-400 leading-relaxed">
          The underlying cloud infrastructure powering the BankGuard platform.
        </p>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-[#0a0a0a] p-8 md:p-12 space-y-12 text-zinc-400 font-light leading-relaxed">
        
        <div className="space-y-4">
          <p>
            This platform converges two independent backend pipelines into a single, unified read layer.
          </p>
          <p>
            By sharing a common schema design, the presentation layer (this Next.js application) is completely decoupled from the heuristics that generate the data.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-medium text-white mb-6 font-mono tracking-widest uppercase">1. Compliance Auditor</h2>
          <div className="space-y-4 pl-4 border-l border-zinc-800">
            <p>
              An AWS Lambda function triggered on a chron-schedule by EventBridge. It continuously audits the active AWS environment against a curated subset of the <span className="text-zinc-200">CIS AWS Foundations Benchmark</span>.
            </p>
            <p>
              When misconfigurations are detected (e.g., exposed S3 buckets, unencrypted EBS volumes), findings are formatted and persisted to the shared DynamoDB table.
            </p>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-medium text-white mb-6 font-mono tracking-widest uppercase">2. Fraud Monitor</h2>
          <div className="space-y-4 pl-4 border-l border-zinc-800">
            <p>
              A high-throughput batch pipeline processing transactional data drops in an S3 bucket.
            </p>
            <p>
              Each transaction is evaluated by a dual-layer engine:
            </p>
            <ul className="list-disc list-outside ml-4 space-y-2 text-zinc-500">
              <li><strong className="text-zinc-300 font-normal">Heuristic Rules:</strong> Fast evaluation of hard constraints (velocity limits, merchant categorization).</li>
              <li><strong className="text-zinc-300 font-normal">Machine Learning:</strong> An <span className="text-zinc-200">Isolation Forest</span> model trained to detect multi-dimensional anomalies in the PCA space.</li>
            </ul>
            <p>
              Anomalous transactions are persisted to the shared DynamoDB table, with critical incidents immediately dispatched via SNS.
            </p>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-medium text-white mb-6 font-mono tracking-widest uppercase">3. The Shared Data Layer</h2>
          <div className="space-y-4 pl-4 border-l border-zinc-800">
            <p>
              Both pipelines converge on a single DynamoDB table utilizing a <span className="text-zinc-200">Single-Table Design</span>. 
            </p>
            <p>
              This Next.js dashboard requests data through a lightweight API Gateway endpoint (the &quot;Lambda Lith&quot; pattern), ensuring the frontend remains thin, performant, and solely focused on presentation.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
