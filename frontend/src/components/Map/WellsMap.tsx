'use client';

import { useEffect, useCallback, useState } from "react";
import Map, { Source, Layer, NavigationControl, type MapRef, type ViewStateChangeEvent, type MapLayerMouseEvent } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useMapStore } from "@/stores/mapStore";
import { fetchWells } from "@/lib/api";
import type { WellProperties } from "@/types";
import { WellPopup } from "./WellPopup";
import { LayerControls } from "./LayerControls";
import { DepressionConeLayer } from "./DepressionConeLayer";
import { InterferenceLayer } from "./InterferenceLayer";

const MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";

// Data-driven circle color by TDS level
const wellCircleColor: maplibregl.ExpressionSpecification = [
  "interpolate",
  ["linear"],
  ["get", "last_tds_mgl"],
  2000, "#22c55e",  // green: good quality
  4000, "#eab308",  // yellow: moderate
  6000, "#f97316",  // orange: elevated
  8000, "#ef4444",  // red: high TDS
];

// Data-driven circle size by debit
const wellCircleRadius: maplibregl.ExpressionSpecification = [
  "interpolate",
  ["linear"],
  ["get", "current_yield_ls"],
  2, 4,
  15, 8,
  30, 14,
];

// Status-based opacity
const wellCircleOpacity: maplibregl.ExpressionSpecification = [
  "match",
  ["get", "status"],
  "active", 0.9,
  "maintenance", 0.6,
  "inactive", 0.3,
  0.5,
];

export function WellsMap() {
  const {
    latitude, longitude, zoom,
    setViewport, setBounds,
    wellsGeoJSON, setWellsGeoJSON,
    selectedWellId, selectWell,
    activeLayers,
  } = useMapStore();

  const [popupWell, setPopupWell] = useState<{
    properties: WellProperties;
    longitude: number;
    latitude: number;
  } | null>(null);

  // Load wells on mount
  useEffect(() => {
    fetchWells().then(setWellsGeoJSON).catch(console.error);
  }, [setWellsGeoJSON]);

  const onMoveEnd = useCallback((evt: ViewStateChangeEvent) => {
    const { latitude: lat, longitude: lng, zoom: z } = evt.viewState;
    setViewport(lat, lng, z);

    const map = (evt as unknown as { target: { getBounds(): { getWest(): number; getSouth(): number; getEast(): number; getNorth(): number } } }).target;
    if (map?.getBounds) {
      const b = map.getBounds();
      setBounds([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
    }
  }, [setViewport, setBounds]);

  const onMapClick = useCallback((evt: MapLayerMouseEvent) => {
    const feature = evt.features?.[0];
    if (feature && feature.properties) {
      const props = feature.properties as unknown as WellProperties;
      const coords = (feature.geometry as GeoJSON.Point).coordinates;
      selectWell(props.id, props);
      setPopupWell({
        properties: props,
        longitude: coords[0],
        latitude: coords[1],
      });
    } else {
      selectWell(null);
      setPopupWell(null);
    }
  }, [selectWell]);

  return (
    <div className="relative w-full h-full">
      <Map
        initialViewState={{ latitude, longitude, zoom }}
        style={{ width: "100%", height: "100%" }}
        mapStyle={MAP_STYLE}
        onMoveEnd={onMoveEnd}
        onClick={onMapClick}
        interactiveLayerIds={["wells-circle"]}
        cursor="pointer"
      >
        <NavigationControl position="top-left" />

        {wellsGeoJSON && activeLayers.includes("wells") && (
          <Source id="wells" type="geojson" data={wellsGeoJSON}>
            {/* Circle layer */}
            <Layer
              id="wells-circle"
              type="circle"
              paint={{
                "circle-radius": wellCircleRadius,
                "circle-color": wellCircleColor,
                "circle-opacity": wellCircleOpacity,
                "circle-stroke-width": [
                  "case",
                  ["==", ["get", "id"], selectedWellId ?? ""],
                  3,
                  1,
                ],
                "circle-stroke-color": [
                  "case",
                  ["==", ["get", "id"], selectedWellId ?? ""],
                  "#3b82f6",
                  "#ffffff",
                ],
              }}
            />

            {/* Label layer */}
            <Layer
              id="wells-label"
              type="symbol"
              minzoom={12}
              layout={{
                "text-field": ["get", "id"],
                "text-size": 10,
                "text-offset": [0, 1.5],
                "text-anchor": "top",
              }}
              paint={{
                "text-color": "#374151",
                "text-halo-color": "#ffffff",
                "text-halo-width": 1,
              }}
            />
          </Source>
        )}

        {/* Depression cone layer */}
        {activeLayers.includes("depression_cones") && wellsGeoJSON && (
          <DepressionConeLayer wellsGeoJSON={wellsGeoJSON} />
        )}

        {/* Interference lines */}
        {activeLayers.includes("interference") && wellsGeoJSON && (
          <InterferenceLayer wellsGeoJSON={wellsGeoJSON} />
        )}

        {/* Well popup */}
        {popupWell && (
          <WellPopup
            properties={popupWell.properties}
            longitude={popupWell.longitude}
            latitude={popupWell.latitude}
            onClose={() => {
              setPopupWell(null);
              selectWell(null);
            }}
          />
        )}
      </Map>

      {/* Layer controls overlay */}
      <LayerControls />
    </div>
  );
}
