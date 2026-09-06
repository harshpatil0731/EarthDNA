# EarthDNA
## AI-Powered Ecosystem Intelligence Platform
### Final-Year CSE Project | Research-Oriented | Software-Only | 3-Member Team | 8 Weeks | Multi-Region Study

---

## 1. Project Definition

> **EarthDNA is a software-based environmental intelligence platform that fuses satellite, weather, and historical environmental data to predict ecosystem risk, explains its predictions with SHAP, retrieves scientific evidence through Hybrid RAG, and turns that into conservation recommendations — evaluated across three geographically and climatically distinct regions to test whether the approach generalizes.**

**Scope decision:** EarthDNA studies **one environmental risk factor (wildfire risk) across three regions**, rather than one region or multiple risk factors. This keeps the pipeline, labels, and RAG corpus consistent while adding a genuine, low-cost generalization dimension to the research — see Section 2 and Section 4.

**Motto:** Observe → Detect → Predict → Explain → Retrieve → Recommend → Visualize

**Framing rule (use consistently in synopsis, paper, PPT, viva, and demo):**
> "Periodic ecosystem monitoring with automated change alerting" — not "real-time satellite monitoring."

---

## 2. Research Contribution & Novelty

Multi-source data fusion for environmental risk prediction has prior art in remote sensing literature, so the paper must state its specific contribution clearly rather than leaving it implied:

> **EarthDNA's contribution is a fully-integrated, evidence-grounded, explainable decision-support pipeline: a system where a risk prediction is never presented without (a) a SHAP-based reason, (b) retrieved scientific evidence supporting that reason, and (c) a traceable recommendation — evaluated end-to-end rather than as isolated ML components.**

Three claims to anchor the abstract and introduction around:
1. **Empirical** — quantify how much single-source vs. multi-source fusion helps for a specific, named risk, and whether that gain holds consistently across three distinct regions.
2. **Generalization** — test whether a model's performance and its SHAP-identified risk drivers transfer across geographically and climatically different regions, or are region-specific — this is the added dimension from the multi-region scope, and it is a genuinely stronger, more publishable claim than a single-site study.
3. **Systems contribution** — a reproducible architecture pattern coupling SHAP explanations to Hybrid-RAG-retrieved evidence to generate a recommendation with traceable provenance.

### Research Questions
- **RQ1 (Primary):** Does combining satellite, weather, and historical features improve risk prediction over each single source alone, and does this hold across all three regions?
- **RQ2:** Which candidate model (Random Forest / XGBoost / LightGBM vs. baseline) gives the best trade-off of predictive performance and interpretability?
- **RQ3:** Which features contribute most to predictions, per SHAP, and are they consistent with known environmental drivers — and are they consistent *across regions*, or does each region have a distinct driver profile?
- **RQ4:** Does a single model trained on pooled data from all three regions generalize as well as, better than, or worse than region-specific models? (Leave-one-region-out evaluation — see Section 5)
- **RQ5 (Secondary):** Does Hybrid RAG outperform vector-only RAG on retrieval precision/recall and answer groundedness?
- **RQ6:** Does the integrated pipeline produce recommendations a domain-adjacent reader would judge as traceable and non-fabricated?

---

## 3. Scope

### 🔴 Core (must build — the paper and demo both depend entirely on this)

| # | Feature | Minimum Bar to Call It "Done" |
|---|---|---|
| 1 | One risk target, three regions | Wildfire risk, chosen using the label-first method in Section 4; three regions locked by end of Week 1 |
| 2 | Satellite-derived features | NDVI/NDWI time series from Sentinel-2 via Google Earth Engine |
| 3 | Weather features | Temperature, rainfall, humidity from a free API, aligned to the same AOI/time window |
| 4 | Historical features | Prior fire/deforestation events, prior vegetation trend |
| 5 | Single-source baselines | Satellite-only, weather-only, historical-only models |
| 6 | Multi-source fusion model | Concatenated/fused feature set, same target, trained per-region and pooled |
| 7 | Model comparison | Logistic/Linear baseline, Random Forest, XGBoost, LightGBM |
| 8 | Leakage-safe evaluation | Spatial block CV + temporal holdout, applied within each region |
| 8b | Cross-region generalization | Leave-one-region-out (LORO) evaluation: train on 2 regions, test on the 3rd |
| 9 | SHAP explainability | Global + per-prediction explanations, compared across all three regions |
| 10 | Hybrid RAG | Vector + BM25 + reranker over a curated 40–70 document corpus (shared wildfire literature + region-specific guidance docs) |
| 11 | RAG evaluation | Vector-only vs Hybrid, on a hand-built eval query set |
| 12 | Full-stack platform | React+TS dashboard, FastAPI backend, MySQL, one AOI view |
| 13 | GIS map view | AOI boundary, risk overlay, before/after imagery toggle |
| 14 | IEEE paper draft | Written alongside the build, not after it |

