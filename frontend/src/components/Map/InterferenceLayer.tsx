'use client';

import { useEffect, useState, useCallback } from "react";
import { Source, Layer, Popup, useMap } from "react-map-gl/maplibre";
import type { MapMouseEvent, MapGeoJSONFeature } from "maplibre-gl";
import type { InterferencePair, InterferenceResult, WellsGeoJSON } from "@/types";
import type { FeatureCollection, LineString, Point } from "geojson";
import { InterferencePopup } from "./InterferencePopup";

interface Props {
  wellsGeoJSON: WellsGeoJSON;
  bbox: [number, number, number, number];
}

const COLOR_LOW = "#16a34a";
const COLOR_MID = "#eab308";
const COLOR_HIGH = "#dc2626";
const HIT_LAYER_ID = "interference-lines-hit";

function colorForCoef(c: number): string {
  if (c >= 0.6) return COLOR_HIGH;
  if (c >= 0.3) return COLOR_MID;
  return COLOR_LOW;
}

export function InterferenceLayer({ wellsGeoJSON, bbox }: Props) {
  const { current: mapRef } = useMap();
  const [data, setData] = useState<InterferenceResult | null>(null);
  const [popup, setPopup] = useState<{ pair: InterferencePair; lng: number; lat: number } | null>(
    null
  );

  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/api/tools/analyze_interference", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bbox, t_days: 30, min_coefficient: 0.1 }),
      signal: ctrl.signal,
    })
      .then((r) => r.json())
      .then((d: InterferenceResult) => setData(d))
      .catch(() => {});
    return () => ctrl.abort();
  }, [bbox]);

  const onLineClick = useCallback(
    (e: MapMouseEvent & { features?: MapGeoJSONFeature[] }) => {
      const f = e.features?.[0];
      if (!f || !data) return;
      const idx = f.properties?.pair_idx as number | undefined;
      if (idx === undefined) return;
      const pair = data.pairs[idx];
      if (!pair) return;
      const { lng, lat } = e.lngLat;
      setPopup({ pair, lng, lat });
      e.originalEvent?.stopPropagation?.();
    },
    [data]
  );

  // Bind layer-scoped click via maplibre native API (react-map-gl <Layer>
  // doesn't forward onClick in this version).
  useEffect(() => {
    const map = mapRef?.getMap();
    if (!map) return;

    const onMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    map.on("click", HIT_LAYER_ID, onLineClick);
    map.on("mouseenter", HIT_LAYER_ID, onMouseEnter);
    map.on("mouseleave", HIT_LAYER_ID, onMouseLeave);
    return () => {
      map.off("click", HIT_LAYER_ID, onLineClick);
      map.off("mouseenter", HIT_LAYER_ID, onMouseEnter);
      map.off("mouseleave", HIT_LAYER_ID, onMouseLeave);
    };
  }, [mapRef, onLineClick]);

  if (!data || data.pairs.length === 0) return null;

  const coords: Record<string, [number, number]> = {};
  for (const f of wellsGeoJSON.features) {
    coords[f.properties.id] = f.geometry.coordinates as [number, number];
  }

  // Single hit-source: one straight LineString per pair, used only for click hit-test.
  const hitLines: FeatureCollection<LineString> = {
    type: "FeatureCollection",
    features: data.pairs
      .filter((p) => coords[p.well_a] && coords[p.well_b])
      .map((p, idx) => ({
        type: "Feature" as const,
        id: idx,
        geometry: {
          type: "LineString" as const,
          coordinates: [coords[p.well_a], coords[p.well_b]],
        },
        properties: {
          severity: p.severity,
          pair_idx: idx,
        },
      })),
  };

  // Per-pair gradient sources (line-gradient stops must be constants — one source per pair).
  const gradientSources = data.pairs
    .filter((p) => coords[p.well_a] && coords[p.well_b])
    .map((p, idx) => ({
      idx,
      data: {
        type: "FeatureCollection" as const,
        features: [
          {
            type: "Feature" as const,
            geometry: {
              type: "LineString" as const,
              coordinates: [coords[p.well_a], coords[p.well_b]],
            },
            properties: {},
          },
        ],
      } as FeatureCollection<LineString>,
      colorA: colorForCoef(p.coef_at_a),
      colorB: colorForCoef(p.coef_at_b),
    }));

  const labels: FeatureCollection<Point> = {
    type: "FeatureCollection",
    features: data.pairs
      .filter((p) => coords[p.well_a] && coords[p.well_b])
      .map((p) => {
        const [lon_a, lat_a] = coords[p.well_a];
        const [lon_b, lat_b] = coords[p.well_b];
        const coefMax = Math.max(p.coef_at_a, p.coef_at_b);
        return {
          type: "Feature" as const,
          geometry: {
            type: "Point" as const,
            coordinates: [(lon_a + lon_b) / 2, (lat_a + lat_b) / 2],
          },
          properties: {
            label: `${Math.round(coefMax * 100)}% / ${p.drawdown_midpoint_m}m`,
            severity: p.severity,
          },
        };
      }),
  };

  return (
    <>
      {/* Per-pair gradient lines (one Source each so line-gradient stops can vary) */}
      {gradientSources.map(({ idx, data: lineData, colorA, colorB }) => (
        <Source
          key={`interference-grad-${idx}`}
          id={`interference-grad-${idx}`}
          type="geojson"
          data={lineData}
          lineMetrics={true}
        >
          <Layer
            id={`interference-grad-${idx}-line`}
            type="line"
            paint={{
              "line-width": 3,
              "line-opacity": 0.9,
              "line-gradient": [
                "interpolate",
                ["linear"],
                ["line-progress"],
                0, colorA,
                0.5, COLOR_MID,
                1, colorB,
              ],
            }}
          />
        </Source>
      ))}

      {/* Single source for click hit-test (wide invisible buffer) */}
      <Source id="interference-hit" type="geojson" data={hitLines}>
        <Layer
          id={HIT_LAYER_ID}
          type="line"
          paint={{ "line-width": 14, "line-color": "#000000", "line-opacity": 0 }}
        />
      </Source>

      <Source id="interference-labels" type="geojson" data={labels}>
        <Layer
          id="interference-labels-symbol"
          type="symbol"
          minzoom={11}
          layout={{
            "text-field": ["get", "label"],
            "text-size": 10,
            "text-offset": [0, 0],
            "text-anchor": "center",
            "text-allow-overlap": true,
          }}
          paint={{
            "text-color": "#1f2937",
            "text-halo-color": "#ffffff",
            "text-halo-width": 1.5,
          }}
        />
      </Source>

      {popup && (
        <Popup
          longitude={popup.lng}
          latitude={popup.lat}
          anchor="bottom"
          onClose={() => setPopup(null)}
          closeOnClick={false}
          maxWidth="360px"
        >
          <InterferencePopup pair={popup.pair} />
        </Popup>
      )}
    </>
  );
}
