import { Check } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

const milestones = ["AOI Configuration", "Weather Collection", "Satellite Collection", "NASA FIRMS Labels", "Feature Engineering", "Single-Source Baselines", "Dashboard Integration"];

export function PhaseProgress() {
  const reduceMotion = useReducedMotion();
  return (
    <section className="phase-progress section-block" aria-labelledby="phase-progress-heading">
      <div className="section-heading">
        <div><p className="eyebrow">Delivery timeline</p><h2 id="phase-progress-heading">Phase 1 progress</h2></div>
        <span className="phase-version">v0.4-phase1-complete</span>
      </div>
      <div className="progress-track">
        {milestones.map((milestone, index) => (
          <motion.div className="progress-item" key={milestone} initial={reduceMotion ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.25 }} transition={{ delay: reduceMotion ? 0 : index * 0.055, duration: 0.35 }}>
            <span className="progress-check"><Check size={15} aria-hidden="true" /></span><span>{milestone}</span>
          </motion.div>
        ))}
      </div>
      <div className="phase-complete"><span className="status-pulse" aria-hidden="true" /><strong>Phase 1 complete</strong><span>AOI configuration, collection pipelines, validation prototypes, and integration are complete.</span></div>
    </section>
  );
}
