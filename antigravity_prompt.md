# Prompt for Antigravity

Copy everything below into Antigravity as your task/agent prompt.

---

## Project: AI-Powered Behavioral Anomaly Detection for Cybersecurity

Build a complete, working, self-contained solution for a hackathon problem statement (Honeywell). I need production-quality code, not a toy notebook. Work in Python. Assume no internet access at runtime for the final artifact (but you can use pip during setup). Target: a end-to-end pipeline I can run locally with one command, plus a report and a dashboard.

### Context / problem statement

Every login, API call, or device connection leaves a behavioral trail — timing, location, access patterns, command sequences, protocol usage. Traditional signature-based security fails against novel or slow, low-and-slow intrusions. The goal is behavioral anomaly detection: learn what "normal" access looks like for a user, service account, or device, and flag deviations — regardless of whether the target is a cloud server, an industrial edge gateway, a POS terminal, or a home IoT hub. The ML task (sequence and behavioral anomaly detection on access logs) is domain-agnostic.

**Task:** Design and build an AI/ML system that models "normal" access and connection behavior for users and devices, detects intrusions or compromised-credential activity in near real-time, and classifies the type of anomaly (e.g., credential misuse, lateral movement, brute force, impossible travel, device spoofing) — with an explainable risk score.

**Must handle:**
1. Sequential and behavioral data — access events over time, not static snapshots.
2. Extreme class imbalance — true intrusions are a tiny fraction of total access events.
3. Concept drift — legitimate behavior evolves (new work patterns, new devices) and should not be permanently flagged.
4. Explainability — a SOC analyst needs to know *why* an event was flagged, not just a score.
5. Cold-start problem — how to score a brand-new user or device with no history.

### Synthetic data requirement

