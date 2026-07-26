import React, { useState, useMemo } from 'react';
import { Search, Filter, ShieldAlert, Download, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';

export default function AlertsTab({ events, onSelectEntity }) {
  const [minRisk, setMinRisk] = useState(25);
  const [selectedType, setSelectedType] = useState('all');
  const [selectedEntityType, setSelectedEntityType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('risk_score');
  const [sortAsc, setSortAsc] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 30;

  // Filtered & Sorted events
  const filteredEvents = useMemo(() => {
    return events.filter(ev => {
      if (ev.risk_score < minRisk) return false;
      if (selectedType !== 'all' && ev.predicted_type !== selectedType) return false;
      if (selectedEntityType !== 'all' && ev.entity_type !== selectedEntityType) return false;
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const matchesEntity = ev.entity_id.toLowerCase().includes(term);
        const matchesResource = ev.resource_accessed?.toLowerCase().includes(term);
        const matchesExplanation = ev.explanation?.toLowerCase().includes(term);
        const matchesType = ev.predicted_type?.toLowerCase().includes(term);
        if (!matchesEntity && !matchesResource && !matchesExplanation && !matchesType) return false;
      }
      return true;
    }).sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [events, minRisk, selectedType, selectedEntityType, searchTerm, sortField, sortAsc]);

  const totalPages = Math.ceil(filteredEvents.length / pageSize) || 1;
  const paginatedEvents = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredEvents.slice(start, start + pageSize);
  }, [filteredEvents, currentPage, pageSize]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const anomalyTypes = ['all', 'brute_force', 'credential_stuffing', 'impossible_travel', 'lateral_movement', 'device_spoofing', 'low_and_slow', 'insider_drift', 'normal'];

  const getRiskBadge = (score) => {
    if (score >= 75) return <span className="badge badge-critical">CRITICAL ({score.toFixed(0)})</span>;
    if (score >= 50) return <span className="badge badge-high">HIGH ({score.toFixed(0)})</span>;
    if (score >= 25) return <span className="badge badge-medium">MEDIUM ({score.toFixed(0)})</span>;
    return <span className="badge badge-low">LOW ({score.toFixed(0)})</span>;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* Control Bar */}
      <div className="glass-card" style={{ padding: '20px', display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center', justifyContent: 'space-between' }}>

        {/* Search Input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1 1 250px' }}>
          <Search size={18} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search entity, resource, explanation..."
            value={searchTerm}
            onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            className="input-field"
            style={{ width: '100%' }}
          />
        </div>

        {/* Min Risk Slider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Min Risk:</span>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={minRisk}
            onChange={e => { setMinRisk(Number(e.target.value)); setCurrentPage(1); }}
            style={{ accentColor: '#6366F1', cursor: 'pointer' }}
          />
          <span className="mono" style={{ fontSize: '0.9rem', fontWeight: '700', minWidth: '32px', color: 'var(--link-color)' }}>{minRisk}</span>
        </div>

        {/* Anomaly Type Dropdown */}
        <select
          value={selectedType}
          onChange={e => { setSelectedType(e.target.value); setCurrentPage(1); }}
          className="input-field"
          style={{ cursor: 'pointer' }}
        >
          {anomalyTypes.map(t => (
            <option key={t} value={t} style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>
              {t === 'all' ? 'All Anomaly Types' : t.replace('_', ' ').toUpperCase()}
            </option>
          ))}
        </select>

        {/* Entity Type Dropdown */}
        <select
          value={selectedEntityType}
          onChange={e => { setSelectedEntityType(e.target.value); setCurrentPage(1); }}
          className="input-field"
          style={{ cursor: 'pointer' }}
        >
          <option value="all" style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>All Entity Types</option>
          <option value="user" style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>User</option>
          <option value="service_account" style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>Service Account</option>
          <option value="edge_device" style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>Edge Device</option>
        </select>

        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Showing <span style={{ color: 'var(--text-primary)', fontWeight: '700' }}>{filteredEvents.length}</span> alerts
        </div>

      </div>

      {/* Table Card */}
      <div className="glass-card" style={{ overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto', maxHeight: '600px' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>Rank</th>
                <th onClick={() => handleSort('risk_score')} style={{ cursor: 'pointer' }}>
                  Risk Score <ArrowUpDown size={12} />
                </th>
                <th onClick={() => handleSort('entity_id')} style={{ cursor: 'pointer' }}>Entity ID</th>
                <th>Entity Type</th>
                <th onClick={() => handleSort('timestamp')} style={{ cursor: 'pointer' }}>Timestamp</th>
                <th>Predicted Anomaly Type</th>
                <th>Confidence</th>
                <th>Inference & Feature Attribution Explanation</th>
              </tr>
            </thead>
            <tbody>
              {paginatedEvents.map((ev, index) => {
                const globalRank = (currentPage - 1) * pageSize + index + 1;
                return (
                  <tr
                    key={`${ev.entity_id}-${ev.timestamp}-${index}`}
                    onClick={() => onSelectEntity(ev.entity_id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>#{globalRank}</td>
                    <td>{getRiskBadge(ev.risk_score)}</td>
                    <td className="mono" style={{ fontWeight: '700', color: 'var(--entity-color)' }}>{ev.entity_id}</td>
                    <td>
                      <span className="badge badge-tag">{ev.entity_type}</span>
                    </td>
                    <td className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {ev.timestamp.replace('T', ' ')}
                    </td>
                    <td>
                      <span style={{
                        fontWeight: '700',
                        color: ev.predicted_type === 'normal' ? 'var(--normal-text)' : 'var(--danger-text)',
                        textTransform: 'uppercase',
                        fontSize: '0.75rem'
                      }}>
                        {ev.predicted_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="mono" style={{ fontSize: '0.85rem' }}>
                      {ev.confidence ? `${ev.confidence.toFixed(1)}%` : 'N/A'}
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
                          color: ev.primary_inference_source === 'personal' ? '#818CF8' : ev.primary_inference_source === 'population' ? '#FCA5A5' : '#FDE047',
                          border: `1px solid ${ev.primary_inference_source === 'personal' ? 'rgba(99,102,241,0.4)' : ev.primary_inference_source === 'population' ? 'rgba(239,68,68,0.4)' : 'rgba(245,158,11,0.4)'}`
                        }}>
                          {ev.primary_inference_source?.toUpperCase()}
                        </span>
                        <span style={{ color: 'var(--text-primary)', lineHeight: '1.4', fontSize: '0.82rem' }}>
                          {ev.explanation?.replace(/Flagged due to: /g, '').replace(/\[PERSONAL\]|\[POPULATION\]|\[SEQUENCE\]/g, '').trim()}
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Page <strong style={{ color: 'var(--text-primary)' }}>{currentPage}</strong> of {totalPages}
          </span>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.8rem', opacity: currentPage === 1 ? 0.5 : 1 }}
            >
              <ChevronLeft size={16} /> Prev
            </button>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.8rem', opacity: currentPage === totalPages ? 0.5 : 1 }}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>

      </div>

    </div>
  );
}
