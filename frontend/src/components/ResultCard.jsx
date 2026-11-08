import React, { useEffect, useState } from 'react'
import {
  IconCheck,
  IconX,
  IconClock,
  IconGraduationCap,
  IconSparkles,
  IconBot,
  IconBarChart,
  IconZap
} from './Icons'

/**
 * ResultCard — High-end Bento-grid analysis dashboard.
 * Displays 0-100 Score Gauge, 4-Dimensional Breakdown, Skills Gap, Alignment & AI Explanation.
 */
function ResultCard({ result }) {
  const [animated, setAnimated] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 60)
    return () => clearTimeout(timer)
  }, [result])

  const {
    matching_score = 0,
    compatibility_label = 'No Fit',
    matched_skills = [],
    missing_skills = [],
    experience_match_summary,
    other_requirements_comparison = {},
    sub_scores = {},
    llm_explanation,
    llm_status,
  } = result

  // Enforce exact mathematical score consistency (US-MultiDim):
  // finalScore = round(0.45 * tech + 0.30 * exp + 0.15 * edu + 0.10 * ml, 1)
  const tech = sub_scores?.tech_skill_score ?? 0
  const exp = sub_scores?.experience_score ?? 0
  const edu = sub_scores?.other_req_score ?? 0
  const ml = sub_scores?.ml_model_score ?? 0

  const hasSubScores = sub_scores && Object.keys(sub_scores).length > 0
  const calculatedScore = hasSubScores
    ? Math.round((0.45 * tech + 0.30 * exp + 0.15 * edu + 0.10 * ml) * 10) / 10
    : Math.round(matching_score * 10) / 10

  const finalScore = Math.min(100, Math.max(0, calculatedScore))
  const displayLabel = finalScore >= 75 ? 'Good Fit' : finalScore >= 50 ? 'Potential Fit' : 'No Fit'

  // Circular gauge setup
  const radius = 56
  const strokeWidth = 10
  const circumference = 2 * Math.PI * radius
  const dashOffset = animated
    ? circumference * (1 - Math.min(100, Math.max(0, finalScore)) / 100)
    : circumference

  const isGood = displayLabel === 'Good Fit'
  const isPotential = displayLabel === 'Potential Fit'

  const scoreColor = isGood ? '#16a34a' : isPotential ? '#d97706' : '#dc2626'
  const badgeClass = isGood ? 'badge-good' : isPotential ? 'badge-potential' : 'badge-nofit'

  const matchedOther = other_requirements_comparison?.matched || []
  const missingOther = other_requirements_comparison?.missing || []
  const eduInfo = other_requirements_comparison?.education

  const handleCopyExplanation = () => {
    if (!llm_explanation) return
    navigator.clipboard.writeText(llm_explanation)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="card">
      <div className="card-title">
        <span className="card-title-icon"><IconBarChart size={22} /></span>
        <span>Multi-Dimensional Match Analysis</span>
      </div>

      {/* Main Score & Alignment Hero */}
      <div className="result-header-card">
        <div className="score-meter">
          <svg width="150" height="150" viewBox="0 0 150 150">
            <circle
              cx="75"
              cy="75"
              r={radius}
              className="score-meter-bg"
            />
            <circle
              cx="75"
              cy="75"
              r={radius}
              className="score-meter-fill"
              stroke={scoreColor}
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              style={{ transition: 'stroke-dashoffset 1.1s cubic-bezier(0.4, 0, 0.2, 1)' }}
            />
          </svg>
          <div className="score-meter-text">
            <span className="score-number" style={{ color: scoreColor }}>
              {finalScore.toFixed(1)}
            </span>
            <span className="score-label-denom">/ 100 PTS</span>
          </div>
        </div>

        <div className={`badge-compat ${badgeClass}`}>
          {isGood ? <IconCheck size={16} /> : isPotential ? <IconZap size={16} /> : <IconX size={16} />}
          <span>{displayLabel}</span>
        </div>
      </div>

      {/* Experience & Domain Alignment Banner */}
      {experience_match_summary && (
        <div className="exp-summary-banner">
          <span style={{ color: 'var(--color-primary)', marginTop: 2 }}>
            <IconClock size={18} />
          </span>
          <div>
            <strong style={{ color: 'var(--color-foreground)' }}>Experience Alignment:</strong>{' '}
            <span>{experience_match_summary}</span>
          </div>
        </div>
      )}

      {/* 4-Dimensional Dimension Breakdown */}
      {sub_scores && Object.keys(sub_scores).length > 0 && (
        <div style={{ marginTop: '1.25rem' }}>
          <div className="skills-header">
            <span>Dimension Score Breakdown</span>
          </div>
          <div className="dimension-grid">
            <div className="dim-item">
              <div className="dim-header">
                <span>Technical Skills (45%)</span>
                <strong style={{ color: '#0284c7' }}>{Number(tech).toFixed(1)}%</strong>
              </div>
              <div className="dim-track">
                <div
                  className="dim-fill"
                  style={{
                    width: `${Math.min(100, Math.max(0, tech))}%`,
                    background: '#0284c7',
                  }}
                />
              </div>
            </div>

            <div className="dim-item">
              <div className="dim-header">
                <span>Experience & Duties (30%)</span>
                <strong style={{ color: '#0891b2' }}>{Number(exp).toFixed(1)}%</strong>
              </div>
              <div className="dim-track">
                <div
                  className="dim-fill"
                  style={{
                    width: `${Math.min(100, Math.max(0, exp))}%`,
                    background: '#0891b2',
                  }}
                />
              </div>
            </div>

            <div className="dim-item">
              <div className="dim-header">
                <span>Education & Other (15%)</span>
                <strong style={{ color: '#7c3aed' }}>{Number(edu).toFixed(1)}%</strong>
              </div>
              <div className="dim-track">
                <div
                  className="dim-fill"
                  style={{
                    width: `${Math.min(100, Math.max(0, edu))}%`,
                    background: '#7c3aed',
                  }}
                />
              </div>
            </div>

            <div className="dim-item">
              <div className="dim-header">
                <span>ML Model Inference (10%)</span>
                <strong style={{ color: '#059669' }}>{Number(ml).toFixed(1)}%</strong>
              </div>
              <div className="dim-track">
                <div
                  className="dim-fill"
                  style={{
                    width: `${Math.min(100, Math.max(0, ml))}%`,
                    background: '#059669',
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Matched Skills */}
      <div className="skills-block">
        <div className="skills-header">
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-accent-dark)' }}>
            <IconCheck size={16} /> Matched Technical Skills ({matched_skills.length})
          </span>
        </div>
        <div className="skills-chips-wrap">
          {matched_skills.length > 0 ? (
            matched_skills.map((skill) => (
              <span key={skill} className="chip chip-matched">
                <IconCheck size={12} /> {skill}
              </span>
            ))
          ) : (
            <span className="chip-empty">No overlapping technical skills detected</span>
          )}
        </div>
      </div>

      {/* Missing Skills */}
      <div className="skills-block">
        <div className="skills-header">
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-destructive)' }}>
            <IconX size={16} /> Missing / Gap Technical Skills ({missing_skills.length})
          </span>
        </div>
        <div className="skills-chips-wrap">
          {missing_skills.length > 0 ? (
            missing_skills.map((skill) => (
              <span key={skill} className="chip chip-missing">
                <IconX size={12} /> {skill}
              </span>
            ))
          ) : (
            <span className="chip-empty">No technical skill gaps found</span>
          )}
        </div>
      </div>

      {/* Other Qualifications & Education */}
      {(matchedOther.length > 0 || missingOther.length > 0 || eduInfo) && (
        <div className="skills-block">
          <div className="skills-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <IconGraduationCap size={16} /> Education & Other Qualifications
            </span>
          </div>

          {eduInfo && (
            <div style={{ fontSize: '0.84rem', color: 'var(--color-foreground)', marginBottom: '0.6rem' }}>
              <strong>Education Degree:</strong> Candidate ({eduInfo.candidate || 'Not specified'}) vs Required ({eduInfo.required || 'Not specified'}) —{' '}
              <span style={{ fontWeight: 600, color: eduInfo.satisfied ? 'var(--color-accent-dark)' : 'var(--color-warning)' }}>
                {eduInfo.satisfied ? 'Satisfied' : 'Partial / Under Review'}
              </span>
            </div>
          )}

          <div className="skills-chips-wrap">
            {matchedOther.map((item) => (
              <span key={item} className="chip chip-matched">
                <IconCheck size={12} /> {item}
              </span>
            ))}
            {missingOther.map((item) => (
              <span key={item} className="chip chip-missing">
                <IconX size={12} /> {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* AI Explanation / Synthesis Copilot */}
      {llm_explanation && (
        <div className="ai-copilot-card">
          <div className="copilot-header">
            <div className="copilot-title">
              <IconSparkles size={18} />
              <span>AI Evaluation & Feedback</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className={`copilot-badge ${llm_status === 'success' ? '' : 'fallback'}`}>
                {llm_status === 'success' ? 'LLM Verified' : 'Rule-Engine'}
              </span>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={handleCopyExplanation}
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>
          <div className="copilot-body">{llm_explanation}</div>
        </div>
      )}
    </div>
  )
}

export default ResultCard
