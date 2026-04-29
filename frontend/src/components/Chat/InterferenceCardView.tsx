'use client';

import type { InterferenceCard } from "@/types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

export function InterferenceCardView({ card }: { card: InterferenceCard }) {
  return (
    <div className="mt-2 p-3 bg-white rounded border text-xs">
      <div className="font-medium mb-2">Interference Analysis</div>

      <div className="flex gap-2 mb-2 flex-wrap">
        {Object.entries(card.pairs_summary).map(([sev, count]) =>
          count > 0 ? (
            <span key={sev} className={`px-2 py-0.5 rounded-full ${SEVERITY_COLOR[sev]}`}>
              {count} {sev}
            </span>
          ) : null
        )}
      </div>

      {card.top_concerns.length > 0 && (
        <div className="mb-2">
          <div className="text-gray-500 uppercase text-[10px] mb-1">Top concerns</div>
          <ul className="space-y-1">
            {card.top_concerns.map((c, i) => (
              <li key={i} className="border-l-2 border-orange-400 pl-2">
                <span className="font-mono">{c.well_a}</span> ↔{" "}
                <span className="font-mono">{c.well_b}</span>{" "}
                <span className="font-medium">{Math.round(c.coef_max * 100)}%</span>
                <div className="text-gray-600">{c.action}</div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {card.regional_pattern && (
        <div className="text-gray-700 border-t pt-2 mt-2">
          <span className="font-semibold">Pattern:</span> {card.regional_pattern}
        </div>
      )}
    </div>
  );
}
