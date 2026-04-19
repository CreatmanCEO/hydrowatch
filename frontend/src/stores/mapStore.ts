'use client';

import { create } from "zustand";
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

  // Actions
  setViewport: (lat: number, lng: number, zoom: number) => void;
  setBounds: (bounds: [number, number, number, number]) => void;
  toggleLayer: (layer: string) => void;
  selectWell: (wellId: string | null, properties?: WellProperties | null) => void;
  setWellsGeoJSON: (data: WellsGeoJSON) => void;
  setFilters: (filters: Record<string, unknown>) => void;

  // Derived
  getApiContext: () => MapContext;
}

export const useMapStore = create<MapState>((set, get) => ({
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

  getApiContext: () => {
    const s = get();
    return buildMapContext(s);
  },
}));
