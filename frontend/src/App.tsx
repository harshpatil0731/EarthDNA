import { useEffect, useState } from "react";
import { Flame, Leaf, Satellite } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import { AnimatedBackground } from "./components/AnimatedBackground";
import { DataSourcesSection } from "./components/DataSourcesSection";
import { Header } from "./components/Header";
import { MapPanel } from "./components/MapPanel";
import { PhaseProgress } from "./components/PhaseProgress";
import { RegionHero } from "./components/RegionHero";
import { StatusCard } from "./components/StatusCard";
import type { RegionDetail, RegionSummary } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function App() {
  const [regions, setRegions] = useState<RegionSummary[]>([]);
  const [selectedRegionId, setSelectedRegionId] = useState("uttarakhand");
  const [activeRegion, setActiveRegion] = useState<RegionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();

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
    fetch(`${API_BASE_URL}/api/regions/${selectedRegionId}`, { signal: controller.signal })
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

  return (
    <main className="app-shell">
      <AnimatedBackground />
      <div className="dashboard-content">
        <Header regions={regions} selectedRegionId={selectedRegionId} onRegionChange={setSelectedRegionId} />
        {error && <p className="error-message" role="alert">{error}</p>}
        {!activeRegion && !error && <p className="loading-message">Establishing EarthDNA observation link...</p>}
        {activeRegion && (
          <motion.div className="dashboard-body" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
            <RegionHero region={activeRegion} />
            <section className="primary-dashboard" aria-label="Area of interest dashboard">
              <MapPanel region={activeRegion} />
              <aside className="status-panel" aria-label="Phase 1 status indicators">
                <StatusCard icon={Flame} title="Wildfire risk" value={activeRegion.placeholder.risk_status} detail={activeRegion.placeholder.phase_label} tone="risk" index={0} />
                <StatusCard icon={Leaf} title="Ecosystem health" value={activeRegion.placeholder.health_status} detail="Health Score is not calculated in Phase 1." tone="health" index={1} />
                <StatusCard icon={Satellite} title="Integration status" value="AOI configuration is connected" detail="No operational prediction is shown." tone="integration" index={2} />
              </aside>
            </section>
            <DataSourcesSection />
            <PhaseProgress />
          </motion.div>
        )}
      </div>
    </main>
  );
}

export default App;
