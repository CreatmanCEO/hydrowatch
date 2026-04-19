/** Serialize map store state into MapContext for API requests. */
import type { MapContext } from "@/types";

export function buildMapContext(state: {
  latitude: number;
  longitude: number;
  zoom: number;
  bounds: [number, number, number, number] | null;
  activeLayers: string[];
  selectedWellId: string | null;
  filters: Record<string, unknown>;
}): MapContext {
  return {
    center_lat: state.latitude,
    center_lng: state.longitude,
    zoom: state.zoom,
    // Fallback: entire Abu Dhabi region until map fires first onMoveEnd
    bbox: state.bounds ?? [54.0, 24.0, 56.0, 25.0],
    active_layers: state.activeLayers,
    selected_well_id: state.selectedWellId,
    filters: state.filters,
  };
}
