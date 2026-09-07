import type { Polygon } from "geojson";

export type PlaceholderDashboard = {
  phase_label: string;
  risk_status: string;
  health_status: string;
  status_note: string;
};

export type RegionSummary = {
  region_id: string;
  study_region_name: string;
  aoi_name: string;
  risk_target: string;
  placeholder: PlaceholderDashboard;
};

export type RegionDetail = RegionSummary & {
  geometry_version: string;
  aoi_geometry: Polygon;
};
