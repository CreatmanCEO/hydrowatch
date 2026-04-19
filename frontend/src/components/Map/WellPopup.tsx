'use client';

import { Popup } from "react-map-gl/maplibre";
import type { WellProperties } from "@/types";

interface WellPopupProps {
  properties: WellProperties;
  longitude: number;
  latitude: number;
  onClose: () => void;
}

const statusColors = {
  active: "bg-green-100 text-green-800",
  inactive: "bg-gray-100 text-gray-800",
  maintenance: "bg-yellow-100 text-yellow-800",
};

export function WellPopup({ properties: p, longitude, latitude, onClose }: WellPopupProps) {
  return (
    <Popup
      longitude={longitude}
      latitude={latitude}
      anchor="bottom"
      onClose={onClose}
      closeOnClick={false}
      className="well-popup"
      maxWidth="320px"
    >
      <div className="p-2 text-sm">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold text-base">{p.id}</h3>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[p.status]}`}>
            {p.status}
          </span>
        </div>

        <p className="text-gray-600 mb-2">{p.name_en} &middot; {p.cluster_name}</p>

        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <div>
            <span className="text-gray-500">Depth:</span>{" "}
            <span className="font-medium">{p.well_depth_m}m</span>
          </div>
          <div>
            <span className="text-gray-500">Aquifer:</span>{" "}
            <span className="font-medium">{p.aquifer_type}</span>
          </div>
          <div>
            <span className="text-gray-500">Yield:</span>{" "}
            <span className="font-medium">{p.current_yield_ls} L/s</span>
          </div>
          <div>
            <span className="text-gray-500">WL:</span>{" "}
            <span className="font-medium">{p.static_water_level_m}m</span>
          </div>
          <div>
            <span className="text-gray-500">TDS:</span>{" "}
            <span className="font-medium">{p.last_tds_mgl} mg/L</span>
          </div>
          <div>
            <span className="text-gray-500">pH:</span>{" "}
            <span className="font-medium">{p.last_ph}</span>
          </div>
          <div>
            <span className="text-gray-500">Cl:</span>{" "}
            <span className="font-medium">{p.last_chloride_mgl} mg/L</span>
          </div>
          <div>
            <span className="text-gray-500">Temp:</span>{" "}
            <span className="font-medium">{p.last_temperature_c}°C</span>
          </div>
        </div>

        <div className="mt-2 pt-2 border-t text-xs text-gray-400">
          {p.operator} &middot; Installed {p.installation_date}
        </div>
      </div>
    </Popup>
  );
}