### 🟡 Stretch (only after Core is fully built and evaluated)

- EarthDNA Health Score (0–100 composite)
- 2–3 LangGraph agents (Risk → RAG → Recommendation)
- Water-body change detection
- Smart alerts
- AI conversational assistant
- Automated PDF report + SHA-256 hash
- Dashboard drill-down UX polish

### 🟢 Out of Scope (state plainly in the paper's Limitations section)

Full multimodal RAG, Neo4j knowledge graph, blockchain, IoT/drones, federated learning, GNNs, causal AI, MLflow/DVC infra, Kubernetes/multi-cloud, 9-agent systems, production monitoring (Prometheus/Grafana).

---

## 4. Risk Factor & Multi-Region Strategy

**Fixed risk factor: wildfire risk.** Kept to one risk factor deliberately — expanding regions is cheap because the pipeline, label type, and RAG corpus stay the same across all three; expanding risk factors instead would have required separate label sources and separate literature per factor, multiplying effort without a proportionate gain in publishability.

- Labels: NASA FIRMS active-fire data, or MODIS/VIIRS burned-area product (free, global, well-documented, same source works for all three regions)
- Weather driver: rainfall deficit + temperature anomaly — a clean, well-understood ablation story
- Satellite: Sentinel-2 NDVI/NDWI, same processing code reused across all three regions

### The Three Regions (deliberately chosen to be climatically distinct — this is what makes the generalization claim meaningful)

| Region | Climate/Vegetation Context | Why It's a Good Fit |
|---|---|---|
| **Uttarakhand, India** | Himalayan forest, monsoon-influenced, pre-monsoon fire season | Strong local relevance for an India-based team; good FIRMS coverage |
| **Southern California, USA** | Mediterranean climate, chaparral/scrub, Santa Ana wind-driven fires | Extensively studied in wildfire literature — easy to benchmark against, good for lit review and RAG corpus |
| **Southeastern Australia (Victoria/NSW)** | Temperate eucalyptus forest, dry-season fires | Distinct fuel type and fire behavior from the other two — maximizes the "does this generalize" contrast |

Choosing three climatically different regions (monsoon-Himalayan, Mediterranean, temperate-eucalyptus) rather than three similar ones is what makes RQ3 and RQ4 (driver consistency and cross-region transfer) a real test rather than a formality.

**Selection checklist (confirm for each region before locking it in Week 1):**
- FIRMS/MODIS label coverage exists and has enough historical fire events (and enough non-fire periods) to avoid degenerate class imbalance
- Clean Sentinel-2 coverage (low persistent cloud cover) for the region and study period
- Adequate weather station/reanalysis (NASA POWER/Open-Meteo) coverage
- A boundable AOI polygon of manageable size (a few hundred to low-thousands of km², not an entire state/country — keeps satellite processing tractable)

**Why this is a cheap expansion, not a 3x one:** every pipeline script from Section 7 (satellite collection, weather collection, label collection, feature engineering) is written once, parameterized by AOI, and simply run three times. The extra cost is data-collection wall-clock time and three sets of results to log — not three separate systems to build.

---

## 5. Methodology Safeguards

### Leakage Control
- No random row-level train/test split — environmental data is spatially and temporally autocorrelated, and random splits inflate reported metrics.
- **Spatial block cross-validation**: split the AOI into non-overlapping tiles; hold out entire tiles for testing.
- **Temporal holdout**: train on earlier years, test on the most recent year/season, to simulate real deployment.
- Report both splits' results.

### Statistical Rigor
- Run each model with at least 5 different random seeds; report mean ± standard deviation.
- Run a paired significance test (paired t-test or Wilcoxon signed-rank) between the best multi-source model and the best single-source baseline, and report the p-value.
- Repeat both of the above independently **within each region**, so each region's result is itself statistically sound, not just the pooled average.

### Cross-Region Generalization (Leave-One-Region-Out)
- Train the fusion model on two regions, test on the third; rotate through all three combinations.
- Compare LORO performance against each region's own in-region model — a large gap indicates the model is learning region-specific patterns rather than transferable wildfire-risk signal, which is itself a valid and interesting finding to report, not a failure.
- Compare SHAP feature-importance rankings across the three regions' in-region models — report which drivers are consistent (likely candidates: temperature anomaly, rainfall deficit) and which are region-specific (likely candidates: specific vegetation/NDVI thresholds tied to local fuel type).

