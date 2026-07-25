import React from 'react';
import { LayoutDashboard, AlertTriangle, Search, Activity, FileText } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const menuItems = [
    { id: 'overview', label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'alerts', label: 'Ranked Alert Queue', icon: AlertTriangle },
    { id: 'investigator', label: 'Entity Investigator', icon: Search },
    { id: 'performance', label: 'Model Evaluation', icon: Activity },
    { id: 'reports', label: 'Reports & Slides', icon: FileText },
  ];

  return (
    <aside style={{
      width: '260px',
      background: 'rgba(15, 23, 42, 0.6)',
      borderRight: '1px solid var(--border-color)',
      padding: '24px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <div style={{ padding: '0 12px 12px 12px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Navigation
      </div>

      {menuItems.map(item => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '10px',
              border: 'none',
              background: isActive ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(79, 70, 229, 0.1) 100%)' : 'transparent',
              color: isActive ? '#A5B4FC' : 'var(--text-secondary)',
              fontWeight: isActive ? '700' : '500',
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              borderLeft: isActive ? '3px solid #6366F1' : '3px solid transparent',
              textAlign: 'left'
            }}
            onMouseEnter={e => {
              if (!isActive) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
            }}
            onMouseLeave={e => {
              if (!isActive) e.currentTarget.style.background = 'transparent';
            }}
          >
            <Icon size={18} color={isActive ? '#818CF8' : 'var(--text-muted)'} />
            <span>{item.label}</span>
          </button>
        );
      })}

      <div style={{ marginTop: 'auto', padding: '16px', borderRadius: '12px', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)' }}>
        <p style={{ fontSize: '0.75rem', fontWeight: '700', color: '#818CF8', marginBottom: '4px' }}>Honeywell Hackathon</p>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Domain-Agnostic Behavioral Sequence Anomaly Detection Pipeline</p>
      </div>
    </aside>
  );
}
