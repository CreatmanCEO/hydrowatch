'use client';

import { useMemo } from "react";
import { Source, Layer } from "react-map-gl/maplibre";
import circle from "@turf/circle";
import type { WellsGeoJSON } from "@/types";
import type { FeatureCollection, Polygon } from "geojson";

interface Props {
  wellsGeoJSON: WellsGeoJSON;
}

const RINGS = 5;

export function DepressionConeLayer({ wellsGeoJSON }: Props) {
  const coneGeoJSON = useMemo<FeatureCollection<Polygon>>(() => {
    const features = wellsGeoJSON.features
      .filter((f) => f.properties.status === "active")
      .flatMap((f) => {
        const [lng, lat] = f.geometry.coordinates;
        // Max cone radius proportional to yield (higher yield = larger cone)
        const maxRadius = 0.3 + (f.properties.current_yield_ls / 30) * 1.5;

        // Generate concentric rings with gradient opacity (dark center → light edge)
        return Array.from({ length: RINGS }, (_, i) => {
          const radius = maxRadius * ((i + 1) / RINGS);
          return circle([lng, lat], radius, {
            steps: 32,
            units: "kilometers",
            properties: {
              well_id: f.properties.id,
              ring: i,
              opacity: 0.15 - i * 0.025, // inner=0.15, outer=0.025
            },
          });
        });
      });

    return {
      type: "FeatureCollection",
      features,
    };
  }, [wellsGeoJSON]);

  return (
    <Source id="depression-cones" type="geojson" data={coneGeoJSON}>
      <Layer
        id="depression-cones-fill"
        type="fill"
        paint={{
          "fill-color": "#3b82f6",
          "fill-opacity": ["get", "opacity"],
        }}
      />
      <Layer
        id="depression-cones-outline"
        type="line"
        filter={["==", ["get", "ring"], RINGS - 1]}
        paint={{
          "line-color": "#3b82f6",
          "line-width": 1,
          "line-dasharray": [3, 2],
          "line-opacity": 0.3,
        }}
      />
    </Source>
  );
}
