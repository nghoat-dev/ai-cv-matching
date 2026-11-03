import React, { useState } from 'react'
import MatchForm from './components/MatchForm'
import ResultCard from './components/ResultCard'
import HistoryList from './components/HistoryList'
import StatsPanel from './components/StatsPanel'
import CompareTab from './components/CompareTab'
import {
  IconBot,
  IconUpload,
  IconUsers,
  IconHistory,
  IconBarChart,
  IconSparkles
} from './components/Icons'
import './App.css'

/**
 * Root Application Component — AI CV-Job Matching System.
 * Implements UI/UX Pro Max standards with modern Bento layouts and zero emoji icons.
 */
function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [result, setResult] = useState(null)
  const [historyRefresh, setHistoryRefresh] = useState(0)

  const handleMatchResult = (data) => {
    setResult(data)
    setHistoryRefresh((n) => n + 1)
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-brand">
            <div className="brand-icon-wrap">
              <IconSparkles size={22} />
            </div>
            <div>
              <div className="header-title">
                <span>AI CV-Job Matching</span>
              </div>
              <p className="header-subtitle">
                Intelligent recruitment decision engine powered by PyMuPDF, Scikit-Learn & LLMs
              </p>
            </div>
          </div>

          <nav className="header-nav" aria-label="Main Navigation">
            <button
              className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
              type="button"
            >
              <IconUpload size={16} />
              <span>Match CV</span>
            </button>
            <button
              className={`nav-btn ${activeTab === 'compare' ? 'active' : ''}`}
              onClick={() => setActiveTab('compare')}
              type="button"
            >
              <IconUsers size={16} />
              <span>Multi-CV Compare</span>
            </button>
            <button
              className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
              type="button"
            >
              <IconHistory size={16} />
              <span>History</span>
            </button>
            <button
              className={`nav-btn ${activeTab === 'stats' ? 'active' : ''}`}
              onClick={() => setActiveTab('stats')}
              type="button"
            >
              <IconBarChart size={16} />
              <span>Analytics</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Body */}
      <main className="app-main">
        {activeTab === 'upload' && (
          <div className="upload-layout">
            <MatchForm onResult={handleMatchResult} />
            {result && <ResultCard result={result} />}
          </div>
        )}
        {activeTab === 'compare' && (
          <CompareTab />
        )}
        {activeTab === 'history' && (
          <HistoryList refreshKey={historyRefresh} />
        )}
        {activeTab === 'stats' && (
          <StatsPanel />
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          AI CV-Job Matching System &copy; 2026 &bull; Agile Team 6 &bull; Sprint 3 Production Release
        </p>
        <p style={{ marginTop: '0.4rem', fontSize: '0.78rem' }}>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            Swagger API Reference
          </a>
          {' '}&bull;{' '}
          <a href="http://localhost:8000/api/v1/info" target="_blank" rel="noreferrer">
            API Specs
          </a>
          {' '}&bull;{' '}
          <a href="http://localhost:8000/health" target="_blank" rel="noreferrer">
            Service Health
          </a>
        </p>
      </footer>
    </div>
  )
}

export default App
