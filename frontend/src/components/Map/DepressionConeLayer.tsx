'use client';

import { useEffect, useState } from "react";
import { Source, Layer } from "react-map-gl/maplibre";
import type { Feature, FeatureCollection, MultiPolygon, Polygon, Position } from "geojson";
import type { DrawdownGrid, WellsGeoJSON } from "@/types";

const ISOLINE_PAINT = [
  { level: 0.5, color: "#84cc16", fillOpacity: 0.03, lineOpacity: 0.45 },
  { level: 1.0, color: "#eab308", fillOpacity: 0.05, lineOpacity: 0.55 },
  { level: 2.0, color: "#f97316", fillOpacity: 0.08, lineOpacity: 0.7 },
  { level: 5.0, color: "#dc2626", fillOpacity: 0.12, lineOpacity: 0.85 },
];

const SMOOTH_ITERATIONS = 2;

/** One pass of Chaikin corner-cutting on a closed ring. */
function chaikinPass(ring: Position[]): Position[] {
  if (ring.length < 4) return ring;
  // Drop the closing duplicate so we treat the ring as cyclic.
  const open = ring.slice(0, -1);
  const out: Position[] = [];
  const n = open.length;
  for (let i = 0; i < n; i++) {
    const [x1, y1] = open[i];
    const [x2, y2] = open[(i + 1) % n];
    out.push([x1 * 0.75 + x2 * 0.25, y1 * 0.75 + y2 * 0.25]);
    out.push([x1 * 0.25 + x2 * 0.75, y1 * 0.25 + y2 * 0.75]);
  }
  // Re-close.
  out.push(out[0]);
  return out;
}

function smoothRing(ring: Position[]): Position[] {
  let r = ring;
  for (let i = 0; i < SMOOTH_ITERATIONS; i++) r = chaikinPass(r);
  return r;
}

function smoothGeometry(geom: Polygon | MultiPolygon): Polygon | MultiPolygon {
  if (geom.type === "Polygon") {
    return { type: "Polygon", coordinates: geom.coordinates.map(smoothRing) };
  }
  return {
    type: "MultiPolygon",
    coordinates: geom.coordinates.map((poly) => poly.map(smoothRing)),
  };
}

interface Props {
  wellsGeoJSON: WellsGeoJSON;
  selectedWellId: string | null;
  mode: "selected" | "all";
  tDays: number;
}

export function DepressionConeLayer({ wellsGeoJSON, selectedWellId, mode, tDays }: Props) {
  const [grids, setGrids] = useState<DrawdownGrid[]>([]);

  // Resolve targets once and derive a stable string key so wellsGeoJSON
  // reference churn doesn't refire the fetch.
  const targets =
    mode === "selected"
      ? selectedWellId
        ? [selectedWellId]
        : []
      : wellsGeoJSON.features
          .filter((f) => f.properties.status === "active")
          .map((f) => f.properties.id)
          .sort();
  const targetsKey = targets.join(",");

  useEffect(() => {
    let isCurrent = true;

    if (targets.length === 0) {
      setGrids([]);
      return;
    }

    Promise.all(
      targets.map((wid) =>
        fetch("/api/tools/compute_drawdown_grid", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ well_id: wid, t_days: tDays, extent_km: 7, resolution: 50 }),
        }).then((r) => r.json() as Promise<DrawdownGrid>)
      )
    )
      .then((result) => {
        if (isCurrent) setGrids(result);
      })
      .catch(() => {});

    return () => {
      isCurrent = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- targets read via closure; targetsKey is the stable trigger.
  }, [targetsKey, mode, tDays]);

  if (grids.length === 0) return null;

  return (
    <>
      {ISOLINE_PAINT.map(({ level, color, fillOpacity, lineOpacity }) => {
        const features: Feature<Polygon | MultiPolygon>[] = grids.flatMap((g) => {
          const iso = g.isolines.find((i) => i.level_m === level);
          if (!iso) return [];
          return [
            {
              type: "Feature" as const,
              geometry: smoothGeometry(iso.polygon),
              properties: { well_id: g.well_id, level_m: level },
            },
          ];
        });
        if (features.length === 0) return null;

        const fc: FeatureCollection<Polygon | MultiPolygon> = {
          type: "FeatureCollection",
          features,
        };

        return (
          <Source key={level} id={`drawdown-iso-${level}`} type="geojson" data={fc}>
            <Layer
              id={`drawdown-iso-${level}-fill`}
              type="fill"
              paint={{ "fill-color": color, "fill-opacity": fillOpacity }}
            />
            <Layer
              id={`drawdown-iso-${level}-outline`}
              type="line"
              paint={{
                "line-color": color,
                "line-width": 1.2,
                "line-opacity": lineOpacity,
              }}
            />
          </Source>
        );
      })}
    </>
  );
}
