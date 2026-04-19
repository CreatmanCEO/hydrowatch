/** API client for HydroWatch backend. */
import type { WellsGeoJSON, WellHistory, ValidationResult } from "@/types";

const API_BASE = "/api";

export async function fetchWells(): Promise<WellsGeoJSON> {
  const res = await fetch(`${API_BASE}/wells`);
  if (!res.ok) throw new Error(`Failed to fetch wells: ${res.status}`);
  return res.json();
}

export async function fetchWellHistory(
  wellId: string,
  parameter = "debit_ls",
  lastNDays?: number
): Promise<WellHistory> {
  const params = new URLSearchParams({ parameter });
  if (lastNDays) params.set("last_n_days", String(lastNDays));
  const res = await fetch(`${API_BASE}/wells/${wellId}/history?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch history: ${res.status}`);
  return res.json();
}

export async function uploadCSV(file: File): Promise<ValidationResult> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/upload/csv`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}
