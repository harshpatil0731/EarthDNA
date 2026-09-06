# EarthDNA — Phase Plan & GitHub Push Strategy

This document splits the 8-week build into two phases (Phase 1 ≈ 40%, Phase 2 ≈ 60%) and tells you exactly when and what to push to GitHub, so that anyone browsing the repository's commit history can follow the project's progress step by step without needing to be told separately.

---

## 1. How the 40/60 Split Works

**Phase 1 (Weeks 1–3, ~40%)** — Foundation: repo, data pipelines, single-source features, single-source baseline models, frontend/backend skeleton wired together, research groundwork started. Nothing "impressive" yet, but everything downstream depends on it being solid.

**Phase 2 (Weeks 4–8, ~60%)** — Everything that makes the project publishable and demo-ready: multi-source fusion, rigorous model comparison, SHAP, Hybrid RAG, the explainability→evidence→recommendation chain, full dashboard/GIS, paper draft, and submission.

This split is intentional, not arbitrary: Phase 1 is infrastructure-heavy (lower complexity, higher volume of setup work), Phase 2 is where the actual research contribution and evaluation live. 40/60 reflects effort more accurately than a 50/50 split would.

---

## 2. Phase 1 — Foundation (Weeks 1–3, Target: 40%)

### Milestone 1.1 — Repo & Project Skeleton (Week 1, Days 1–2)
- Initialize repo with the full folder structure (empty placeholder folders + `.gitkeep` where needed)
- Add root `README.md` (the project plan), `.env.example`, `.gitignore`, `docker-compose.yml` skeleton
- Add a `LICENSE` and a one-paragraph project description
- Set up basic FastAPI app (`/health` endpoint) and basic React+TS app (default page) — just proving both run

**Push 1:** `feat: initial project scaffolding (backend, frontend, docker, docs)`
→ Tag: `v0.1-scaffold`

### Milestone 1.2 — Risk Factor & Three Regions Finalized (Week 1, Days 3–5)
- Add `docs/region_selection.md` documenting the fixed risk factor (wildfire) and all three regions (Uttarakhand, Southern California, Southeastern Australia) with justification per the selection checklist
- Add AOI boundary files (GeoJSON) for all three regions under `datasets/aoi/uttarakhand.geojson`, `datasets/aoi/california.geojson`, `datasets/aoi/australia.geojson`

**Push 2:** `docs: finalize wildfire risk factor and three-region study design`

### Milestone 1.3 — Data Collection Pipelines, Run for All Three Regions (Week 2)
- `ai/features/satellite_collection.py` — Google Earth Engine pull for Sentinel-2, NDVI/NDWI computation, parameterized by AOI so the same script runs for all three regions
- `ai/features/weather_collection.py` — weather API pull, aligned to AOI/time window, parameterized the same way
- `ai/features/label_collection.py` — FIRMS active-fire label ingestion, parameterized the same way
- Raw data saved under `datasets/raw/{uttarakhand,california,australia}/` (or documented as external if too large for git — use `.gitignore` + a `datasets/README.md` explaining how to fetch it per region)

**Push 3:** `feat: satellite, weather, and label collection pipelines (parameterized for 3 regions)`
**Push 3b:** `data: initial data pull for Uttarakhand, California, and Australia`

### Milestone 1.4 — Feature Engineering & Preprocessing (Week 2–3)
- `ai/features/build_features.py` — merges satellite, weather, historical sources into aligned, per-region feature tables; parameterized by region, run three times
- Basic exploratory data analysis notebook under `experiments/eda.ipynb`, one section per region

**Push 4:** `feat: environmental feature engineering pipeline (3-region parameterized)`

### Milestone 1.5 — Single-Source Baseline Models, Per Region (Week 3)
- `ai/prediction/single_source_models.py` — satellite-only, weather-only, historical-only models, trained and evaluated separately for each of the three regions (even with a simple split at this stage — leakage-safe evaluation gets tightened in Phase 2)
- `experiments/phase1_baseline_results.md` — logged results, one table per region

**Push 5:** `feat: single-source baseline models across all three regions`

### Milestone 1.6 — Early Frontend/Backend Integration (Week 3, end)
- FastAPI endpoint serving region metadata + placeholder risk values for all three regions
- React dashboard: real map (Leaflet) with a **region switcher** showing all three AOIs, with placeholder cards for Health Score/Risk (per the Early Integration Rule — visible before the real models are ready)
- MySQL schema created (`database/schema.sql`), with a `region` column threaded through the relevant tables, and connected

