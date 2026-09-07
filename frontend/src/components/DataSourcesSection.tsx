import { CloudSun, Flame, Satellite } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

type Source = { name: string; description: string; icon: LucideIcon; tone: string };
const sources: Source[] = [
  { name: "Sentinel-2", description: "Environmental vegetation observations", icon: Satellite, tone: "emerald" },
  { name: "Weather", description: "Temperature, precipitation, humidity", icon: CloudSun, tone: "cyan" },
  { name: "NASA FIRMS", description: "VIIRS active-fire detections", icon: Flame, tone: "amber" },
];

export function DataSourcesSection() {
  const reduceMotion = useReducedMotion();
  return (
    <section className="data-sources section-block" aria-labelledby="data-sources-heading">
      <div className="section-heading">
        <div><p className="eyebrow">Observation network</p><h2 id="data-sources-heading">Connected data sources</h2></div>
        <span className="section-meta">3 verified source connections</span>
      </div>
      <div className="source-grid">
        {sources.map(({ name, description, icon: Icon, tone }, index) => (
          <motion.article className={`source-card source-card--${tone}`} key={name} initial={reduceMotion ? false : { opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ delay: reduceMotion ? 0 : index * 0.09, duration: 0.44, ease: "easeOut" }} whileHover={reduceMotion ? undefined : { y: -5 }}>
            <div className="source-icon"><Icon size={23} aria-hidden="true" /></div>
            <div><h3>{name}</h3><p>{description}</p></div>
            <span className="connected-status"><i aria-hidden="true" /> Connected</span>
          </motion.article>
        ))}
      </div>
    </section>
  );
}
