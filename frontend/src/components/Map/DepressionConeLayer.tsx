'use client';

import { useMemo } from "react";
import { Source, Layer } from "react-map-gl/maplibre";
import circle from "@turf/circle";
import type { WellsGeoJSON } from "@/types";
import type { FeatureCollection, Polygon } from "geojson";

interface Props {
  wellsGeoJSON: WellsGeoJSON;
}

export function DepressionConeLayer({ wellsGeoJSON }: Props) {
  const coneGeoJSON = useMemo<FeatureCollection<Polygon>>(() => {
    const features = wellsGeoJSON.features
      .filter((f) => f.properties.status === "active")
      .map((f) => {
        const [lng, lat] = f.geometry.coordinates;
        // Cone radius proportional to yield (higher yield = larger cone)
        const radiusKm = 0.3 + (f.properties.current_yield_ls / 30) * 1.5;
        const c = circle([lng, lat], radiusKm, {
          steps: 32,
          units: "kilometers",
          properties: {
            well_id: f.properties.id,
            yield_ls: f.properties.current_yield_ls,
          },
        });
        return c;
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
          "fill-opacity": 0.08,
        }}
      />
      <Layer
        id="depression-cones-outline"
        type="line"
        paint={{
          "line-color": "#3b82f6",
          "line-width": 1,
          "line-dasharray": [3, 2],
          "line-opacity": 0.4,
        }}
      />
    </Source>
  );
}
