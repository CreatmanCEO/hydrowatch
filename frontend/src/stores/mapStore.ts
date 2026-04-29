'use client';

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { WellProperties, WellsGeoJSON, MapContext } from "@/types";
import { buildMapContext } from "@/lib/contextBridge";

interface MapState {
  // Viewport
  latitude: number;
  longitude: number;
  zoom: number;
  bounds: [number, number, number, number] | null;

  // Layers & selection
  activeLayers: string[];
  selectedWellId: string | null;
  selectedWell: WellProperties | null;
  filters: Record<string, unknown>;

  // Data
  wellsGeoJSON: WellsGeoJSON | null;

  // Theis cone state
  coneTimeDays: number; // 1, 7, 30, 90
  coneMode: "selected" | "all";

  // Actions
  setViewport: (lat: number, lng: number, zoom: number) => void;
  setBounds: (bounds: [number, number, number, number]) => void;
  toggleLayer: (layer: string) => void;
  selectWell: (wellId: string | null, properties?: WellProperties | null) => void;
  setWellsGeoJSON: (data: WellsGeoJSON) => void;
  setFilters: (filters: Record<string, unknown>) => void;
  setConeTimeDays: (days: number) => void;
  setConeMode: (mode: "selected" | "all") => void;

  // Derived
  getApiContext: () => MapContext;
}

export const useMapStore = create<MapState>()(
  devtools(
    (set, get) => ({
      // Default: Abu Dhabi center
      latitude: 24.42,
      longitude: 54.85,
      zoom: 9,
      bounds: null,

      activeLayers: ["wells"],
      selectedWellId: null,
      selectedWell: null,
      filters: {},

      wellsGeoJSON: null,

      coneTimeDays: 30,
      coneMode: "selected",

      setViewport: (latitude, longitude, zoom) =>
        set({ latitude, longitude, zoom }),

      setBounds: (bounds) => set({ bounds }),

      toggleLayer: (layer) =>
        set((s) => ({
          activeLayers: s.activeLayers.includes(layer)
            ? s.activeLayers.filter((l) => l !== layer)
            : [...s.activeLayers, layer],
        })),

      selectWell: (wellId, properties = null) =>
        set({ selectedWellId: wellId, selectedWell: properties ?? null }),

      setWellsGeoJSON: (data) => set({ wellsGeoJSON: data }),

      setFilters: (filters) => set({ filters }),

      setConeTimeDays: (days) => set({ coneTimeDays: days }),
      setConeMode: (mode) => set({ coneMode: mode }),

      getApiContext: () => {
        const s = get();
        return {
          ...buildMapContext(s),
          depression_cone_t_days: s.coneTimeDays,
          depression_cone_mode: s.coneMode,
          interference_visible: s.activeLayers.includes("interference"),
        };
      },
    }),
    { name: "MapStore" }
  )
);
