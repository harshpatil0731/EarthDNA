import type { LucideIcon } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

type StatusCardProps = {
  icon: LucideIcon;
  title: string;
  value: string;
  detail: string;
  tone: "risk" | "health" | "integration";
  index: number;
};

export function StatusCard({ icon: Icon, title, value, detail, tone, index }: StatusCardProps) {
  const reduceMotion = useReducedMotion();
  return (
    <motion.article className={`status-card status-card--${tone}`} initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: reduceMotion ? 0 : 0.22 + index * 0.09, duration: 0.45, ease: "easeOut" }} whileHover={reduceMotion ? undefined : { y: -4 }}>
      <div className="card-icon"><Icon size={20} aria-hidden="true" /></div>
      <div className="card-copy">
        <p>{title}</p>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </motion.article>
  );
}
