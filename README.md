# 🛡️ CyberShield — AI-Powered Behavioral Anomaly Detection Engine

> **Honeywell Hackathon Submission**  
> An end-to-end, domain-agnostic AI/ML pipeline that models "normal" access behavior for users, service accounts, and edge IoT devices, detects intrusions in near real-time, classifies attack categories, and provides explainable risk scores with a modern React SOC Analyst dashboard.

---

## 📸 Dashboard Overview

![CyberShield Executive Overview](outputs/metrics/pr_curve.png)

CyberShield includes a **production-grade React SOC Analyst Dashboard** with glassmorphism design, real-time telemetry, filterable alert queues, entity drill-downs, and a **Light / Dark mode** toggle.

---

## ⚡ Quick Start

### 1. Prerequisites & Environment Setup

```bash
# Clone the repository
git clone https://github.com/devdiyac/AI-Powered-Behavioral-Anomaly-Detection.git
cd AI-Powered-Behavioral-Anomaly-Detection

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run the Full ML Pipeline

Execute all 7 pipeline steps sequentially (data generation, feature extraction, model fitting, scoring, explainability, evaluation, and report generation):

```bash
python main.py
```

> **Execution Time:** ~97 seconds  
> **Output:** All 16 artifacts (scored CSVs, trained models, evaluation charts, markdown report) generated in `outputs/`.

### 3. Launch the React Analyst Dashboard

```bash
cd dashboard-react
npm install
npm run dev
```

Open **`http://localhost:3000`** in your browser to interact with the CyberShield dashboard.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Data Layer
        A[data_generator.py] -->|34,500 Access Events| B[(outputs/access_logs.csv)]
    end

    subgraph Feature Engineering Layer
        B --> C[feature_engineering.py]
        C -->|Rolling Temporal Features| D1[Entity Profile Tracker]
        C -->|Haversine Geo Velocity| D2[Geo Engine]
        C -->|Command Token Sequence| D3[Markov Transition Matrix]
        D1 & D2 & D3 -->|12 Causal Features| E[(outputs/features.csv)]
    end

    subgraph Modeling Layer
        E --> F[models.py]
        F -->|Fit Habitual Baselines| G1[BaselineProfiler]
        F -->|Multivariate Outliers| G2[IsolationForest]
        F -->|0-100 Risk Ensemble| G3[RiskScorer]
        F -->|Attack Categorization| G4[RandomForest AnomalyClassifier]
        F -->|EMA Profile Decay| G5[ConceptDriftAdapter]
    end

    subgraph Attribution & Scoring Layer
        G3 & G4 & G5 --> H[explainability.py]
        H -->|Z-Score / SHAP + Inference Tagging| I[(outputs/scored_events.csv)]
    end

    subgraph Evaluation & UI Layer
        I --> J[evaluation.py]
        I --> K[prepare_dashboard_data.py]
        J -->|PR-AUC / Confusion Matrix / Alert Budget| L[(outputs/metrics/)]
        K -->|JSON Bundle| M[dashboard-react/ React App]
    end