### Reproducibility Log (per experiment)
Dataset version/date · AOI definition · time period · train/test split method · feature list · model + hyperparameters · random seed(s) · metrics · one-line limitation note.

### Class Imbalance
Risk events are typically rare. Use class-weighted loss or resampling, and report precision/recall/F1 and PR-AUC — accuracy alone is not meaningful on imbalanced risk data.

---

## 6. System Architecture

```text
React + TypeScript GIS Dashboard
              │
              ▼
          FastAPI API
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
   CV      Hybrid RAG  Risk + SHAP
     │        │        │
     └────────┼────────┘
              ▼
       (Stretch) LangGraph Agents
              │
              ▼
            MySQL
```

---

## 7. Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Frontend | React + TypeScript, Tailwind CSS | Dashboard UI |
| GIS | Leaflet | Map + overlays |
| Backend | FastAPI | REST API |
| Database | MySQL | Structured metadata, predictions, experiment logs |
| Satellite | Google Earth Engine + Sentinel-2 (+ Landsat for historical) | Imagery + NDVI/NDWI |
| Labels | NASA FIRMS or Hansen Global Forest Change | Ground truth |
| Weather | Open-Meteo or NASA POWER | Temperature/rainfall/humidity |
| GIS processing | GeoPandas, Rasterio, GDAL | Vector/raster handling |
| ML | Scikit-learn, XGBoost, LightGBM | Risk prediction |
| XAI | SHAP | Explainability |
| RAG | LangChain, Sentence-Transformers, BM25 (`rank_bm25`), FAISS or ChromaDB, a cross-encoder reranker | Hybrid retrieval |
| LLM | Any accessible API-based LLM | Grounded answer generation |
| Deployment | Docker Compose | Local + demo consistency |

---

## 8. Hybrid RAG

### Corpus
40–70 curated documents: a shared core of general wildfire-ecology papers (fire behavior, weather drivers, fuel types) plus a smaller set of region-specific documents for each of the three regions (local forest-management guidelines, region-specific fire-history reports). The shared core keeps the corpus from tripling in size while still letting retrieval surface region-relevant evidence.

### Pipeline
```text
Question → Vector Search + BM25 → Metadata Filter → Reranker → Context → LLM → Grounded Answer + Citations
```

