'use client';

const PRESETS = [1, 7, 30, 90];

interface Props {
  value: number;
  onChange: (days: number) => void;
}

export function TimeSlider({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-md px-3 py-2 text-xs">
      <span className="text-gray-500 font-medium">Pumping time:</span>
      {PRESETS.map((d) => (
        <button
          key={d}
          onClick={() => onChange(d)}
          className={`px-2.5 py-1 rounded ${
            value === d ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          {d}d
        </button>
      ))}
    </div>
  );
}
