import { Activity, Orbit } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import type { RegionSummary } from "../types";
import { RegionSelector } from "./RegionSelector";

type HeaderProps = {
  regions: RegionSummary[];
  selectedRegionId: string;
  onRegionChange: (regionId: string) => void;
};

export function Header({ regions, selectedRegionId, onRegionChange }: HeaderProps) {
  const reduceMotion = useReducedMotion();

  return (
    <header className="site-header">
      <motion.div className="brand-lockup" initial={reduceMotion ? false : { opacity: 0, x: -18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.55, ease: "easeOut" }}>
        <div className="brand-mark" aria-hidden="true"><Orbit size={22} /></div>
        <div>
          <p className="brand-kicker">Environmental intelligence</p>
          <h1>EarthDNA</h1>
        </div>
      </motion.div>
      <div className="header-actions">
        <div className="system-status" aria-label="System configuration online">
          <span className="status-pulse" aria-hidden="true" />
          <Activity aria-hidden="true" size={15} />
          <span>System online</span>
        </div>
        <RegionSelector regions={regions} selectedRegionId={selectedRegionId} onChange={onRegionChange} />
      </div>
    </header>
  );
}
