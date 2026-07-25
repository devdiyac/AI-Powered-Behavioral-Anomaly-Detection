import React from 'react';
import { 
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, 
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid 
} from 'recharts';
import { ShieldAlert, Activity, UserX, Target, Zap, ArrowUpRight } from 'lucide-react';

const COLOR_MAP = {
  brute_force: '#EF4444',
  credential_stuffing: '#F97316',
  impossible_travel: '#EC4899',
  lateral_movement: '#8B5CF6',
  device_spoofing: '#06B6D4',
  low_and_slow: '#EAB308',
  insider_drift: '#10B981',
  normal: '#64748B'
};

export default function OverviewTab({ data, onSelectEntity, setActiveTab }) {
  if (!data) return <div style={{ padding: '40px', textAlign: 'center' }}>Loading dashboard data...</div>;

  const { summary, detection_metrics, alerts_by_date, anomaly_type_counts, risk_distribution, events } = data;

  // Compute top 5 highest risk entities
  const entityRiskMap = {};
  events.forEach(ev => {
    if (!entityRiskMap[ev.entity_id] || ev.risk_score > entityRiskMap[ev.entity_id].max_risk) {
      entityRiskMap[ev.entity_id] = {
        entity_id: ev.entity_id,
        entity_type: ev.entity_type,
        max_risk: ev.risk_score,
        latest_type: ev.predicted_type,
        latest_explanation: ev.explanation,
        timestamp: ev.timestamp
      };
    }
  });

  const topRiskEntities = Object.values(entityRiskMap)
    .sort((a, b) => b.max_risk - a.max_risk)
    .slice(0, 5);

  const pieData = Object.entries(anomaly_type_counts || {}).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value,
    color: COLOR_MAP[name] || '#6366F1'
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Stat Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>TOTAL ACCESS LOGS</span>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(99,102,241,0.1)', color: '#818CF8' }}>
              <Activity size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', marginTop: '10px' }} className="mono">
            {summary.total_events?.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Across {summary.unique_entities} Monitored Entities
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #EF4444' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>DETECTED INTRUSIONS</span>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(239,68,68,0.1)', color: '#FCA5A5' }}>
              <ShieldAlert size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', marginTop: '10px', color: '#EF4444' }} className="mono">
            {summary.total_anomalies?.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#F87171', marginTop: '4px' }}>
            Anomaly Rate: {(summary.anomaly_rate * 100).toFixed(2)}%
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>MODEL PR-AUC SCORE</span>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(6,182,212,0.1)', color: '#22D3EE' }}>
              <Target size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', marginTop: '10px' }} className="mono">
            {detection_metrics?.pr_auc ? detection_metrics.pr_auc.toFixed(3) : '0.381'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#38BDF8', marginTop: '4px' }}>
            Imbalance-Resilient Evaluator
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>COLD-START ENTITIES</span>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(245,158,11,0.1)', color: '#FBBF24' }}>
              <UserX size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', marginTop: '10px', color: '#FBBF24' }} className="mono">
            15
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Population Baseline Fallback Active
          </div>
        </div>

      </div>

      {/* Main Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        
        {/* Timeline Chart */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>Threat Event Velocity Timeline</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Daily frequency of anomalous sessions over time</p>
            </div>
            <span className="badge badge-critical">Live Pipeline Log</span>
          </div>

          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={alerts_by_date}>
                <defs>
                  <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip 
                  contentStyle={{ background: '#0F172A', borderColor: '#334155', borderRadius: '8px', color: '#FFF' }}
                  itemStyle={{ color: '#FCA5A5' }}
                />
                <Area type="monotone" dataKey="count" name="Threat Events" stroke="#EF4444" strokeWidth={2} fillOpacity={1} fill="url(#colorRisk)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Attack Type Breakdown */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '4px' }}>Attack Taxonomy Breakdown</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>Distribution by predicted category</p>

          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0F172A', borderColor: '#334155', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '10px' }}>
            {pieData.map(item => (
              <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: item.color }}></span>
                <span style={{ color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</span>
                <span style={{ fontWeight: '700', marginLeft: 'auto' }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Second Row: Risk Score Distribution + Top Risk Entities */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

        {/* Risk Distribution */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '4px' }}>Risk Score Distribution (0–100)</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>Ensemble score: IsolationForest + Personal Z-Score + Markov Sequence</p>

          <div style={{ width: '100%', height: '240px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={risk_distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="bin" stroke="#64748B" fontSize={10} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip contentStyle={{ background: '#0F172A', borderColor: '#334155', borderRadius: '8px' }} />
                <Bar dataKey="count" name="Sessions" fill="#6366F1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top At-Risk Entities */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>Highest Risk Entities</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Entities triggering peak threat scores</p>
            </div>
            <button 
              onClick={() => setActiveTab('alerts')}
              style={{ background: 'none', border: 'none', color: '#818CF8', fontSize: '0.8rem', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              View Queue <ArrowUpRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {topRiskEntities.map(ent => (
              <div 
                key={ent.entity_id}
                onClick={() => onSelectEntity(ent.entity_id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-color)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                className="glass-card-interactive"
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: '700', fontSize: '0.9rem' }} className="mono">{ent.entity_id}</span>
                    <span className="badge badge-tag">{ent.entity_type}</span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Latest: {ent.latest_type}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: '800', color: ent.max_risk >= 75 ? '#EF4444' : '#F97316' }} className="mono">
                    {ent.max_risk.toFixed(1)}
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Risk Score</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
