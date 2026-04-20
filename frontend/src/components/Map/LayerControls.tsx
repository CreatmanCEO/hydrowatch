'use client';

import { useMapStore } from "@/stores/mapStore";

const LAYERS = [
  { id: "wells", label: "Wells", icon: "⬤" },
  { id: "depression_cones", label: "Depression Cones", icon: "◎" },
  { id: "interference", label: "Interference", icon: "⟷" },
];

export function LayerControls() {
  const { activeLayers, toggleLayer } = useMapStore();

  return (
    <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-sm rounded-lg shadow-md p-3 z-10">
      <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Layers</h4>
      <div className="space-y-1.5">
        {LAYERS.map(({ id, label, icon }) => (
          <label
            key={id}
            className="flex items-center gap-2 cursor-pointer text-sm hover:bg-gray-50 px-1 py-0.5 rounded"
          >
            <input
              type="checkbox"
              checked={activeLayers.includes(id)}
              onChange={() => toggleLayer(id)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-xs">{icon}</span>
            <span>{label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
