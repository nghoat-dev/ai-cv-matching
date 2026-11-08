import React, { useEffect, useState, useCallback } from 'react'
import {
  IconHistory,
  IconRefresh,
  IconDownload,
  IconTrash,
  IconSearch,
  IconCheck,
  IconX,
  IconZap,
  IconFileText
} from './Icons'

/**
 * HistoryList — Searchable, filterable, and exportable matching records table.
 * Props:
 *   refreshKey — increment to trigger a reload.
 */
function HistoryList({ refreshKey }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [labelFilter, setLabelFilter] = useState('all')

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
      const res = await fetch(`${API_BASE}/api/v1/history?limit=100`)
      const contentType = res.headers.get('content-type') || ''
      if (!res.ok || contentType.includes('text/html')) throw new Error(`HTTP Error: ${res.status}`)
      const data = await res.json()
      setHistory(data.results || [])
    } catch (err) {
      // Demo records fallback when backend is not deployed
      setHistory([
        {
          id: 4,
          cv_filename: 'alex_nguyen_senior_dev.pdf',
          matching_score: 92.4,
          compatibility_label: 'Good Fit',
          matched_skills: ['python', 'fastapi', 'docker', 'postgresql', 'git', 'rest api'],
          created_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
          id: 3,
          cv_filename: 'sarah_tran_backend.pdf',
          matching_score: 71.8,
          compatibility_label: 'Potential Fit',
          matched_skills: ['python', 'sql', 'docker'],
          created_at: new Date(Date.now() - 7200000).toISOString()
        },
        {
          id: 2,
          cv_filename: 'david_pham_ml.pdf',
          matching_score: 84.5,
          compatibility_label: 'Good Fit',
          matched_skills: ['pandas', 'numpy', 'scikit-learn', 'python'],
          created_at: new Date(Date.now() - 14400000).toISOString()
        },
        {
          id: 1,
          cv_filename: 'michael_le_accountant.pdf',
          matching_score: 14.5,
          compatibility_label: 'No Fit',
          matched_skills: ['excel'],
          created_at: new Date(Date.now() - 86400000).toISOString()
        }
      ])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory, refreshKey])

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Delete record for "${filename}"?`)) return
    try {
      const res = await fetch(`/api/v1/history/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error(`Could not delete record: ${res.status}`)
      setHistory((prev) => prev.filter((item) => item.id !== id))
    } catch (err) {
      alert(err.message)
    }
  }

  const handleExport = (format) => {
    window.open(`/api/v1/history/export?format=${format}`, '_blank')
  }

  const filteredHistory = history.filter((item) => {
    const matchesSearch =
      !search ||
      (item.cv_filename || '').toLowerCase().includes(search.toLowerCase()) ||
      (item.compatibility_label || '').toLowerCase().includes(search.toLowerCase())
    const matchesLabel =
      labelFilter === 'all' || item.compatibility_label === labelFilter
    return matchesSearch && matchesLabel
  })

  const getScoreColor = (label) => {
    if (label === 'Good Fit') return '#16a34a'
    if (label === 'Potential Fit') return '#d97706'
    return '#dc2626'
  }

  const getScoreBg = (label) => {
    if (label === 'Good Fit') return '#dcfce7'
    if (label === 'Potential Fit') return '#fef3c7'
    return '#fee2e2'
  }

  const formatDate = (iso) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="card">
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>
          <span className="card-title-icon"><IconHistory size={22} /></span>
          <span>Matching Evaluation History ({filteredHistory.length})</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => handleExport('csv')}
            title="Download records as CSV"
          >
            <IconDownload size={15} /> Export CSV
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={fetchHistory}
            disabled={loading}
          >
            <IconRefresh size={15} /> {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filter and Search Toolbar */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1', minWidth: '220px', position: 'relative' }}>
          <input
            type="text"
            className="form-textarea"
            style={{ minHeight: 'auto', padding: '0.5rem 0.75rem 0.5rem 2.25rem', fontSize: '0.85rem' }}
            placeholder="Search by CV filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <span style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-foreground-subtle)' }}>
            <IconSearch size={16} />
          </span>
        </div>

        <select
          className="form-textarea"
          style={{ minHeight: 'auto', padding: '0.5rem 0.85rem', width: 'auto', fontSize: '0.85rem' }}
          value={labelFilter}
          onChange={(e) => setLabelFilter(e.target.value)}
        >
          <option value="all">All Labels</option>
          <option value="Good Fit">Good Fit (Green)</option>
          <option value="Potential Fit">Potential Fit (Yellow)</option>
          <option value="No Fit">No Fit (Red)</option>
        </select>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {!loading && filteredHistory.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon"><IconFileText size={48} /></div>
          <p style={{ fontWeight: 600 }}>No matching records found</p>
          <p style={{ fontSize: '0.82rem', marginTop: '0.25rem' }}>
            Upload a resume and job description in the Match tab to evaluate candidate compatibility.
          </p>
        </div>
      )}

      {filteredHistory.length > 0 && (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Candidate CV File</th>
                <th>Score</th>
                <th>Fit Label</th>
                <th>Top Matched Skills</th>
                <th>Timestamp</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((item, idx) => (
                <tr key={item.id || idx}>
                  <td style={{ color: 'var(--color-foreground-subtle)', fontWeight: 600 }}>
                    {filteredHistory.length - idx}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span style={{ color: 'var(--color-primary)' }}><IconFileText size={16} /></span>
                      <span className="truncate" title={item.cv_filename}>
                        {item.cv_filename || 'Unknown CV'}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span
                      className="score-pill"
                      style={{
                        background: getScoreBg(item.compatibility_label),
                        color: getScoreColor(item.compatibility_label),
                      }}
                    >
                      {item.matching_score?.toFixed(1)}
                    </span>
                  </td>
                  <td>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        color: getScoreColor(item.compatibility_label),
                        fontWeight: 600,
                        fontSize: '0.82rem',
                      }}
                    >
                      {item.compatibility_label === 'Good Fit' ? (
                        <IconCheck size={14} />
                      ) : item.compatibility_label === 'Potential Fit' ? (
                        <IconZap size={14} />
                      ) : (
                        <IconX size={14} />
                      )}
                      {item.compatibility_label}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                      {(item.matched_skills || []).slice(0, 3).map((skill) => (
                        <span key={skill} className="chip chip-matched" style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem' }}>
                          {skill}
                        </span>
                      ))}
                      {(item.matched_skills || []).length > 3 && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-foreground-muted)', alignSelf: 'center' }}>
                          +{item.matched_skills.length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ color: 'var(--color-foreground-muted)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                    {formatDate(item.created_at)}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      type="button"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#94a3b8',
                        cursor: 'pointer',
                        padding: '0.3rem',
                        borderRadius: '4px',
                        display: 'inline-flex',
                        alignItems: 'center'
                      }}
                      onClick={() => handleDelete(item.id, item.cv_filename)}
                      title="Delete record"
                    >
                      <IconTrash size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default HistoryList
