import React, { useState, useRef } from 'react'
import { performRealClientSideMatch } from './MatchForm'
import {
  IconUsers,
  IconUpload,
  IconCheck,
  IconX,
  IconZap,
  IconFileText,
  IconAward,
  IconAlertCircle,
  IconSparkles
} from './Icons'

/**
 * CompareTab — Multi-CV Side-by-Side Comparison & Candidate Ranking Dashboard.
 * Calls POST /api/v1/compare with multiple PDF CVs and a single JD.
 */
function CompareTab() {
  const [files, setFiles] = useState([])
  const [jdText, setJdText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [compareResults, setCompareResults] = useState(null)
  const fileInputRef = useRef(null)

  const handleFilesChange = (selectedFiles) => {
    if (!selectedFiles || selectedFiles.length === 0) return
    const valid = []
    for (let i = 0; i < selectedFiles.length; i++) {
      const f = selectedFiles[i]
      if (f.name.toLowerCase().endsWith('.pdf') && f.size <= 5 * 1024 * 1024) {
        valid.push(f)
      }
    }
    if (valid.length < selectedFiles.length) {
      setError('Some files were skipped (only PDFs under 5MB are supported).')
    } else {
      setError('')
    }
    setFiles((prev) => [...prev, ...valid])
  }

  const handleRemoveFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleCompare = async (e) => {
    e.preventDefault()
    if (files.length < 2) {
      setError('Please select at least 2 CV PDF files for comparison.')
      return
    }
    const trimmedJd = jdText.trim()
    const words = trimmedJd.match(/[a-zA-Z]+/g) || []
    if (trimmedJd.length < 30 || words.length < 5) {
      setError('Job description must contain at least 30 characters and at least 5 valid words.')
      return
    }

    setLoading(true)
    setError('')
    setCompareResults(null)

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
      const formData = new FormData()
      files.forEach((file) => {
        formData.append('files', file)
      })
      formData.append('jd_text', jdText)

      const res = await fetch(`${API_BASE}/api/v1/compare`, {
        method: 'POST',
        body: formData,
      })

      const contentType = res.headers.get('content-type') || ''
      const isHtmlResponse = contentType.includes('text/html')

      if (res.status === 405 || res.status === 404 || isHtmlResponse) {
        throw new Error('Static host API unavailable')
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message || `Server error ${res.status}`)
      }

      const data = await res.json()
      setCompareResults(data)
    } catch (err) {
      // Dynamic client-side evaluation against actual jdText and uploaded PDFs
      const candidateEvals = await Promise.all(
        files.map(async (file) => {
          const match = await performRealClientSideMatch(file, jdText)
          return {
            filename: file.name,
            matching_score: match.matching_score,
            compatibility_label: match.compatibility_label,
            matched_skills: match.matched_skills,
            missing_skills: match.missing_skills,
          }
        })
      )
      candidateEvals.sort((a, b) => b.matching_score - a.matching_score)
      setCompareResults({
        total_candidates: files.length,
        candidates: candidateEvals,
        rankings: candidateEvals,
      })
    } finally {
      setLoading(false)
    }
  }

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

  return (
    <div>
      <div className="card" style={{ marginBottom: '1.75rem' }}>
        <div className="card-title">
          <span className="card-title-icon"><IconUsers size={22} /></span>
          <span>Multi-Candidate Comparison & Ranking</span>
        </div>

        <form onSubmit={handleCompare}>
          {/* File Multi-Upload */}
          <div className="form-group">
            <div className="form-label">
              <span>Select 2+ Candidate CVs (PDF)</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-foreground-muted)' }}>
                {files.length} selected
              </span>
            </div>

            <div
              className="file-drop-zone"
              onClick={() => fileInputRef.current?.click()}
              style={{ padding: '1.25rem' }}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf"
                style={{ display: 'none' }}
                onChange={(e) => handleFilesChange(e.target.files)}
              />
              <div className="drop-icon-container">
                <IconUpload size={22} />
              </div>
              <div className="drop-title">Click to select multiple candidate PDFs</div>
              <div className="drop-hint">Compare experience, technical skill overlap, and suitability ranking</div>
            </div>

            {/* Selected File Chips */}
            {files.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
                {files.map((file, idx) => (
                  <span
                    key={idx}
                    className="file-pill"
                    style={{ background: '#f8fafc', borderColor: 'var(--color-border)' }}
                  >
                    <IconFileText size={14} />
                    <span className="truncate" style={{ maxWidth: '140px' }}>{file.name}</span>
                    <span
                      onClick={() => handleRemoveFile(idx)}
                      style={{ cursor: 'pointer', display: 'flex', marginLeft: 4 }}
                    >
                      <IconX size={12} />
                    </span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Target Job Description */}
          <div className="form-group">
            <div className="form-label">
              <span>Target Job Description</span>
            </div>
            <textarea
              className="form-textarea"
              placeholder="Paste the job description against which all uploaded candidate CVs will be ranked..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={5}
            />
          </div>

          {error && <div className="error-msg">{error}</div>}

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || files.length < 2 || !jdText.trim()}
            style={{ marginTop: '0.75rem' }}
          >
            {loading ? (
              <>
                <span className="spinner" />
                <span>Evaluating Candidates...</span>
              </>
            ) : (
              <>
                <IconSparkles size={18} />
                <span>Rank Candidates Side-by-Side</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Comparison Leaderboard Results */}
      {compareResults && compareResults.rankings && (
        <div className="card">
          <div className="card-title">
            <span className="card-title-icon"><IconAward size={22} /></span>
            <span>Candidate Evaluation Leaderboard ({compareResults.total_candidates} candidates)</span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '50px' }}>Rank</th>
                  <th>Candidate File</th>
                  <th>Score</th>
                  <th>Fit Label</th>
                  <th>Matched Skills</th>
                  <th>Skill Gap Count</th>
                </tr>
              </thead>
              <tbody>
                {compareResults.rankings.map((cand, idx) => (
                  <tr key={idx} style={idx === 0 ? { background: '#f0fdf4' } : {}}>
                    <td style={{ fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
                      {idx === 0 ? (
                        <span style={{ color: '#16a34a', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <IconAward size={16} /> #1
                        </span>
                      ) : (
                        `#${idx + 1}`
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ color: 'var(--color-primary)' }}><IconFileText size={16} /></span>
                        <strong className="truncate" title={cand.filename}>
                          {cand.filename}
                        </strong>
                      </div>
                    </td>
                    <td>
                      <span
                        className="score-pill"
                        style={{
                          background: getScoreBg(cand.compatibility_label),
                          color: getScoreColor(cand.compatibility_label),
                        }}
                      >
                        {cand.matching_score?.toFixed(1)}
                      </span>
                    </td>
                    <td>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          color: getScoreColor(cand.compatibility_label),
                          fontWeight: 600,
                        }}
                      >
                        {cand.compatibility_label === 'Good Fit' ? (
                          <IconCheck size={14} />
                        ) : cand.compatibility_label === 'Potential Fit' ? (
                          <IconZap size={14} />
                        ) : (
                          <IconX size={14} />
                        )}
                        {cand.compatibility_label}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                        {(cand.matched_skills || []).slice(0, 4).map((s) => (
                          <span key={s} className="chip chip-matched" style={{ fontSize: '0.72rem', padding: '0.15rem 0.45rem' }}>
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ color: (cand.missing_skills || []).length > 0 ? '#b91c1c' : '#16a34a', fontWeight: 600 }}>
                      {(cand.missing_skills || []).length} gaps
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default CompareTab

