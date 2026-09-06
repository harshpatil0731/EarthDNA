import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, Polygon } from "geojson";
import type { LatLngBoundsExpression } from "leaflet";

import "leaflet/dist/leaflet.css";

type PlaceholderDashboard = {
  phase_label: string;
  risk_status: string;
  health_status: string;
  status_note: string;
};

type RegionSummary = {
  region_id: string;
  study_region_name: string;
  aoi_name: string;
  risk_target: string;
  placeholder: PlaceholderDashboard;
};

type RegionDetail = RegionSummary & {
  geometry_version: string;
  aoi_geometry: Polygon;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function MapViewport({ geometry }: { geometry: Polygon }) {
  const map = useMap();

  useEffect(() => {
    const coordinates = geometry.coordinates[0].map(([longitude, latitude]) => [
      latitude,
      longitude,
    ]) as LatLngBoundsExpression;
    map.fitBounds(coordinates, { padding: [36, 36] });
  }, [geometry, map]);

  return null;
}

function App() {
  const [regions, setRegions] = useState<RegionSummary[]>([]);
  const [selectedRegionId, setSelectedRegionId] = useState("uttarakhand");
  const [activeRegion, setActiveRegion] = useState<RegionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/regions`)
      .then((response) => {
        if (!response.ok) throw new Error("Unable to load EarthDNA regions.");
        return response.json() as Promise<RegionSummary[]>;
      })
      .then(setRegions)
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    setError(null);
    fetch(`${API_BASE_URL}/api/regions/${selectedRegionId}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error("Unable to load the selected AOI.");
        return response.json() as Promise<RegionDetail>;
      })
      .then((region) => {
        if (!controller.signal.aborted) setActiveRegion(region);
      })
      .catch((requestError: Error) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      });

    return () => controller.abort();
  }, [selectedRegionId]);

  if (error) {
    return <main className="app-shell"><p className="error-message">{error}</p></main>;
  }

  if (!activeRegion) {
    return <main className="app-shell"><p className="loading-message">Loading EarthDNA regions...</p></main>;
  }

  const feature: Feature<Polygon> = {
    type: "Feature",
    properties: { region_id: activeRegion.region_id },
    geometry: activeRegion.aoi_geometry,
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Ecosystem Intelligence Platform</p>
          <h1>EarthDNA</h1>
        </div>
        <label className="region-control">
          <span>Study region</span>
          <select
            value={selectedRegionId}
            onChange={(event) => setSelectedRegionId(event.target.value)}
            aria-label="Select study region"
          >
            {regions.map((region) => (
              <option key={region.region_id} value={region.region_id}>
                {region.study_region_name} - {region.aoi_name}
              </option>
            ))}
          </select>
        </label>
      </header>

      <section className="region-summary" aria-labelledby="region-heading">
        <div>
          <p className="eyebrow">Active Area of Interest</p>
          <h2 id="region-heading">{activeRegion.study_region_name}</h2>
          <p>{activeRegion.aoi_name} · Wildfire risk study</p>
        </div>
        <span className="placeholder-badge">{activeRegion.placeholder.phase_label}</span>
      </section>

      <section className="dashboard-grid">
        <div className="map-panel">
          <MapContainer className="aoi-map" center={[20, 0]} zoom={3} scrollWheelZoom>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapViewport geometry={activeRegion.aoi_geometry} />
            <GeoJSON key={activeRegion.region_id} data={feature} style={{ color: "#087e8b", weight: 3, fillOpacity: 0.16 }} />
          </MapContainer>
          <p className="map-caption">Finalized AOI boundary · Geometry v{activeRegion.geometry_version}</p>
        </div>

        <div className="status-panel">
          <article className="status-card">
            <span>Wildfire Risk</span>
            <strong>{activeRegion.placeholder.risk_status}</strong>
            <small>{activeRegion.placeholder.phase_label}</small>
          </article>
          <article className="status-card">
            <span>Ecosystem Health</span>
            <strong>{activeRegion.placeholder.health_status}</strong>
            <small>Health Score is not calculated in Phase 1.</small>
          </article>
          <article className="status-note">
            <span>Integration Status</span>
            <p>{activeRegion.placeholder.status_note}</p>
          </article>
        </div>
      </section>
    </main>
  );
}

export default App;
