import React, { useState, useMemo } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';
import { Search, UserCheck, ShieldAlert, Cpu, MapPin, Key, Clock, AlertCircle } from 'lucide-react';

export default function InvestigatorTab({ data, selectedEntityId, onSelectEntity }) {
  const { events } = data;

  // Extract list of all unique entity IDs
  const allEntityIds = useMemo(() => {
    return Array.from(new Set(events.map(e => e.entity_id))).sort();
  }, [events]);

  const [activeEntity, setActiveEntity] = useState(selectedEntityId || allEntityIds[0] || '');

  // Update active entity if prop changes
  React.useEffect(() => {
    if (selectedEntityId) setActiveEntity(selectedEntityId);
  }, [selectedEntityId]);

  // Events for selected entity
  const entityEvents = useMemo(() => {
    return events.filter(e => e.entity_id === activeEntity).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  }, [events, activeEntity]);

  if (!entityEvents || entityEvents.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Select an entity to investigate history and feature attribution.</p>
      </div>
    );
  }

  const latestEvent = entityEvents[entityEvents.length - 1];
  const highestRiskEvent = [...entityEvents].sort((a, b) => b.risk_score - a.risk_score)[0];

  // Extract top features for highest risk event
  const topFeatures = highestRiskEvent?.top_features || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Entity Selector Bar */}
      <div className="glass-card" style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Search size={20} color="var(--link-color)" />
          <span style={{ fontWeight: '700', fontSize: '0.9rem' }}>Investigate Entity:</span>
          <select 
            value={activeEntity}
            onChange={e => setActiveEntity(e.target.value)}
            className="input-field mono"
            style={{ fontWeight: '700', fontSize: '0.95rem', color: 'var(--entity-color)', padding: '8px 16px' }}
          >
            {allEntityIds.map(eid => (
              <option key={eid} value={eid} style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>{eid}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className="badge badge-tag">{latestEvent.entity_type}</span>
          {latestEvent.is_cold_start === 1 ? (
            <span className="badge badge-medium">COLD-START [POPULATION BASELINE]</span>
          ) : (
            <span className="badge badge-low">ESTABLISHED PROFILE [PERSONAL]</span>
          )}
        </div>
      </div>

      {/* Entity Overview Header Card */}
      <div className="glass-card" style={{ padding: '24px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>ENTITY IDENTIFIER</span>
          <h2 className="mono" style={{ fontSize: '1.4rem', fontWeight: '800', marginTop: '4px', color: 'var(--entity-color)' }}>{activeEntity}</h2>
        </div>

        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>MONITORED SESSIONS</span>
          <div className="mono" style={{ fontSize: '1.4rem', fontWeight: '800', marginTop: '4px' }}>{entityEvents.length}</div>
        </div>

        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>PEAK RISK SCORE</span>
          <div className="mono" style={{ fontSize: '1.4rem', fontWeight: '800', marginTop: '4px', color: highestRiskEvent.risk_score >= 50 ? 'var(--risk-critical)' : 'var(--risk-low)' }}>
            {highestRiskEvent.risk_score.toFixed(1)} / 100
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>PRIMARY AUTH & FINGERPRINT</span>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {latestEvent.auth_method} · {latestEvent.device_fingerprint?.split('|')[0] || 'Unknown OS'}
          </p>
        </div>
      </div>

      {/* Main Analysis Section: Timeline + Top Features */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '20px' }}>
        
        {/* Risk History Timeline */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '4px' }}>Risk History Timeline</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>Session-by-session risk scores & sequence log-likelihood</p>

          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={entityEvents}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="timestamp" stroke="var(--text-muted)" fontSize={10} tickFormatter={t => t.split('T')[0]} />
                <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={{ background: 'var(--tooltip-bg)', borderColor: 'var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)' }} />
                <Line type="monotone" dataKey="risk_score" name="Risk Score" stroke="#EF4444" strokeWidth={2.5} dot={{ r: 3, fill: '#EF4444' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Feature Attribution Bar Chart */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '4px' }}>Peak Alert Attribution</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>Top Z-Score & SHAP importance factors</p>

          {topFeatures.length > 0 ? (
            <div style={{ width: '100%', height: '260px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topFeatures} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis type="number" stroke="var(--text-muted)" fontSize={10} />
                  <YAxis dataKey="description" type="category" stroke="var(--text-muted)" fontSize={10} width={130} />
                  <Tooltip contentStyle={{ background: 'var(--tooltip-bg)', borderColor: 'var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)' }} />
                  <Bar dataKey="importance_score" name="Importance" fill="#818CF8" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No significant anomaly features for this session.</p>
          )}
        </div>

      </div>

      {/* Session History Table */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '16px' }}>Complete Monitored Sessions</h3>
        
        <div style={{ overflowX: 'auto', maxHeight: '400px' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Risk Score</th>
                <th>Resource Accessed</th>
                <th>Auth Method</th>
                <th>Duration (min)</th>
                <th>Predicted Type</th>
                <th>Explanation String</th>
              </tr>
            </thead>
            <tbody>
              {entityEvents.map((ev, idx) => (
                <tr key={idx}>
                  <td className="mono" style={{ fontSize: '0.8rem' }}>{ev.timestamp.replace('T', ' ')}</td>
                  <td className="mono" style={{ fontWeight: '700', color: ev.risk_score >= 50 ? 'var(--risk-critical)' : 'var(--risk-low)' }}>
                    {ev.risk_score.toFixed(1)}
                  </td>
                  <td className="mono" style={{ color: 'var(--entity-color)' }}>{ev.resource_accessed}</td>
                  <td>{ev.auth_method}</td>
                  <td className="mono">{ev.session_duration?.toFixed(1)}</td>
                  <td>
                    <span style={{ 
                      fontWeight: '700', 
                      color: ev.predicted_type === 'normal' ? 'var(--normal-text)' : 'var(--danger-text)',
                      fontSize: '0.75rem',
                      textTransform: 'uppercase'
                    }}>
                      {ev.predicted_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '460px', padding: '10px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ 
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.65rem',
                        fontWeight: '800',
                        letterSpacing: '0.04em',
                        background: ev.primary_inference_source === 'personal' ? 'rgba(99,102,241,0.2)' : ev.primary_inference_source === 'population' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)',
                        color: ev.primary_inference_source === 'personal' ? 'var(--link-color)' : ev.primary_inference_source === 'population' ? 'var(--danger-text)' : 'var(--warning-text)',
                        border: `1px solid ${ev.primary_inference_source === 'personal' ? 'rgba(99,102,241,0.4)' : ev.primary_inference_source === 'population' ? 'rgba(239,68,68,0.4)' : 'rgba(245,158,11,0.4)'}`
                      }}>
                        {ev.primary_inference_source?.toUpperCase() || 'PERSONAL'}
                      </span>
                      <span style={{ color: 'var(--text-primary)', lineHeight: '1.4', fontSize: '0.82rem' }}>
                        {ev.explanation?.replace(/Flagged due to: /g, '').replace(/\[PERSONAL\]|\[POPULATION\]|\[SEQUENCE\]/g, '').trim()}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