**Push 6:** `feat: dashboard-backend integration with live AOI map and placeholder risk view`
→ Tag: `v0.4-phase1-complete`

### Phase 1 Checkpoint — Update Root README
Before moving to Phase 2, update the root `README.md` progress checklist (Section 6 below) to show Phase 1 items as done. This single update is what makes a repo visitor immediately understand "this is 40% along, here's what exists."

**Push 7:** `docs: mark Phase 1 complete, update project status`

---

## 3. Phase 2 — Core Research & Full Platform (Weeks 4–8, Target: 60%)

### Milestone 2.1 — Rigorous Multi-Source Model Comparison, Per Region (Week 4)
- `ai/prediction/multi_source_model.py` — fused feature model, parameterized by region
- `ai/prediction/evaluation.py` — spatial block CV + temporal holdout implementation, run within each region
- `ai/prediction/model_comparison.py` — baseline vs RF vs XGBoost vs LightGBM, 5-seed runs, significance test, per region
- `experiments/model_comparison_results.md` — full results tables, one per region, with mean±std and p-values

**Push 8:** `feat: multi-source fusion model with spatial/temporal leakage-safe evaluation (3 regions)`
**Push 9:** `feat: per-region model comparison with multi-seed runs and significance testing`

### Milestone 2.1b — Cross-Region Generalization / LORO Evaluation (Week 4–5)
- `ai/prediction/loro_evaluation.py` — leave-one-region-out training/testing across all three region-pair combinations
- `ai/prediction/pooled_model.py` — single model trained on pooled data from all three regions, compared against per-region models
- `experiments/loro_results.md` — LORO results table, pooled vs per-region comparison

**Push 9b:** `feat: leave-one-region-out and pooled-model cross-region evaluation`

### Milestone 2.2 — SHAP Explainability, Cross-Region Comparison (Week 5, early)
- `ai/xai/shap_explain.py` — global + per-prediction SHAP explanations for the winning model in each region
- `experiments/shap_cross_region_comparison.md` — which drivers are consistent across regions vs region-specific
- SHAP plots saved and referenced in `experiments/`

**Push 10:** `feat: SHAP explainability with cross-region driver comparison`

### Milestone 2.3 — Hybrid RAG (Week 5)
- `rag/ingestion/` — document cleaning, chunking, embedding pipeline; corpus organized as `rag/corpus/shared/` (general wildfire ecology) + `rag/corpus/{region}/` (region-specific guidance/history docs)
- `rag/vector_search/`, `rag/keyword_search/` (BM25), `rag/reranking/`
- `rag/evaluation/eval_queries.json` — the 40–60 hand-labeled question/document pairs, spanning shared and region-specific questions
- `rag/evaluation/run_eval.py` — vector-only vs Hybrid comparison script + results

**Push 11:** `feat: hybrid RAG pipeline (vector + BM25 + reranker)`
**Push 12:** `feat: RAG evaluation set and vector-only vs hybrid comparison results`

### Milestone 2.4 — Explainability → Evidence → Recommendation Chain (Week 6)
- `backend/routers/recommendation.py` — combines risk + SHAP + RAG evidence into a structured recommendation response
- Wording discipline enforced here (decision-support language only)

**Push 13:** `feat: recommendation engine combining risk, SHAP, and RAG evidence`

### Milestone 2.5 — Full Dashboard & GIS (Week 6)
- Real risk overlays, before/after satellite comparison view, SHAP visualizations, RAG evidence display, recommendation display — all replacing the Phase 1 placeholders
- Region switcher fully functional: switching regions updates map, risk, SHAP, and recommendations
- Optional cross-region comparison view (side-by-side SHAP driver comparison) if time allows
- `frontend/` fully wired to real backend endpoints

**Push 14:** `feat: full dashboard integration — risk, SHAP, RAG evidence, and recommendations`
→ Tag: `v0.8-core-complete`

### Milestone 2.6 — Stretch Features (Week 7, only if Core is done and time remains)
- Health Score, LangGraph agents, alerts, PDF reports, water-body detection — each as its own push, clearly separable so they can be reverted without affecting Core if needed

**Push 15+ (as applicable):** `feat: [stretch feature name]`

### Milestone 2.7 — Testing, Deployment, Final Polish (Week 8)
- `docker-compose.yml` finalized for one-command local run
- Bug fixes, README polish, demo script

