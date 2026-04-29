'use client';

interface Props {
  value: "selected" | "all";
  onChange: (mode: "selected" | "all") => void;
}

export function ConeModeToggle({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-md px-3 py-2 text-xs">
      <span className="text-gray-500 font-medium">Cones:</span>
      <button
        onClick={() => onChange("selected")}
        className={`px-2.5 py-1 rounded ${
          value === "selected" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        Selected
      </button>
      <button
        onClick={() => onChange("all")}
        className={`px-2.5 py-1 rounded ${
          value === "all" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        All active
      </button>
    </div>
  );
}
