import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import OverviewTab from './components/OverviewTab';
import AlertsTab from './components/AlertsTab';
import InvestigatorTab from './components/InvestigatorTab';
import PerformanceTab from './components/PerformanceTab';
import ReportTab from './components/ReportTab';

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedEntityId, setSelectedEntityId] = useState(null);

  useEffect(() => {
    fetch('/data.json')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load data.json');
        return res.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching dashboard data:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleSelectEntity = (entityId) => {
    setSelectedEntityId(entityId);
    setActiveTab('investigator');
  };

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#090D16',
        color: '#F9FAFB'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          borderRadius: '50%',
          border: '3px solid rgba(99,102,241,0.2)',
          borderTopColor: '#6366F1',
          animation: 'spin 1s linear infinite'
        }}></div>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        <p style={{ marginTop: '20px', fontWeight: '600', color: 'var(--text-secondary)' }}>Loading CyberShield Telemetry & ML Scored Events...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '50px', textAlign: 'center', color: '#EF4444' }}>
        <h2>Error Loading Dashboard Data</h2>
        <p>{error || 'data.json not found in public directory.'}</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-dark)' }}>
      <Header summary={data.summary} activeTab={activeTab} setActiveTab={setActiveTab} />

      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        <main style={{ flex: 1, padding: '28px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
          {activeTab === 'overview' && (
            <OverviewTab data={data} onSelectEntity={handleSelectEntity} setActiveTab={setActiveTab} />
          )}

          {activeTab === 'alerts' && (
            <AlertsTab events={data.events} onSelectEntity={handleSelectEntity} />
          )}

          {activeTab === 'investigator' && (
            <InvestigatorTab data={data} selectedEntityId={selectedEntityId} onSelectEntity={handleSelectEntity} />
          )}

          {activeTab === 'performance' && (
            <PerformanceTab data={data} />
          )}

          {activeTab === 'reports' && (
            <ReportTab />
          )}
        </main>
      </div>
    </div>
  );
}