Real intrusion/access-log datasets are scarce, outdated, privacy-restricted, or domain-specific. Build a **synthetic data generator** (Python, numpy/pandas — do not depend on external data downloads since there's no guaranteed internet access) that produces access-log data using this schema, with injected attack patterns at a controlled rate (0.5%–3% of sessions):

| Field | Description |
|---|---|
| entity_id | user_id or device_id |
| entity_type | user / service_account / edge_device |
| timestamp | access or connection time |
| source_ip / geo_location | origin of the access |
| resource_accessed | file, endpoint, port, or device function |
| auth_method | password, token, certificate, biometric |
| session_duration | length of connection |
| command_sequence | ordered list of actions taken (for privileged sessions) |
| device_fingerprint | OS/firmware version, MAC address, protocol used |
| label | normal / anomaly_type (for training & evaluation only — hidden at inference) |

Simulate these behavior patterns, each with a defined "simulation approach":

| Pattern | Simulation approach | Signal |
|---|---|---|
| Normal baseline | Per-entity habitual pattern: regular login hours, consistent geo, typical resource set, sampled with noise | Benign |
| Brute force | Rapid repeated failed-auth attempts from one source in a short window | Anomaly |
| Impossible travel | Same entity_id logging in from geographically distant locations within an implausible time gap | Anomaly |
| Credential stuffing | Many entity_ids, few source_ips, high failure rate | Anomaly |
| Lateral movement | A compromised entity accessing an unusual sequence/breadth of resources it never touched before | Anomaly |
| Device spoofing | A device_id reappearing with a mismatched fingerprint (different OS/MAC than history) | Anomaly |
| Low-and-slow exfiltration | Gradual, small, off-hours resource access building up over days/weeks | Anomaly |
| Insider drift | Legitimate entity slowly expanding privilege/resource footprint — ambiguous, used for false-positive tuning | Edge case |

Build per-entity behavioral profiles first (habitual login hours, home geo, typical resource set, typical device fingerprint), then inject the above patterns at controlled rates on top, retaining ground-truth labels separately from what the model sees at inference.

### Required architecture / pipeline

Build these as clearly separated modules:

1. **`data_generator.py`** — synthetic access-log generator per the schema/patterns above. Produces a reproducible (seeded), timestamp-sorted CSV. Include a small pool of brand-new entities that only appear near the end of the time range (to exercise the cold-start path).

2. **`feature_engineering.py`** — turns raw log rows into a feature matrix, computed **causally** (each session scored using only that entity's history *before* it — no leakage). Include:
   - Rolling/temporal features: deviation from personal typical login hour, geo-velocity (km/h between consecutive sessions using haversine distance), time since last session, session count so far (for cold-start detection), auth failure streak.
   - Behavioral flags: new-resource-for-this-entity flag, new-device-fingerprint-for-this-entity flag.
   - Sequence-awareness: a lightweight Markov transition-probability model (or if you have GPU/deep-learning available, an LSTM/GRU/Transformer sequence model) over `command_sequence` tokens per entity_type, producing a sequence log-likelihood score (rare/unlikely transitions = surprising sequence = higher risk). Prefer starting with the Markov approach for speed/explainability, and layer in a neural sequence model only if time and environment allow (check for GPU/torch/tensorflow availability first — don't assume it's present).
   - Maintain population-level (per entity_type) statistics as a **cold-start fallback baseline** for entities with insufficient history.

3. **`models.py`**:
   - **Baseline profiling model** — per-entity statistical profile (mean/std per feature) *and* an unsupervised **IsolationForest** (or One-Class SVM / autoencoder if a deep-learning stack is available) fit on the joint feature space to catch multivariate anomalies a single feature's z-score would miss.
   - **Detection model** — combine (a) IsolationForest anomaly score, (b) personal z-score deviation from the entity's own baseline (falling back to population/entity_type baseline for cold-start entities), and (c) the sequence log-likelihood score into a single weighted **0–100 risk score**. Make the weights configurable.
   - **Anomaly classification** — supervised classifier (RandomForest/XGBoost — check what's installed, don't assume XGBoost is available) trained on the labeled synthetic anomaly types, to predict *which* attack category an alert resembles (not just anomalous/not).
   - **Concept drift handling** — profiles must update online/incrementally as new normal behavior accumulates, so a legitimately new pattern (new device, new working hours) stops being flagged after it's established, rather than being permanently blacklisted. Document/demonstrate this explicitly (e.g. a scenario where a user's habits shift and alerts taper off over subsequent sessions).

4. **`explainability.py`** — per-alert feature attribution. Use SHAP if it can be installed in the environment; otherwise fall back to RandomForest `feature_importances_` for global importance plus per-alert top-3 contributing features via z-score deviation, phrased as a human-readable reason string, e.g. `"flagged due to geo-velocity (4.2 std above personal baseline) + new device fingerprint"`. Tag every explanation with its inference source (personal history vs. population/cold-start baseline vs. sequence model) — this is an explicit deliverable requirement ("tag every suggestion with possible source of inference").

5. **Evaluation** (this is graded — implement carefully):
   - Do a **chronological** train/test split (not random) to respect the sequential nature of the data and simulate a realistic deployment.
   - Report: precision/recall/F1 and PR-AUC (not just ROC-AUC, given class imbalance) for detection; per-class precision/recall/F1 and a confusion matrix for anomaly-type classification.
   - Report **false positive rate at a realistic analyst alert budget** — e.g., if only the top 1% of scored events can be reviewed by a SOC analyst, what fraction of true intrusions are captured (recall@top-1%) and what's the false-positive rate within that budget? Plot precision/recall vs. alert-budget-percentile.
   - Explicitly demonstrate cold-start handling: show detection performance/behavior for the newly-introduced entities separately.
   - Explicitly demonstrate concept-drift handling: show that a legitimate behavior shift stops triggering alerts after enough supporting history accumulates.

6. **Analyst-facing dashboard** — a self-contained HTML file (embed data/charts directly, don't depend on a live backend or external CDN so it works offline for judges) showing:
   - Ranked alert queue (risk score descending), with entity_id, timestamp, predicted anomaly type + confidence, and the explainability reason string.
   - Per-alert drill-down: contributing factors, entity's recent history/context.
   - Summary charts: alerts over time, risk score distribution, anomaly-type breakdown, detection metrics.
   - Keep it clean and legible — this is what a SOC analyst would actually look at.

7. **Report** (Markdown, convertible to PDF) covering: architecture diagram (as a text/mermaid description if no image tool available), methodology per deliverable above, the data schema and generation assumptions, all evaluation metrics with plots, explicit discussion of assumptions and known limitations (e.g., synthetic data may not capture real adversarial adaptation; Markov sequence model is a lightweight stand-in for a full sequence neural model; etc.), and how each of the 5 "must handle" requirements (imbalance, drift, explainability, cold-start, sequential data) is addressed.

### Constraints / good practices

- Detect what's actually installed (numpy/pandas/sklearn should be safe defaults; check before assuming faker, xgboost, shap, torch, tensorflow are available — degrade gracefully to sklearn-only equivalents if not, and note the substitution in the report rather than failing).
- No hardcoded absolute paths outside the project folder; everything should run via a single `main.py` (or `make run`) from the project root and regenerate all artifacts (data, models, metrics, dashboard, report) into an `outputs/` folder.
- Seed everything for reproducibility.
- Keep the codebase modular (separate files per the modules above), documented with docstrings, and free of dead code.
- Write a top-level `README.md` explaining how to run it, the architecture, and where to find each deliverable.

### Final deliverables checklist (map 1:1 to the problem statement's required deliverables)

1. Synthetic data generator with documented behavioral assumptions and injected attack taxonomy.
2. Baseline profiling model (per-entity "normal" behavior representation).
3. Detection model (sequence-aware, flags deviations).
4. Anomaly classification (which attack category, not just anomalous/not).
5. Explainability layer (feature attribution per alert).
6. Analyst-facing dashboard (ranked alert queue, risk score, contributing factors, entity history view).
7. Report (assumptions, metrics, known limitations).
8. A short slide-deck-style summary (markdown or reveal.js is fine) covering the same points, since a presentation is also required for submission.

Build all of this now, run it end-to-end, fix any errors until it runs cleanly, and summarize the final evaluation numbers when done.
