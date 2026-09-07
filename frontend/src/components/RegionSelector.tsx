import { ChevronDown, MapPinned } from "lucide-react";
import { motion } from "framer-motion";

import type { RegionSummary } from "../types";

type RegionSelectorProps = {
  regions: RegionSummary[];
  selectedRegionId: string;
  onChange: (regionId: string) => void;
};

export function RegionSelector({ regions, selectedRegionId, onChange }: RegionSelectorProps) {
  return (
    <label className="region-selector">
      <span className="control-label">Active study region</span>
      <motion.div className="select-shell" whileHover={{ y: -1 }} whileTap={{ scale: 0.99 }}>
        <MapPinned aria-hidden="true" size={17} />
        <select value={selectedRegionId} onChange={(event) => onChange(event.target.value)} aria-label="Select study region">
          {regions.map((region) => (
            <option key={region.region_id} value={region.region_id}>
              {region.study_region_name} - {region.aoi_name}
            </option>
          ))}
        </select>
        <ChevronDown aria-hidden="true" className="select-chevron" size={17} />
      </motion.div>
    </label>
  );
}
