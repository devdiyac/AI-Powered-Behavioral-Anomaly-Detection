import React from 'react';
import { Shield, ShieldAlert, Activity, Cpu, Bell } from 'lucide-react';

export default function Header({ summary, activeTab, setActiveTab }) {
  const criticalCount = summary?.total_anomalies || 0;

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 28px',
      background: 'var(--header-bg)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-color)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      {/* Brand / Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)'
        }}>
          <Shield size={24} color="#FFF" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '10px' }}>
            CyberShield <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '6px', background: 'rgba(99,102,241,0.2)', color: 'var(--link-color)', border: '1px solid rgba(99,102,241,0.3)' }}>v2.4 SOC ML</span>
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
            AI-Powered Behavioral Anomaly Detection & Threat Intelligence
          </p>
        </div>
      </div>

      {/* Live System Indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '20px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          fontSize: '0.8rem',
          color: 'var(--success-text)'
        }}>
          <span className="animate-pulse-slow" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success-dot)' }}></span>
          <span style={{ fontWeight: '600' }}>ONLINE</span>
          <span style={{ opacity: 0.6 }}>|</span>
          <Cpu size={14} />
          <span>IsolationForest + Markov Chain</span>
        </div>

        <button 
          onClick={() => setActiveTab('alerts')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '10px',
            background: criticalCount > 0 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255,255,255,0.05)',
            border: criticalCount > 0 ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid var(--border-color)',
            color: criticalCount > 0 ? 'var(--danger-text)' : 'var(--text-primary)',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '0.85rem'
          }}
        >
          <Bell size={16} color={criticalCount > 0 ? 'var(--risk-critical)' : 'var(--text-secondary)'} />
          <span>{criticalCount} Detected Anomalies</span>
        </button>
      </div>
    </header>
  );
}
