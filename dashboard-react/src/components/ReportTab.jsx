import React, { useState } from 'react';
import { FileText, Presentation, CheckCircle, Shield, Download } from 'lucide-react';

export default function ReportTab() {
  const [subView, setSubView] = useState('report');

  const deliverables = [
    { title: "Synthetic Data Generator", path: "outputs/access_logs.csv", desc: "7 attack types + concept drift + cold-start entities" },
    { title: "Baseline Profiling Model", path: "outputs/models/profiles.pkl", desc: "Per-entity mean/std and entity_type population baselines" },
    { title: "Detection Model & Risk Scorer", path: "outputs/models/isolation_forest.pkl", desc: "IsolationForest + Personal Z-score + Markov sequence log-likelihood" },
    { title: "Anomaly-Type Classification", path: "outputs/models/classifier.pkl", desc: "RandomForest/XGBoost multi-class classifier (0.90 F1)" },
    { title: "Explainability Layer", path: "outputs/scored_events.csv", desc: "SHAP/z-score attribution with [PERSONAL], [POPULATION], [SEQUENCE] source tags" },
    { title: "Analyst Dashboard", path: "dashboard-react", desc: "Full React + Streamlit SOC Analyst Interfaces" },
    { title: "Technical Report", path: "outputs/report.md", desc: "Comprehensive technical document detailing methodology & metrics" },
    { title: "Slide-Deck Presentation", path: "outputs/presentation.md", desc: "10-slide executive pitch deck for Honeywell Hackathon" },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Sub-view Navigation Header */}
      <div className="glass-card" style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button 
            onClick={() => setSubView('report')}
            className={`btn ${subView === 'report' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <FileText size={16} /> Technical Report (Markdown)
          </button>
          <button 
            onClick={() => setSubView('slides')}
            className={`btn ${subView === 'slides' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Presentation size={16} /> Hackathon Slide Deck
          </button>
        </div>

        <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <CheckCircle size={14} /> All 8 Problem Deliverables Complete
        </span>
      </div>

      {/* Deliverables Checklist Grid */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '4px' }}>Deliverables Verification Matrix</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>1:1 mapping to Honeywell problem statement requirements</p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
          {deliverables.map((item, i) => (
            <div key={i} style={{ padding: '12px 16px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <div style={{ color: '#10B981', marginTop: '2px' }}>
                <CheckCircle size={18} />
              </div>
              <div>
                <div style={{ fontWeight: '700', fontSize: '0.85rem' }}>{item.title}</div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{item.desc}</p>
                <span className="mono" style={{ fontSize: '0.7rem', color: '#818CF8', marginTop: '4px', display: 'block' }}>{item.path}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Content Display Card */}
      <div className="glass-card" style={{ padding: '32px' }}>
        {subView === 'report' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', lineHeight: '1.7' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '800' }} className="gradient-text">
              AI-Powered Behavioral Anomaly Detection for Cybersecurity — Technical Report
            </h2>
            
            <div style={{ padding: '16px', borderRadius: '10px', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}>
              <h4 style={{ color: '#A5B4FC', fontWeight: '700' }}>Architecture & Pipeline Design</h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                The solution consists of 8 modular Python subsystems executing causally from synthetic sequence log generation (`data_generator.py`), 
                causal feature computation with Markov transition matrices (`feature_engineering.py`), IsolationForest joint anomaly detection + statistical baseline z-scoring (`models.py`), 
                RandomForest/XGBoost attack classification (`models.py`), SHAP/z-score per-alert explainability with inference source tags (`explainability.py`), 
                and comprehensive evaluation (`evaluation.py`).
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div style={{ padding: '16px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontWeight: '700', marginBottom: '8px' }}>Handling 5 Core Requirements</h4>
                <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '20px' }}>
                  <li><strong>Sequential Data:</strong> Causal feature computation, Markov command transition probability, chronological train/test split.</li>
                  <li><strong>Class Imbalance:</strong> PR-AUC primary metric, IsolationForest unsupervised detection, balanced class weighting.</li>
                  <li><strong>Concept Drift:</strong> Exponential Moving Average (EMA, α=0.05) online baseline updating to taper alerts for shifted habits.</li>
                  <li><strong>Explainability:</strong> Top-3 feature attribution strings with source tags ([PERSONAL], [POPULATION], [SEQUENCE]).</li>
                  <li><strong>Cold-Start:</strong> Entity-type population baseline fallback for entities with &lt; 5 sessions.</li>
                </ul>
              </div>

              <div style={{ padding: '16px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontWeight: '700', marginBottom: '8px' }}>Attack Taxonomy Injected</h4>
                <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '20px' }}>
                  <li>Brute Force (Rapid failed-auth bursts)</li>
                  <li>Impossible Travel (&gt;5000 km velocity gaps)</li>
                  <li>Credential Stuffing (Multi-entity same-IP bursts)</li>
                  <li>Lateral Movement (Unusual resource sequence expansion)</li>
                  <li>Device Spoofing (MAC/OS fingerprint mismatches)</li>
                  <li>Low-and-Slow Exfiltration (Gradual off-hours access)</li>
                  <li>Insider Drift (Ambiguous footprint expansion)</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '800' }} className="gradient-text">
              Honeywell Hackathon Slide Deck Pitch
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
              <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(15,23,42,0.8)', border: '1px solid var(--border-color)' }}>
                <span className="badge badge-tag" style={{ marginBottom: '8px' }}>SLIDE 1</span>
                <h4 style={{ fontWeight: '700' }}>The Problem</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  Traditional signature-based security fails against novel or low-and-slow intrusions. We model "normal" behavioral access trails across users, service accounts, and edge IoT devices.
                </p>
              </div>

              <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(15,23,42,0.8)', border: '1px solid var(--border-color)' }}>
                <span className="badge badge-tag" style={{ marginBottom: '8px' }}>SLIDE 2</span>
                <h4 style={{ fontWeight: '700' }}>End-to-End Pipeline</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  A unified pipeline running locally with one command (`python main.py`), generating reproducible synthetic access logs, causal feature matrix, IsolationForest risk models, and interactive SOC dashboard.
                </p>
              </div>

              <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(15,23,42,0.8)', border: '1px solid var(--border-color)' }}>
                <span className="badge badge-tag" style={{ marginBottom: '8px' }}>SLIDE 3</span>
                <h4 style={{ fontWeight: '700' }}>Sequence & Risk Scoring</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  Ensemble 0–100 risk score combining multivariate IsolationForest, personal baseline z-scores, and Markov transition command sequence surprisability log-likelihood.
                </p>
              </div>

              <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(15,23,42,0.8)', border: '1px solid var(--border-color)' }}>
                <span className="badge badge-tag" style={{ marginBottom: '8px' }}>SLIDE 4</span>
                <h4 style={{ fontWeight: '700' }}>SOC Analyst Experience</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  Ranked alert queue, instant feature attribution explaining *why* an event was flagged, inference source tagging, and full entity timeline drill-down.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