```

---

## 🌟 Core Technical Innovations

### 1. Causal Feature Engineering (Zero Data Leakage)
Turns raw event logs into a 12-dimensional feature matrix where each event is evaluated **strictly using prior history**. Includes rolling login hour deviations, haversine geo-velocity ($\text{km/h}$), auth failure streaks, and new resource/device flags.

### 2. Sequence-Aware Markov Transition Model
Privileged session command strings (e.g. `["sudo", "cat /etc/shadow"]`) are modeled using a lightweight **Markov Chain transition probability matrix**, calculating log-likelihood surprisability scores without GPU overhead.

### 3. Ensemble Risk Scoring (0–100)
Combines unsupervised **IsolationForest** outlier probabilities, personal $z$-score deviations, and Markov sequence surprisability into a unified, calibrated 0–100 Risk Score.

### 4. Supervised Anomaly Classifier (**0.90 Weighted F1**)
Predicts the exact attack category once an anomaly is flagged across 7 distinct attack taxonomies:
- 🔨 **Brute Force:** Rapid repeated failed logins (F1: **0.95**)
- 🔑 **Credential Stuffing:** High failure rate across multiple entities (F1: **0.97**)
- 🌐 **Lateral Movement:** Accessing unusual sequence/breadth of sensitive endpoints (F1: **0.94**)
- ✈️ **Impossible Travel:** Physical velocity $>5000\text{ km/h}$ between sessions (F1: **0.73**)
- 📱 **Device Spoofing:** Discrepant OS/MAC fingerprint vs entity history (F1: **0.84**)
- 🐢 **Low-and-Slow Exfiltration:** Gradual off-hours access over days/weeks (F1: **0.82**)
- 📈 **Insider Drift:** Legitimate footprint expansion for false-positive tuning (F1: **0.76**)

### 5. EMA Concept Drift Adapter
Uses Exponential Moving Average ($\alpha=0.05$) to incrementally update baseline profiles online as new normal habits accumulate, preventing permanent blacklisting of evolving legitimate behavior.

### 6. Cold-Start Population Fallbacks
Maintains population-level statistics aggregated per `entity_type` (`user`, `service_account`, `edge_device`) as a safe fallback baseline for new entities with $<5$ sessions.

### 7. Explainability & Inference Source Tagging
Every alert includes human-readable feature attribution strings tagged with its explicit inference source:
- `[PERSONAL]`: Deviated from the entity's own baseline profile.
- `[SEQUENCE]`: Flagged by the Markov command sequence model.
- `[POPULATION]`: Flagged against population baselines (cold-start).

---

## 📊 Empirical Evaluation Summary

| Metric | Score | Note |
|---|---|---|
| **Attack Classifier Weighted F1** | **0.90** | Supervised classification across 7 attack types |
| **Detection ROC-AUC** | **0.768** | Joint feature separation score |
| **Detection PR-AUC** | **0.381** | Class imbalance-resilient evaluator ($11.7\%$ anomaly rate) |
| **Recall @ Top 1% Alert Budget** | **40.0%** | Intrusions caught within top 1% analyst review budget |
| **Total Monitored Events** | **34,500** | 10,359 scored in chronological test set |

---

## 📁 Repository Structure

```
.
├── config.py                  # Global hyperparameters, seeds, & feature schema
├── utils.py                   # Math helpers (Haversine), logging, & env checks
├── data_generator.py          # Synthetic access log engine (34.5K logs, 7 attacks)
├── feature_engineering.py     # Causal feature matrix & Markov sequence model
├── models.py                  # BaselineProfiler, IsolationForest, RiskScorer, AnomalyClassifier
├── explainability.py          # SHAP/z-score attribution & inference source tagging
├── evaluation.py              # Chronological train/test split, PR-AUC, confusion matrix
├── report.py                  # Technical report & 10-slide deck generator
├── main.py                    # Single-command orchestrator (runs full pipeline)
├── prepare_dashboard_data.py  # Bundles pipeline outputs into dashboard JSON
├── requirements.txt           # Python dependency requirements
├── dashboard.py               # Alternative Streamlit dashboard
├── dashboard-react/           # Production React SOC Analyst Web App
│   ├── src/
│   │   ├── components/        # OverviewTab, AlertsTab, InvestigatorTab, PerformanceTab
│   │   ├── App.jsx            # Main React layout & state manager
│   │   └── index.css          # Theme-aware CSS design system (Light/Dark Mode)
│   └── public/data.json       # Pre-bundled telemetry data
└── outputs/                   # Generated pipeline deliverables (CSVs, models, plots)
```

---

## ✅ Deliverables Checklist (Honeywell Hackathon)

- [x] **1. Synthetic Data Generator:** reproducible access log generator with injected attack taxonomy.
- [x] **2. Baseline Profiling Model:** per-entity statistical profiles + population fallback.
- [x] **3. Detection Model:** sequence-aware IsolationForest + Z-score ensemble risk scorer (0–100).
- [x] **4. Anomaly Classification:** supervised multi-class attack category classifier.
- [x] **5. Explainability Layer:** per-alert feature attribution with explicit inference source tagging.
- [x] **6. Analyst Dashboard:** React & Streamlit SOC dashboards featuring ranked alert queue, entity drill-downs, and theme toggling.
- [x] **7. Technical Report:** comprehensive markdown report covering architecture, metrics, and limitations (`outputs/report.md`).
- [x] **8. Presentation Slide Deck:** 10-slide summary deck for competition submission (`outputs/presentation.md`).

---

## 📜 License

Distributed under the MIT License.
