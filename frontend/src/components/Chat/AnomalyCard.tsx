'use client';

import type { AnomalyCard as AnomalyCardType } from "@/types";

const severityStyles = {
  critical: "border-red-500 bg-red-50",
  high: "border-orange-500 bg-orange-50",
  medium: "border-yellow-500 bg-yellow-50",
  low: "border-blue-500 bg-blue-50",
};

const severityBadge = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-blue-100 text-blue-800",
};

export function AnomalyCardComponent({ card }: { card: AnomalyCardType }) {
  const changeSign = card.change_pct > 0 ? "+" : "";

  return (
    <div className={`border-l-4 rounded-lg p-3 my-2 ${severityStyles[card.severity]}`}>
      <div className="flex items-center justify-between mb-1">
        <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${severityBadge[card.severity]}`}>
          {card.severity}
        </span>
        <span className="text-xs text-gray-500 font-mono">{card.well_id}</span>
      </div>

      <h4 className="font-semibold text-sm mt-1">{card.title}</h4>
      <p className="text-xs text-gray-600 mt-1">{card.description}</p>

      <div className="flex gap-4 mt-2 text-xs">
        <div>
          <span className="text-gray-500">Current: </span>
          <span className="font-medium">{card.value_current}</span>
        </div>
        <div>
          <span className="text-gray-500">Baseline: </span>
          <span className="font-medium">{card.value_baseline}</span>
        </div>
        <div>
          <span className="text-gray-500">Change: </span>
          <span className={`font-medium ${card.change_pct < 0 ? "text-red-600" : "text-green-600"}`}>
            {changeSign}{card.change_pct}%
          </span>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-gray-200">
        <p className="text-xs text-gray-700">
          <span className="font-medium">Recommendation:</span> {card.recommendation}
        </p>
      </div>
    </div>
  );
}
