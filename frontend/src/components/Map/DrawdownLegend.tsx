'use client';

const LEVELS = [
  { color: "#dc2626", label: "5m+ severe" },
  { color: "#f97316", label: "2m" },
  { color: "#eab308", label: "1m" },
  { color: "#84cc16", label: "0.5m" },
];

export function DrawdownLegend({ tDays }: { tDays: number }) {
  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-md px-3 py-2 text-xs">
      <div className="text-gray-500 font-medium mb-1">Drawdown after {tDays}d:</div>
      <div className="flex gap-2">
        {LEVELS.map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-gray-700">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
