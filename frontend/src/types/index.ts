/** Shared types mirroring backend Pydantic schemas. */

export interface MapContext {
  center_lat: number;
  center_lng: number;
  zoom: number;
  bbox: [number, number, number, number]; // [west, south, east, north]
  active_layers: string[];
  selected_well_id: string | null;
  filters: Record<string, unknown>;
}

export interface WellProperties {
  id: string;
  name_en: string;
  cluster_id: string;
  cluster_name: string;
  well_depth_m: number;
  aquifer_type: string;
  casing_diameter_mm: number;
  ground_elevation_m: number;
  transmissivity_m2d: number;
  storativity: number;
  status: "active" | "inactive" | "maintenance";
  current_yield_ls: number;
  static_water_level_m: number;
  last_tds_mgl: number;
  last_ph: number;
  last_chloride_mgl: number;
  last_temperature_c: number;
  operator: string;
  installation_date: string;
}

export interface WellFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number]; // [lng, lat]
  };
  properties: WellProperties;
}

export interface WellsGeoJSON {
  type: "FeatureCollection";
  features: WellFeature[];
}

export interface AnomalyCard {
  type: "anomaly_card";
  severity: "low" | "medium" | "high" | "critical";
  well_id: string;
  anomaly_type: string;
  title: string;
  description: string;
  value_current: number;
  value_baseline: number;
  change_pct: number;
  recommendation: string;
}

export interface ValidationResult {
  type: "validation_result";
  valid: boolean;
  total_rows: number;
  valid_rows: number;
  errors: string[];
  warnings: string[];
  column_stats: Record<string, { min: number; max: number; mean: number }>;
}

export interface WellHistory {
  type: "well_history";
  well_id: string;
  parameter: string;
  timestamps: string[];
  values: number[];
  trend: "rising" | "falling" | "stable";
  anomalies_detected: Record<string, unknown>[];
}

export interface RegionStats {
  type: "region_stats";
  well_count: number;
  active_count: number;
  avg_debit_ls: number;
  avg_tds_mgl: number;
  anomaly_count: number;
  wells_in_bbox: string[];
}

export type StructuredCard = AnomalyCard | ValidationResult | RegionStats | WellHistory;

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  cards?: StructuredCard[];
  timestamp: Date;
}

/** SSE event types from backend */
export type SSEEvent =
  | { type: "meta"; model_pool: string; task_type: string }
  | { type: "token"; content: string }
  | { type: "tool_call"; tool: string; args: Record<string, unknown> }
  | { type: "tool_result"; tool: string; success: boolean; result: unknown }
  | { type: "error"; message: string }
  | { type: "done"; latency_ms: number };
