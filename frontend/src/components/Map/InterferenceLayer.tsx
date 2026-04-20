'use client';

import { useMemo } from "react";
import { Source, Layer } from "react-map-gl/maplibre";
import type { WellsGeoJSON } from "@/types";
import type { FeatureCollection, LineString } from "geojson";

interface Props {
  wellsGeoJSON: WellsGeoJSON;
}

const INTERFERENCE_RADIUS_KM = 2;

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function InterferenceLayer({ wellsGeoJSON }: Props) {
  const linesGeoJSON = useMemo<FeatureCollection<LineString>>(() => {
    const features: FeatureCollection<LineString>["features"] = [];
    const wells = wellsGeoJSON.features;

    for (let i = 0; i < wells.length; i++) {
      for (let j = i + 1; j < wells.length; j++) {
        const [lon1, lat1] = wells[i].geometry.coordinates;
        const [lon2, lat2] = wells[j].geometry.coordinates;
        const dist = haversineKm(lat1, lon1, lat2, lon2);

        if (dist < INTERFERENCE_RADIUS_KM) {
          const bothActive = wells[i].properties.status === "active" && wells[j].properties.status === "active";
          const totalYield = wells[i].properties.current_yield_ls + wells[j].properties.current_yield_ls;

          features.push({
            type: "Feature",
            geometry: {
              type: "LineString",
              coordinates: [[lon1, lat1], [lon2, lat2]],
            },
            properties: {
              well_a: wells[i].properties.id,
              well_b: wells[j].properties.id,
              distance_km: Math.round(dist * 100) / 100,
              total_yield: totalYield,
              both_active: bothActive,
              width: Math.max(1, Math.min(4, totalYield / 15)),
            },
          });
        }
      }
    }

    return { type: "FeatureCollection", features };
  }, [wellsGeoJSON]);

  return (
    <Source id="interference-lines" type="geojson" data={linesGeoJSON}>
      <Layer
        id="interference-lines-layer"
        type="line"
        paint={{
          "line-color": ["case", ["get", "both_active"], "#ef4444", "#9ca3af"],
          "line-width": ["get", "width"],
          "line-dasharray": [4, 3],
          "line-opacity": 0.6,
        }}
      />
    </Source>
  );
}