### Evaluation Set
Before building, write 40–60 question–relevant-document pairs by hand (read the corpus, write realistic questions, mark which documents answer them). This ground truth supports:
- Retrieval precision / recall @k
- Context relevance
- Groundedness (does the LLM's answer stay within retrieved evidence)
- Vector-only vs Hybrid comparison (RQ4)

---

## 9. Explainability → Evidence → Recommendation Chain

```text
Risk Prediction (HIGH/MED/LOW)
        +
SHAP top contributing features
        +
Hybrid RAG-retrieved scientific evidence relevant to those features
        ↓
Recommendation (decision-support wording only)
```

Example output style:
> "Predicted risk: HIGH. Primary drivers: 3-month rainfall deficit, rising vegetation stress (SHAP). Related guidance: [retrieved source, cited]. Recommendation: prioritize this zone for field verification and monitoring — not an automated confirmation of active risk."

---

## 10. Database Design

```text
users
ecosystems / aoi_definitions
satellite_observations
weather_observations
environmental_features
risk_predictions
model_results          -- per model, per seed, per split
shap_explanations
rag_documents
rag_eval_queries        -- the hand-labeled Q/doc pairs
rag_queries_log
recommendations
```

Stretch-only tables (`alerts`, `reports`, `report_hashes`, `ai_audit_logs`) can be added later if Stretch scope is reached.

---

## 11. 8-Week Plan

| Week | Build | Research / Paper |
|---|---|---|
| 1 | Lock wildfire as risk factor + all three regions (Section 4), FastAPI+MySQL+React skeleton, start satellite/weather/label collection **for all three regions in parallel** (same script, three runs) | Literature review (10–15 papers, spread across all three regions' wildfire literature), finalize RQs, pick target venue, start paper skeleton |
| 2 | Finish data collection + preprocessing for all three regions, NDVI/NDWI features, align weather + label timelines per region | Draft Related Work |
| 3 | Build single-source + multi-source feature sets per region; frontend shows a region-selector map with all three AOIs by end of week | Draft Methodology (include LORO design) |
| 4 | Train baseline, RF, XGBoost, LightGBM **per region** with spatial-block CV + multi-seed runs + significance test; begin pooled/LORO training | Draft initial Results (RQ1–RQ2, per-region tables) |
| 5 | Finish LORO evaluation; SHAP explanations per region + cross-region comparison; build RAG corpus (shared + region-specific docs) + eval query set; implement vector-only and Hybrid RAG | Draft Results for RQ3–RQ4 (SHAP consistency, generalization); run RAG evaluation (RQ5) |
| 6 | Integrate SHAP + RAG + recommendation chain into dashboard; GIS overlays with region switcher, before/after view | Draft Discussion + Limitations |
| 7 | Full-stack polish, bug fixes, Stretch features only if Core (all three regions) is fully evaluated | Full paper draft complete; internal review pass |
| 8 | Final testing, deployment, demo rehearsal (demo should show region-switching) | Abstract, conclusion, formatting to venue template, submission, viva prep |

**Note on the added workload:** the three-region expansion adds real time to Weeks 1–2 (data collection) and Week 4–5 (three sets of model runs, LORO evaluation) — budget roughly 3–4 extra days total across the project. If the team falls behind, the first thing to cut is **not** a region (that would break the generalization story) but the Stretch features in Section 3 — the three-region core evaluation should be protected over any Stretch item.

**Early integration rule:** a real AOI, map, and placeholder risk view should be visible in the dashboard by end of Week 3 — don't let the frontend wait for backend completion.

---

## 12. Success Criteria

**Technical**
- All Core items in Section 3 working end-to-end
- Every model result reported with spatial+temporal split, multi-seed mean±std, and a significance test on the headline comparison

**Research**
- RQ1–RQ4 answered with numbers, not assertions
- Explicit Limitations section covering: label noise, satellite revisit/cloud gaps, small AOI generalizability, RAG corpus size, LLM groundedness caveats
- Paper formatted to the chosen venue's template, submitted before its deadline

**Demonstration (viva flow)**
```text
Select AOI → View satellite change → View risk prediction → SHAP explanation
   → Ask AI assistant why → Show RAG evidence → Show recommendation → GIS detail view
```

---

## 13. Risk Register

| Risk | Mitigation |
|---|---|
| No usable label source for chosen AOI | Label-source-first selection before AOI is locked |
| Leaked/inflated model metrics | Mandatory spatial block CV + temporal holdout |
| Reviewer asks "what's new" | Explicit novelty claim stated in abstract/intro |
| Accuracy looks great but is meaningless (imbalance) | PR-AUC/F1/recall required; accuracy alone disallowed |
| RAG comparison has no ground truth | Hand-built 40–60 query eval set, scheduled as its own task |
| Scope creep eats evaluation time | Core/Stretch split; Stretch forbidden until Core is evaluated |
| Paper rushed at the end | Paper skeleton and lit review start Week 1 |
| Cloud cover / satellite revisit gaps | Named as a stated limitation |
| LLM fabricating claims not in evidence | Groundedness checked against retrieved context; strict wording discipline in outputs |
| Data quality/coverage differs across the three regions | Checked against the Section 4 selection checklist for each region individually before locking it in Week 1 |
| Three regions triple the debugging surface | All region-specific pipelines share one parameterized codebase (Section 4) — a bug fixed once fixes all three |
| LORO results are weak/inconsistent (models don't transfer) | Framed as a valid finding either way — "risk drivers are largely region-specific" is still a publishable result, not a failure, as long as it's reported honestly |

---

## 14. Team Division

**Member 1 — AI/CV & Research Lead:** satellite preprocessing, feature engineering, model training/comparison, SHAP, experiment design, methodology + results writing.

**Member 2 — GenAI/RAG:** corpus curation, embeddings, BM25, reranking, RAG eval set + evaluation, RAG results writing.

**Member 3 — Full-Stack:** React/TS dashboard, FastAPI, MySQL, GIS map, Docker, deployment, demo integration.

All three should be able to explain every Core component in viva.

---

## 15. Repository Structure

```text
EarthDNA/
├── frontend/
├── backend/
├── ai/
│   ├── features/
│   ├── prediction/
│   └── xai/
├── rag/
│   ├── ingestion/
│   ├── vector_search/
│   ├── keyword_search/
│   ├── reranking/
│   └── evaluation/
├── gis/
├── database/
├── datasets/
├── experiments/          -- one YAML/log per run: seed, split, metrics
├── paper/                -- lit review, drafts, venue template
├── docker/
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 16. Final Statement

EarthDNA is scoped to be finishable and defensible. The paper's strength comes from a small number of claims — multi-source fusion effect, cross-region generalization, SHAP-consistency, Hybrid RAG improvement — each backed by leakage-safe, statistically-tested evidence, not from the length of the feature list. The three-region design was chosen specifically because it strengthens these claims at low added engineering cost; if time runs short, protect the three-region core evaluation and cut Stretch features first, never a region.
