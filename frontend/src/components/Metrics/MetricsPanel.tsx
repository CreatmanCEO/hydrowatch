'use client';

import { useEffect, useState } from "react";

interface ModelMetric {
  model: string;
  pool?: string;
  total_cases: number;
  accuracy: number;
  schema_compliance: number;
  latency_p50: number;
  latency_p95: number;
  cost_per_request: number;
  avg_tokens_per_request: number;
  error_rate: number;
}

interface MetricsResponse {
  source: string;
  models: Record<string, ModelMetric>;
}

function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function cost(v: number): string {
  return `$${v.toFixed(5)}`;
}

const poolColors: Record<string, string> = {
  "pool-a": "bg-green-100 text-green-800",
  "pool-a (fallback)": "bg-green-50 text-green-600",
  "pool-b": "bg-blue-100 text-blue-800",
  "pool-b-upgrade": "bg-purple-100 text-purple-800",
};

export function MetricsPanel() {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const fetchMetrics = () => {
    fetch("/api/metrics")
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setError(e.message));
  };

  useEffect(() => { fetchMetrics(); }, []);

  const handleRunEval = async () => {
    setIsRunning(true);
    try {
      await fetch("/api/metrics/run", { method: "POST" });
      // Poll for results after 30s
      setTimeout(() => { fetchMetrics(); setIsRunning(false); }, 30000);
    } catch {
      setIsRunning(false);
    }
  };

  if (error) return <div className="p-4 text-red-500 text-sm">Failed to load metrics: {error}</div>;
  if (!data) return <div className="p-4 text-gray-400 text-sm">Loading metrics...</div>;

  const models = Object.values(data.models);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-lg">Model Evaluation</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 px-2 py-1 bg-gray-100 rounded">
            {data.source === "sample" ? "Sample data" : "Eval run"}
          </span>
          <button
            onClick={handleRunEval}
            disabled={isRunning}
            className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isRunning ? "Running..." : "Run Eval"}
          </button>
        </div>
      </div>

      {/* Comparison table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b text-left text-xs text-gray-500 uppercase">
              <th className="py-2 pr-3">Model</th>
              <th className="py-2 px-2 text-right">Accuracy</th>
              <th className="py-2 px-2 text-right">Schema</th>
              <th className="py-2 px-2 text-right">P50</th>
              <th className="py-2 px-2 text-right">P95</th>
              <th className="py-2 px-2 text-right">Cost/req</th>
              <th className="py-2 px-2 text-right">Errors</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.model} className="border-b hover:bg-gray-50">
                <td className="py-2.5 pr-3">
                  <div className="font-medium text-sm">{m.model.split("/")[1]}</div>
                  {m.pool && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${poolColors[m.pool] || "bg-gray-100"}`}>
                      {m.pool}
                    </span>
                  )}
                </td>
                <td className="py-2 px-2 text-right font-mono">
                  <span className={m.accuracy >= 0.9 ? "text-green-600" : m.accuracy >= 0.8 ? "text-yellow-600" : "text-red-600"}>
                    {pct(m.accuracy)}
                  </span>
                </td>
                <td className="py-2 px-2 text-right font-mono">
                  <span className={m.schema_compliance >= 0.9 ? "text-green-600" : "text-yellow-600"}>
                    {pct(m.schema_compliance)}
                  </span>
                </td>
                <td className="py-2 px-2 text-right font-mono text-gray-600">{m.latency_p50}ms</td>
                <td className="py-2 px-2 text-right font-mono text-gray-600">{m.latency_p95}ms</td>
                <td className="py-2 px-2 text-right font-mono text-gray-600">{cost(m.cost_per_request)}</td>
                <td className="py-2 px-2 text-right font-mono">
                  <span className={m.error_rate === 0 ? "text-green-600" : "text-red-600"}>
                    {pct(m.error_rate)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Key insights */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-3 bg-green-50 rounded-lg">
          <div className="text-green-800 font-medium mb-1">Best Accuracy</div>
          <div className="text-green-600">
            {models.reduce((a, b) => a.accuracy > b.accuracy ? a : b).model.split("/")[1]}
            {" "}&mdash; {pct(Math.max(...models.map((m) => m.accuracy)))}
          </div>
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-blue-800 font-medium mb-1">Fastest (P50)</div>
          <div className="text-blue-600">
            {models.reduce((a, b) => a.latency_p50 < b.latency_p50 ? a : b).model.split("/")[1]}
            {" "}&mdash; {Math.min(...models.map((m) => m.latency_p50))}ms
          </div>
        </div>
        <div className="p-3 bg-yellow-50 rounded-lg">
          <div className="text-yellow-800 font-medium mb-1">Cheapest</div>
          <div className="text-yellow-600">
            {models.reduce((a, b) => a.cost_per_request < b.cost_per_request ? a : b).model.split("/")[1]}
            {" "}&mdash; {cost(Math.min(...models.map((m) => m.cost_per_request)))}
          </div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <div className="text-purple-800 font-medium mb-1">Best Schema</div>
          <div className="text-purple-600">
            {models.reduce((a, b) => a.schema_compliance > b.schema_compliance ? a : b).model.split("/")[1]}
            {" "}&mdash; {pct(Math.max(...models.map((m) => m.schema_compliance)))}
          </div>
        </div>
      </div>

      {/* Pool routing explanation */}
      <div className="text-xs text-gray-400 border-t pt-3">
        <p><strong>Pool A</strong> (simple tasks): Gemini Flash ↔ Cerebras Llama (mutual fallback)</p>
        <p><strong>Pool B</strong> (complex): Haiku 4.5 → Sonnet 4.5 (upgrade for reasoning)</p>
      </div>
    </div>
  );
}
