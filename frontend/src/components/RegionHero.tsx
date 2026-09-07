import { CheckCircle2, MapPin } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

import type { RegionDetail } from "../types";

export function RegionHero({ region }: { region: RegionDetail }) {
  const reduceMotion = useReducedMotion();

  return (
    <section className="region-hero" aria-labelledby="region-heading">
      <AnimatePresence mode="wait" initial={!reduceMotion}>
        <motion.div className="region-copy" key={region.region_id} initial={reduceMotion ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? undefined : { opacity: 0, y: -8 }} transition={{ duration: 0.34, ease: "easeOut" }}>
          <p className="eyebrow">Earth observation platform</p>
          <h2 id="region-heading">{region.aoi_name}</h2>
          <p className="region-subtitle"><MapPin size={16} aria-hidden="true" /> {region.study_region_name} · Wildfire &amp; Ecosystem Study</p>
        </motion.div>
      </AnimatePresence>
      <motion.div className="phase-badge" initial={reduceMotion ? false : { opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: reduceMotion ? 0 : 0.18, duration: 0.34 }}>
        <CheckCircle2 size={16} aria-hidden="true" />
        <span>Phase 1 complete</span>
      </motion.div>
    </section>
  );
}
