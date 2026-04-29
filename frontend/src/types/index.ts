/** Shared types mirroring backend Pydantic schemas. */

export interface MapContext {
  center_lat: number;
  center_lng: number;
  zoom: number;
  bbox: [number, number, number, number]; // [west, south, east, north]
  active_layers: string[];
  selected_well_id: string | null;
  filters: Record<string, unknown>;
  depression_cone_t_days?: number;
  depression_cone_mode?: "selected" | "all";
  interference_visible?: boolean;
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

// --- Theis Interference ---

export type Severity = "low" | "medium" | "high" | "critical";

export interface InterferencePair {
  well_a: string;
  well_b: string;
  distance_km: number;
  coef_at_a: number;
  coef_at_b: number;
  drawdown_midpoint_m: number;
  severity: Severity;
  dominant_well: string;
  recommendation: string;
}

export interface InterferenceResult {
  type: "interference_result";
  pairs: InterferencePair[];
  t_days: number;
  wells_analyzed: number;
  pairs_significant: number;
}

export interface InterferenceCard {
  type: "interference_card";
  pairs_summary: Record<string, number>;
  top_concerns: Array<{
    well_a: string;
    well_b: string;
    coef_max: number;
    action: string;
  }>;
  regional_pattern: string;
}

// --- Theis Drawdown ---

export interface DrawdownIsoline {
  level_m: number;
  polygon: GeoJSON.MultiPolygon | GeoJSON.Polygon;
}

export interface DrawdownGrid {
  type: "drawdown_grid";
  well_id: string;
  center: [number, number];
  t_days: number;
  isolines: DrawdownIsoline[];
  max_drawdown_m: number;
  interfering_wells: string[];
}

export interface DrawdownCard {
  type: "drawdown_card";
  well_id: string;
  t_days: number;
  max_drawdown_m: number;
  cone_radius_1m_km: number;
  interfering_wells: string[];
  assessment: string;
  recommendation: string;
}

export type StructuredCard =
  | AnomalyCard
  | ValidationResult
  | RegionStats
  | WellHistory
  | InterferenceCard
  | DrawdownCard;

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
