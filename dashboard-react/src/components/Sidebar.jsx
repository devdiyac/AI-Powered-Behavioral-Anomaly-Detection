import React from 'react';
import { LayoutDashboard, AlertTriangle, Search, Activity, Sun, Moon } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, theme, setTheme }) {
  const menuItems = [
    { id: 'overview', label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'alerts', label: 'Ranked Alert Queue', icon: AlertTriangle },
    { id: 'investigator', label: 'Entity Investigator', icon: Search },
    { id: 'performance', label: 'Model Evaluation', icon: Activity },
  ];

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
  };

  return (
    <aside style={{
      width: '260px',
      background: 'var(--sidebar-bg)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      borderRight: '1px solid var(--border-color)',
      padding: '24px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      transition: 'background 0.3s ease'
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
              if (!isActive) e.currentTarget.style.background = 'var(--table-row-hover)';
            }}
            onMouseLeave={e => {
              if (!isActive) e.currentTarget.style.background = 'transparent';
            }}
          >
            <Icon size={18} color={isActive ? 'var(--link-color)' : 'var(--text-muted)'} />
            <span>{item.label}</span>
          </button>
        );
      })}

      {/* Theme toggle button at bottom */}
      <button
        onClick={toggleTheme}
        style={{
          marginTop: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px',
          padding: '12px 16px',
          borderRadius: '10px',
          border: '1px solid var(--border-color)',
          background: 'var(--bg-card)',
          color: 'var(--text-secondary)',
          fontSize: '0.85rem',
          fontWeight: '600',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={e => {
          e.currentTarget.style.borderColor = 'var(--border-highlight)';
          e.currentTarget.style.color = 'var(--text-primary)';
        }}
        onMouseLeave={e => {
          e.currentTarget.style.borderColor = 'var(--border-color)';
          e.currentTarget.style.color = 'var(--text-secondary)';
        }}
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
      </button>
    </aside>
  );
}
