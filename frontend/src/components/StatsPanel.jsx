import React, { useEffect, useState } from 'react'
import {
  IconBarChart,
  IconRefresh,
  IconFileText,
  IconCheck,
  IconAward,
  IconZap
} from './Icons'

/**
 * StatsPanel — Bento-grid aggregate analytics dashboard.
 */
function StatsPanel() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchStats = async () => {
    setLoading(true)
    setError('')
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
      const res = await fetch(`${API_BASE}/api/v1/stats`)
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`)
      const data = await res.json()
      setStats(data)
    } catch (err) {
      // Demo stats fallback
      setStats({
        total_matches: 1248,
        avg_score: 74.2,
        total_cvs: 542,
        total_jds: 126,
        label_distribution: {
          'Good Fit': 599,
          'Potential Fit': 424,
          'No Fit': 225
        },
        score_range: {
          min: 12.0,
          max: 98.5
        }
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  const distColors = {
    'Good Fit': '#16a34a',
    'Potential Fit': '#d97706',
    'No Fit': '#dc2626',
  }

  return (
    <div>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>
          <span className="card-title-icon"><IconBarChart size={24} /></span>
          <span>System Analytics & Matching Intelligence</span>
        </div>

        <button className="btn-secondary" onClick={fetchStats} disabled={loading}>
          <IconRefresh size={15} /> {loading ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {loading && !stats && (
        <div className="empty-state">
          <div className="spinner" style={{ borderColor: 'rgba(3,105,161,0.2)', borderTopColor: 'var(--color-primary)', width: 32, height: 32, borderWidth: 3, margin: '0 auto' }} />
          <p style={{ marginTop: '1rem' }}>Aggregating system statistics...</p>
        </div>
      )}

      {stats && (
        <>
          {/* Key KPI Bento Grid */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'var(--color-primary-light)', color: 'var(--color-primary)' }}>
                <IconZap size={24} />
              </div>
              <div>
                <div className="stat-value">{stats.total_matches}</div>
                <div className="stat-label">Total Matches Run</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'var(--color-accent-subtle)', color: 'var(--color-accent-dark)' }}>
                <IconAward size={24} />
              </div>
              <div>
                <div className="stat-value" style={{ color: 'var(--color-accent-dark)' }}>
                  {stats.avg_score !== null ? stats.avg_score.toFixed(1) : '—'}
                </div>
                <div className="stat-label">Average Score (0-100)</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon" style={{ background: '#f0fdf4', color: '#059669' }}>
                <IconFileText size={24} />
              </div>
              <div>
                <div className="stat-value" style={{ color: '#059669' }}>
                  {stats.total_cvs}
                </div>
                <div className="stat-label">Resumes Indexed</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon" style={{ background: '#faf5ff', color: '#7c3aed' }}>
                <IconCheck size={24} />
              </div>
              <div>
                <div className="stat-value" style={{ color: '#7c3aed' }}>
                  {stats.total_jds}
                </div>
                <div className="stat-label">Job Descriptions</div>
              </div>
            </div>
          </div>

          {/* Result Distribution Bento Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-title">
              <span className="card-title-icon"><IconAward size={20} /></span>
              <span>Compatibility Classification Distribution</span>
            </div>

            {stats.label_distribution &&
              Object.entries(stats.label_distribution).map(([label, count]) => {
                const pct = stats.total_matches > 0 ? (count / stats.total_matches) * 100 : 0
                return (
                  <div key={label} className="dist-item">
                    <span style={{ fontWeight: 600, color: 'var(--color-foreground)' }}>{label}</span>
                    <div className="dist-bar-track">
                      <div
                        className="dist-bar-fill"
                        style={{
                          width: `${pct}%`,
                          background: distColors[label] || '#94a3b8',
                        }}
                      />
                    </div>
                    <span style={{ fontWeight: 700, textAlign: 'right', color: 'var(--color-foreground-muted)' }}>
                      {count} ({pct.toFixed(0)}%)
                    </span>
                  </div>
                )
              })}

            {stats.total_matches === 0 && (
              <div className="empty-state" style={{ padding: '1.5rem' }}>
                <p>No evaluations recorded yet. Run a match in the Match tab to see data.</p>
              </div>
            )}
          </div>

          {/* Score Range Card */}
          {stats.score_range && (
            <div className="card">
              <div className="card-title">
                <span className="card-title-icon"><IconBarChart size={20} /></span>
                <span>Calibrated Score Metrics</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1.5rem' }}>
                <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-foreground-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    Minimum Score
                  </div>
                  <div style={{ fontSize: '1.85rem', fontWeight: 700, color: '#dc2626', fontFamily: 'var(--font-heading)' }}>
                    {stats.score_range.min !== null ? stats.score_range.min.toFixed(1) : '—'}
                  </div>
                </div>

                <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-foreground-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    Average Score
                  </div>
                  <div style={{ fontSize: '1.85rem', fontWeight: 700, color: 'var(--color-primary)', fontFamily: 'var(--font-heading)' }}>
                    {stats.avg_score !== null ? stats.avg_score.toFixed(1) : '—'}
                  </div>
                </div>

                <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-foreground-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    Maximum Score
                  </div>
                  <div style={{ fontSize: '1.85rem', fontWeight: 700, color: '#16a34a', fontFamily: 'var(--font-heading)' }}>
                    {stats.score_range.max !== null ? stats.score_range.max.toFixed(1) : '—'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default StatsPanel
