import { useEffect } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, Polygon } from "geojson";
import type { LatLngBoundsExpression } from "leaflet";
import { Crosshair, Layers3 } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import type { RegionDetail } from "../types";

function MapViewport({ geometry }: { geometry: Polygon }) {
  const map = useMap();

  useEffect(() => {
    const coordinates = geometry.coordinates[0].map(([longitude, latitude]) => [latitude, longitude]) as LatLngBoundsExpression;
    const mapLayoutTimer = window.setTimeout(() => {
      map.invalidateSize({ animate: false });
      map.fitBounds(coordinates, { padding: [42, 42], animate: true, duration: 0.6 });
    }, 0);

    return () => window.clearTimeout(mapLayoutTimer);
  }, [geometry, map]);

  return null;
}

const REGION_COLORS: Record<string, string> = {
  uttarakhand: "#32d583",
  california: "#f6b44f",
  australia: "#4bc4e6",
};

export function MapPanel({ region }: { region: RegionDetail }) {
  const reduceMotion = useReducedMotion();
  const feature: Feature<Polygon> = { type: "Feature", properties: { region_id: region.region_id }, geometry: region.aoi_geometry };
  const color = REGION_COLORS[region.region_id] ?? "#32d583";

  return (
    <motion.section className="map-panel" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: reduceMotion ? 0 : 0.15, duration: 0.55, ease: "easeOut" }} aria-label="Interactive area of interest map">
      <div className="map-toolbar" aria-hidden="true">
        <span><Layers3 size={15} /> AOI boundary</span>
        <span><Crosshair size={15} /> Geometry v{region.geometry_version}</span>
      </div>
      <div className="map-frame">
        <MapContainer className="aoi-map" center={[20, 0]} zoom={3} scrollWheelZoom>
          <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <MapViewport geometry={region.aoi_geometry} />
          <GeoJSON key={region.region_id} data={feature} style={{ color, weight: 3, opacity: 1, fillColor: color, fillOpacity: 0.19, className: "aoi-boundary" }} />
        </MapContainer>
        <div className="map-grid-overlay" aria-hidden="true" />
        <div className="map-scan-overlay" aria-hidden="true" />
      </div>
      <p className="map-caption">Finalized AOI boundary delivered by the EarthDNA region API.</p>
    </motion.section>
  );
}