**Push N-1:** `fix: final testing and deployment fixes`
**Push N:** `docs: final README, demo instructions, and project write-up`
→ Tag: `v1.0-final`

### Paper Track (runs in parallel throughout, in its own folder — not app code, but still versioned)
- `paper/lit_review.md` (Week 1–2), `paper/methodology_draft.md` (Week 3), `paper/results_draft.md` (Week 4–5), `paper/full_draft.md` (Week 7), `paper/final_submission.pdf` (Week 8)
- Push each draft update on its own commit under `docs:` or `paper:` prefix so the paper's evolution is visible in history too

---

## 4. Commit Message Convention

Use prefixes consistently so the commit log itself reads like a changelog:

| Prefix | Use for |
|---|---|
| `feat:` | New functionality (models, pipelines, endpoints, UI features) |
| `fix:` | Bug fixes |
| `docs:` | README, AOI docs, paper drafts, progress updates |
| `data:` | Dataset additions, label/feature pipeline changes |
| `experiment:` | Logged experiment results, evaluation runs |
| `refactor:` | Code restructuring without behavior change |

This alone makes the repo self-explanatory — someone scrolling the commit log sees `feat → data → feat → experiment → docs` and understands the project's build order without reading anything else.

---

## 5. Branching (Keep It Simple for a 3-Person Team)

- `main` — always working, always demoable
- One short-lived feature branch per person per milestone (e.g. `feature/multi-source-model`, `feature/rag-pipeline`), merged into `main` via a small pull request once that milestone's tests/demo work
- Tag `main` at the end of each phase and at major milestones (`v0.1-scaffold`, `v0.4-phase1-complete`, `v0.8-core-complete`, `v1.0-final`) — tags let anyone jump straight to "what did the repo look like at 40%" vs "at 100%"

Don't over-engineer branching for a 3-person 8-week project — the tags matter more than the branch strategy here.

---

## 6. Root README Progress Checklist (Keep This Updated — This Is What Makes the Repo Self-Explanatory)

Add this block near the top of the root `README.md` and check items off as each push lands. A visitor should be able to read this and the commit log together and understand exactly where the project stands without asking anyone.

```markdown
## Project Status

### Phase 1 — Foundation (Target: 40%)
- [ ] Repo scaffolding (backend, frontend, docker)
- [ ] AOI and risk target finalized
- [ ] Satellite, weather, and label data pipelines
- [ ] Feature engineering pipeline
- [ ] Single-source baseline models
- [ ] Dashboard-backend integration (live map + placeholders)

### Phase 2 — Core Research & Platform (Target: 60%)
- [ ] Multi-source fusion model
- [ ] Leakage-safe evaluation (spatial + temporal) with significance testing
- [ ] SHAP explainability
- [ ] Hybrid RAG pipeline
- [ ] RAG evaluation (vector-only vs hybrid)
- [ ] Explainability → evidence → recommendation chain
- [ ] Full dashboard and GIS integration
- [ ] Stretch features (if time allows)
- [ ] Final testing and deployment
- [ ] IEEE paper draft and submission
```

---

## 7. Quick Reference — Push Order Summary

| # | Week | Push | Tag |
|---|---|---|---|
| 1 | 1 | Repo scaffolding | v0.1-scaffold |
| 2 | 1 | Risk factor + 3-region decision docs | |
| 3, 3b | 2 | Data collection pipelines + initial pull for all 3 regions | |
| 4 | 2–3 | Feature engineering (3-region parameterized) | |
| 5 | 3 | Single-source baselines, all 3 regions | |
| 6 | 3 | Dashboard-backend integration with region switcher | v0.4-phase1-complete |
| 7 | 3 | README status update (Phase 1 done) | |
| 8–9 | 4 | Multi-source model + per-region rigorous comparison | |
| 9b | 4–5 | LORO + pooled cross-region evaluation | |
| 10 | 5 | SHAP explainability + cross-region comparison | |
| 11–12 | 5 | Hybrid RAG (shared + region corpus) + evaluation | |
| 13 | 6 | Recommendation chain | |
| 14 | 6 | Full dashboard/GIS integration with region switcher | v0.8-core-complete |
| 15+ | 7 | Stretch features (optional, separate commits) | |
| N-1, N | 8 | Final fixes + docs | v1.0-final |

Push at the end of each milestone, not at the end of each day — a commit should represent one working, demoable unit, so anyone checking out any tagged commit sees a functioning (if partial) system.
