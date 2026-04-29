'use client';

import type { DrawdownCard } from "@/types";

export function DrawdownCardView({ card }: { card: DrawdownCard }) {
  const severeCone = card.cone_radius_1m_km > 2;
  return (
    <div className="mt-2 p-3 bg-white rounded border text-xs">
      <div className="font-medium mb-2">
        Depression Cone — <span className="font-mono">{card.well_id}</span>{" "}
        <span className="text-gray-500">({card.t_days}d)</span>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2">
        <div>
          <div className="text-gray-500 text-[10px] uppercase">Max drawdown</div>
          <div className={`font-medium ${card.max_drawdown_m > 5 ? "text-red-600" : "text-gray-800"}`}>
            {card.max_drawdown_m} m
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-[10px] uppercase">1m isoline radius</div>
          <div className={`font-medium ${severeCone ? "text-orange-600" : "text-gray-800"}`}>
            {card.cone_radius_1m_km} km
          </div>
        </div>
      </div>

      {card.interfering_wells.length > 0 && (
        <div className="mb-2">
          <div className="text-gray-500 text-[10px] uppercase mb-1">Interfering wells</div>
          <div className="flex flex-wrap gap-1">
            {card.interfering_wells.map((w) => (
              <span key={w} className="font-mono px-1.5 py-0.5 bg-gray-100 rounded">
                {w}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="text-gray-700 border-t pt-2 mt-2 space-y-1">
        <div>
          <span className="font-semibold">Assessment:</span> {card.assessment}
        </div>
        <div>
          <span className="font-semibold">Recommendation:</span> {card.recommendation}
        </div>
      </div>
    </div>
  );
}
