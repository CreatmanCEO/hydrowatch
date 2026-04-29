'use client';

import type { InterferencePair } from "@/types";

const SEVERITY_BG: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

export function InterferencePopup({ pair }: { pair: InterferencePair }) {
  const dominantIsA = pair.dominant_well === pair.well_a;

  return (
    <div className="p-2 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono">{pair.well_a}</span>
        <span>↔</span>
        <span className="font-mono">{pair.well_b}</span>
        <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-semibold ${SEVERITY_BG[pair.severity]}`}>
          {pair.severity}
        </span>
      </div>

      <div className="text-xs text-gray-600 mb-2">Distance: {pair.distance_km} km</div>

      <div className="space-y-1 text-xs mb-2">
        <div>
          Drawdown at <span className="font-mono">{pair.well_a}</span>:{" "}
          <span className="font-medium">{Math.round(pair.coef_at_a * 100)}%</span> from B
          {!dominantIsA && pair.coef_at_a > 0.4 ? <span className="text-red-600"> (vulnerable)</span> : null}
        </div>
        <div>
          Drawdown at <span className="font-mono">{pair.well_b}</span>:{" "}
          <span className="font-medium">{Math.round(pair.coef_at_b * 100)}%</span> from A
          {dominantIsA && pair.coef_at_b > 0.4 ? <span className="text-red-600"> (vulnerable)</span> : null}
        </div>
        <div className="text-gray-600">
          Combined drawdown midpoint: <span className="font-medium">{pair.drawdown_midpoint_m} m</span>
        </div>
      </div>

      <div className="text-xs text-gray-700 border-t pt-2">
        <span className="font-semibold">Recommendation:</span> {pair.recommendation}
      </div>
    </div>
  );
}
