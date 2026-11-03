"""
Web UI template for AI CV-Job Matching System.

Sprint 3 Production Release — Redesigned with ui-ux-pro-max skill.
Provides a modern, high-performance HTML5/CSS3/Vanilla-JS single-page application
served directly by FastAPI at GET / and GET /app.
Works without Node.js, providing an identical top-tier design system to the React UI.
"""

WEB_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="AI CV-Job Matching System — Intelligent recruitment screening using Machine Learning and LLMs">
  <title>AI CV-Job Matching System — Sprint 3 Production</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --color-primary: #0369a1;
      --color-primary-dark: #075985;
      --color-primary-light: #e0f2fe;
      --color-secondary: #0ea5e9;
      --color-accent: #16a34a;
      --color-accent-dark: #15803d;
      --color-accent-subtle: rgba(22, 163, 74, 0.1);
      --color-warning: #d97706;
      --color-warning-subtle: rgba(217, 119, 6, 0.1);
      --color-destructive: #dc2626;
      --color-destructive-subtle: rgba(220, 38, 38, 0.1);
      --color-background: #f8fafc;
      --color-surface: #ffffff;
      --color-surface-hover: #f1f5f9;
      --color-foreground: #0f172a;
      --color-muted: #64748b;
      --color-border: #e2e8f0;
      --color-border-strong: #cbd5e1;
      --color-ring: #0369a1;

      --font-heading: 'Space Grotesk', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-body: 'DM Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --radius-full: 9999px;

      --shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
      --shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04);
      --shadow-xl: 0 20px 25px -5px rgba(15, 23, 42, 0.09), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
    }

    body {
      font-family: var(--font-body);
      background-color: var(--color-background);
      color: var(--color-foreground);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      -webkit-font-smoothing: antialiased;
    }

    :focus-visible { outline: 2px solid var(--color-ring); outline-offset: 2px; }

    header {
      background: linear-gradient(135deg, #07192f 0%, #0a2540 60%, #034870 100%);
      color: #ffffff;
      padding: 0.85rem 1.5rem;
      box-shadow: 0 4px 20px rgba(7, 25, 47, 0.25);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      position: sticky;
      top: 0;
      z-index: 50;
    }

    .header-inner {
      max-width: 1280px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1.25rem;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      text-decoration: none;
      color: inherit;
    }

    .brand-icon {
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, var(--color-secondary) 0%, var(--color-primary) 100%);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35);
      flex-shrink: 0;
    }

    .brand h1 {
      font-family: var(--font-heading);
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .brand-badge {
      font-size: 0.68rem;
      font-weight: 600;
      padding: 0.15rem 0.5rem;
      border-radius: var(--radius-full);
      background: rgba(14, 165, 233, 0.2);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .brand p { font-size: 0.8rem; color: #94a3b8; font-weight: 400; }

    .nav-tabs { display: flex; gap: 0.4rem; align-items: center; }

    .tab-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.5rem 0.95rem;
      font-family: var(--font-body);
      font-size: 0.85rem;
      font-weight: 500;
      color: #cbd5e1;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all 180ms ease;
    }

    .tab-btn:hover {
      background: rgba(255, 255, 255, 0.12);
      color: #ffffff;
      transform: translateY(-1px);
    }

    .tab-btn.active {
      background: #ffffff;
      color: var(--color-foreground);
      border-color: #ffffff;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .tab-btn.active svg { color: var(--color-primary); }

    main {
      flex: 1;
      max-width: 1280px;
      width: 100%;
      margin: 1.75rem auto;
      padding: 0 1.5rem;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.75rem;
      align-items: start;
    }

    @media (min-width: 1024px) {
      .grid-2 { grid-template-columns: 1.05fr 0.95fr; }
    }

    .card {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: 1.75rem;
      box-shadow: var(--shadow-md);
      transition: box-shadow 200ms ease, border-color 200ms ease;
    }

    .card:hover {
      box-shadow: var(--shadow-lg);
      border-color: var(--color-border-strong);
    }

    .card-title {
      font-family: var(--font-heading);
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--color-foreground);
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      letter-spacing: -0.01em;
    }

    .card-title-icon { color: var(--color-primary); display: flex; }

    .presets-bar {
      background: var(--color-primary-light);
      border: 1px solid #bae6fd;
      border-radius: var(--radius-md);
      padding: 0.75rem 1rem;
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .presets-label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--color-primary-dark);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .btn-sample {
      background: #ffffff;
      border: 1px solid #7dd3fc;
      color: var(--color-primary-dark);
      padding: 0.35rem 0.75rem;
      border-radius: var(--radius-sm);
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: all 150ms ease;
    }

    .btn-sample:hover {
      background: var(--color-primary);
      color: #ffffff;
      border-color: var(--color-primary);
      transform: translateY(-1px);
    }

    .form-group { margin-bottom: 1.25rem; }

    .form-label {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--color-foreground);
      margin-bottom: 0.5rem;
    }

    .form-label span.req { color: var(--color-destructive); }

    .file-drop {
      border: 2px dashed var(--color-border-strong);
      background: var(--color-background);
      border-radius: var(--radius-md);
      padding: 1.75rem 1.25rem;
      text-align: center;
      cursor: pointer;
      transition: all 200ms ease;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.6rem;
    }

    .file-drop:hover, .file-drop.dragover {
      border-color: var(--color-primary);
      background: var(--color-primary-light);
      transform: scale(1.005);
    }

    .file-drop.file-selected {
      border-color: var(--color-accent);
      background: rgba(22, 163, 74, 0.04);
    }

    .drop-icon-wrap {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-full);
      background: #ffffff;
      border: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-primary);
      box-shadow: var(--shadow-sm);
    }

    .file-drop.file-selected .drop-icon-wrap { color: var(--color-accent); border-color: #86efac; }

    textarea.form-control {
      width: 100%;
      min-height: 180px;
      padding: 0.85rem 1rem;
      font-family: var(--font-body);
      font-size: 0.88rem;
      color: var(--color-foreground);
      background: #ffffff;
      border: 1px solid var(--color-border-strong);
      border-radius: var(--radius-md);
      resize: vertical;
      line-height: 1.5;
      transition: border-color 150ms ease, box-shadow 150ms ease;
    }

    textarea.form-control:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px var(--color-primary-light);
      outline: none;
    }

    .btn-primary {
      width: 100%;
      background: linear-gradient(135deg, var(--color-primary) 0%, #0284c7 100%);
      color: #ffffff;
      border: none;
      border-radius: var(--radius-md);
      padding: 0.85rem 1.5rem;
      font-family: var(--font-heading);
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.6rem;
      box-shadow: 0 4px 12px rgba(3, 105, 161, 0.25);
      transition: all 200ms ease;
    }

    .btn-primary:hover:not(:disabled) {
      background: linear-gradient(135deg, var(--color-primary-dark) 0%, #0369a1 100%);
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(3, 105, 161, 0.35);
    }

    .btn-primary:disabled { opacity: 0.65; cursor: not-allowed; }

    .btn-secondary {
      background: #ffffff;
      border: 1px solid var(--color-border-strong);
      color: var(--color-foreground);
      border-radius: var(--radius-md);
      padding: 0.5rem 0.95rem;
      font-family: var(--font-body);
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 150ms ease;
    }

    .btn-secondary:hover:not(:disabled) {
      background: var(--color-surface-hover);
      border-color: var(--color-muted);
    }

    .spinner {
      width: 18px;
      height: 18px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: #ffffff;
      border-radius: var(--radius-full);
      animation: spin 0.8s linear infinite;
      display: inline-block;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .error-box {
      background: var(--color-destructive-subtle);
      border: 1px solid #fca5a5;
      color: var(--color-destructive);
      padding: 0.75rem 1rem;
      border-radius: var(--radius-md);
      font-size: 0.85rem;
      margin-top: 0.75rem;
      display: none;
    }

    /* Score Gauge */
    .gauge-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 2rem 1.5rem;
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
      border-radius: var(--radius-lg);
      border: 1px solid var(--color-border);
      box-shadow: var(--shadow-md);
      margin-bottom: 1.5rem;
      position: relative;
      overflow: hidden;
    }

    .gauge-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 4px;
      background: linear-gradient(90deg, var(--color-secondary), var(--color-accent));
    }

    .gauge-wrap {
      position: relative;
      width: 150px;
      height: 150px;
      margin-bottom: 1.25rem;
    }

    .gauge-wrap svg { transform: rotate(-90deg); }

    .gauge-bg { stroke: #e2e8f0; stroke-width: 10; fill: none; }

    .gauge-fill {
      stroke-width: 10;
      stroke-linecap: round;
      fill: none;
      filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.1));
      transition: stroke-dashoffset 1.1s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .gauge-text {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .score-big {
      font-family: var(--font-heading);
      font-size: 2.5rem;
      font-weight: 700;
      line-height: 1;
    }

    .score-unit {
      font-size: 0.75rem;
      color: var(--color-muted);
      font-weight: 500;
      margin-top: 0.2rem;
    }

    .badge-compat {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.45rem 1.15rem;
      border-radius: var(--radius-full);
      font-family: var(--font-heading);
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }

    .badge-good { background: var(--color-accent-subtle); color: var(--color-accent-dark); border: 1px solid #86efac; }
    .badge-potential { background: var(--color-warning-subtle); color: #b45309; border: 1px solid #fcd34d; }
    .badge-nofit { background: var(--color-destructive-subtle); color: #b91c1c; border: 1px solid #fca5a5; }

    /* Chips */
    .chips-section { margin-top: 1.25rem; }
    .chips-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--color-foreground);
      margin-bottom: 0.6rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .chips-wrapper { display: flex; flex-wrap: wrap; gap: 0.4rem; }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.3rem 0.65rem;
      border-radius: var(--radius-full);
      font-size: 0.8rem;
      font-weight: 500;
    }

    .chip-green { background: var(--color-accent-subtle); color: var(--color-accent-dark); border: 1px solid #bbf7d0; }
    .chip-red { background: var(--color-destructive-subtle); color: #b91c1c; border: 1px solid #fecaca; }
    .chip-gray { font-size: 0.8rem; color: var(--color-muted); font-style: italic; }

    .ai-box {
      margin-top: 1.5rem;
      background: linear-gradient(135deg, #f0fdf4 0%, #f0f9ff 100%);
      border: 1px solid #bae6fd;
      border-radius: var(--radius-md);
      padding: 1.25rem;
    }

    .ai-content {
      font-size: 0.88rem;
      color: #1e293b;
      line-height: 1.6;
      white-space: pre-wrap;
      margin-top: 0.5rem;
    }

    .tag-llm {
      font-size: 0.68rem;
      font-weight: 700;
      padding: 0.15rem 0.5rem;
      border-radius: var(--radius-full);
      text-transform: uppercase;
      background: var(--color-primary);
      color: #ffffff;
    }

    /* Tables */
    .table-responsive {
      overflow-x: auto;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      background: #ffffff;
    }

    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
    th {
      background: #f8fafc;
      color: var(--color-muted);
      font-weight: 600;
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--color-border);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    td { padding: 0.85rem 1rem; border-bottom: 1px solid var(--color-border); color: var(--color-foreground); }
    tr:hover td { background: #f8fafc; }
    tr:last-child td { border-bottom: none; }

    .pill {
      display: inline-block;
      padding: 0.2rem 0.6rem;
      border-radius: var(--radius-full);
      font-weight: 700;
      font-size: 0.82rem;
      font-family: var(--font-heading);
    }

    /* Stats Grid */
    .stats-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
      margin-bottom: 1.75rem;
    }

    .stat-card {
      background: #ffffff;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      padding: 1.25rem;
      box-shadow: var(--shadow-sm);
      display: flex;
      align-items: center;
      gap: 1rem;
      transition: transform 150ms ease;
    }

    .stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }

    .stat-val {
      font-family: var(--font-heading);
      font-size: 1.85rem;
      font-weight: 700;
      line-height: 1.1;
    }

    .stat-lbl {
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--color-muted);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    footer {
      margin-top: auto;
      background: #ffffff;
      border-top: 1px solid var(--color-border);
      padding: 1.25rem 1.5rem;
      font-size: 0.82rem;
      color: var(--color-muted);
      text-align: center;
    }

    footer a { color: var(--color-primary); text-decoration: none; font-weight: 500; }
    footer a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <!-- Header -->
  <header>
    <div class="header-inner">
      <div class="brand">
        <div class="brand-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>
        </div>
        <div>
          <h1>
            <span>AI CV-Job Matching</span>
            <span class="brand-badge">Sprint 3 Prod</span>
          </h1>
          <p>Intelligent recruitment decision engine powered by PyMuPDF, Scikit-Learn & LLMs</p>
        </div>
      </div>

      <nav class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('match')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
          <span>Match CV</span>
        </button>
        <button class="tab-btn" onclick="switchTab('history')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
          <span>History</span>
        </button>
        <button class="tab-btn" onclick="switchTab('stats')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>
          <span>Analytics</span>
        </button>
      </nav>
    </div>
  </header>

  <main>
    <!-- TAB 1: MATCHING -->
    <section id="tab-match">
      <div class="grid-2">
        <!-- Input Form Card -->
        <div class="card">
          <div class="card-title">
            <span class="card-title-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
            </span>
            <span>Upload CV & Job Description</span>
          </div>

          <!-- Presets Bar -->
          <div class="presets-bar">
            <div class="presets-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <span>1-Click Presets:</span>
            </div>
            <div style="display:flex; gap:0.4rem; flex-wrap:wrap;">
              <button type="button" class="btn-sample" onclick="loadSample('python')">Senior Python Dev</button>
              <button type="button" class="btn-sample" onclick="loadSample('data')">Data Analyst</button>
              <button type="button" class="btn-sample" onclick="loadSample('accountant')">Accountant</button>
            </div>
          </div>

          <form id="match-form" onsubmit="handleMatchSubmit(event)">
            <div class="form-group">
              <div class="form-label">
                <span>Candidate Resume (PDF)<span class="req">*</span></span>
                <span style="font-size:0.75rem; color:var(--color-muted);">Max 5 MB</span>
              </div>
              <div class="file-drop" id="drop-zone" onclick="document.getElementById('file-input').click()">
                <input type="file" id="file-input" accept=".pdf" style="display:none;" onchange="handleFileSelect(this.files[0])">
                <div class="drop-icon-wrap" id="drop-icon-container">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
                </div>
                <div id="drop-title" style="font-size:0.92rem; font-weight:600; color:var(--color-foreground);">Drop candidate PDF here, or click to browse</div>
                <div id="drop-sub" style="font-size:0.78rem; color:var(--color-muted);">Strict magic-byte verification & text extraction via PyMuPDF</div>
              </div>
            </div>

            <div class="form-group">
              <div class="form-label">
                <span>Target Job Description<span class="req">*</span></span>
                <span id="char-count" style="font-size:0.75rem; color:var(--color-muted);">0 / 5000 chars</span>
              </div>
              <textarea id="jd-input" class="form-control" placeholder="Paste target Job Description here...&#10;&#10;Key requirements, technical skills, domain responsibilities, and qualifications will be automatically parsed and matched against the resume." maxlength="5000" oninput="updateCharCount()"></textarea>
            </div>

            <div id="form-error" class="error-box"></div>

            <button type="submit" id="btn-submit" class="btn-primary" style="margin-top:1.25rem;">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>
              <span>Analyze Compatibility</span>
            </button>
          </form>
        </div>

        <!-- Result Card -->
        <div class="card" id="result-card">
          <div class="card-title">
            <span class="card-title-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>
            </span>
            <span>Multi-Dimensional Match Analysis</span>
          </div>

          <!-- Empty State -->
          <div id="empty-state" style="text-align: center; padding: 4rem 1.5rem; color: var(--color-muted);">
            <div style="width: 56px; height: 56px; margin: 0 auto 1rem; color: #cbd5e1;">
              <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
            </div>
            <p style="font-weight: 600; font-size: 0.95rem;">Awaiting Evaluation</p>
            <p style="font-size: 0.82rem; margin-top: 0.25rem;">Select a CV and provide a Job Description to inspect compatibility.</p>
          </div>

          <!-- Active Results Container -->
          <div id="active-results" style="display: none;">
            <div class="gauge-card">
              <div class="gauge-wrap">
                <svg width="150" height="150" viewBox="0 0 150 150">
                  <circle cx="75" cy="75" r="56" class="gauge-bg" />
                  <circle cx="75" cy="75" r="56" class="gauge-fill" id="gauge-circle" stroke="#0369a1" stroke-dasharray="351.85" stroke-dashoffset="351.85" />
                </svg>
                <div class="gauge-text">
                  <span class="score-big" id="score-text">0.0</span>
                  <span class="score-unit">/ 100 PTS</span>
                </div>
              </div>
              <div class="badge-compat" id="compat-badge">No Fit</div>
            </div>

            <!-- Experience Summary Banner -->
            <div id="exp-summary-box" style="display:none; background:#f8fafc; border-left:3px solid var(--color-primary); padding:0.75rem 1rem; margin-bottom:1rem; font-size:0.85rem; border-radius:0 var(--radius-sm) var(--radius-sm) 0;">
              <strong>Experience Alignment:</strong> <span id="exp-summary-text"></span>
            </div>

            <!-- Dimension Breakdown -->
            <div id="subscores-box" style="display:none; margin-bottom:1.25rem;">
              <div style="font-size:0.85rem; font-weight:600; color:var(--color-foreground); margin-bottom:0.6rem;">Dimension Score Breakdown</div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;" id="subscores-grid"></div>
            </div>

            <div class="chips-section">
              <div class="chips-title" style="color:var(--color-accent-dark);">
                <span>Matched Technical Skills (<span id="matched-count">0</span>)</span>
              </div>
              <div class="chips-wrapper" id="matched-chips"></div>
            </div>

            <div class="chips-section">
              <div class="chips-title" style="color:var(--color-destructive);">
                <span>Missing Technical Skills (<span id="missing-count">0</span>)</span>
              </div>
              <div class="chips-wrapper" id="missing-chips"></div>
            </div>

            <div class="chips-section" id="other-reqs-section" style="display:none;">
              <div class="chips-title">Education & Other Qualifications</div>
              <div id="edu-comparison-text" style="font-size:0.84rem; color:var(--color-foreground); margin-bottom:0.4rem;"></div>
              <div class="chips-wrapper" id="other-chips"></div>
            </div>

            <div class="ai-box">
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem;">
                <div style="font-family:var(--font-heading); font-size:0.92rem; font-weight:700; color:var(--color-primary-dark); display:flex; align-items:center; gap:0.4rem;">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>
                  <span>AI Evaluation & Feedback</span>
                </div>
                <span class="tag-llm" id="llm-badge">LLM</span>
              </div>
              <div class="ai-content" id="explanation-text"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 2: HISTORY -->
    <section id="tab-history" style="display: none;">
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 1rem;">
          <h2 class="card-title" style="margin-bottom: 0;">
            <span class="card-title-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg></span>
            <span>Matching Evaluation History</span>
          </h2>
          <div style="display:flex; gap:0.5rem;">
            <button class="btn-secondary" onclick="window.open('/api/v1/history/export?format=csv', '_blank')">Export CSV</button>
            <button class="btn-secondary" onclick="loadHistory()">Refresh</button>
          </div>
        </div>
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Candidate CV</th>
                <th>Score</th>
                <th>Fit Classification</th>
                <th>Matched Skills</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody id="history-body">
              <tr><td colspan="6" style="text-align:center; padding:2rem; color:var(--color-muted);">Loading evaluation records...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 3: STATS -->
    <section id="tab-stats" style="display: none;">
      <div class="stats-cards">
        <div class="stat-card">
          <div>
            <div class="stat-val" id="stat-total">0</div>
            <div class="stat-lbl">Total Matches</div>
          </div>
        </div>
        <div class="stat-card">
          <div>
            <div class="stat-val" id="stat-avg" style="color:var(--color-accent-dark);">0.0</div>
            <div class="stat-lbl">Average Score</div>
          </div>
        </div>
        <div class="stat-card">
          <div>
            <div class="stat-val" id="stat-cvs" style="color:var(--color-primary);">0</div>
            <div class="stat-lbl">Resumes Analyzed</div>
          </div>
        </div>
        <div class="stat-card">
          <div>
            <div class="stat-val" id="stat-jds" style="color:#7c3aed;">0</div>
            <div class="stat-lbl">Job Descriptions</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2 class="card-title">
          <span class="card-title-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg></span>
          <span>Compatibility Classification Distribution</span>
        </h2>
        <div id="dist-bars" style="margin-top:1rem;"></div>
      </div>
    </section>
  </main>

  <footer>
    <p>AI CV-Job Matching System &copy; 2026 &bull; Agile Team 6 &bull; Sprint 3 Production Release</p>
    <p style="margin-top:0.35rem;">
      <a href="/docs" target="_blank">Swagger API Reference</a> &bull;
      <a href="/health" target="_blank">Service Health</a> &bull;
      <a href="/api/v1/info" target="_blank">API Specs</a>
    </p>
  </footer>

  <script>
    let selectedFile = null;

    function switchTab(name) {
      ['match', 'history', 'stats'].forEach(t => {
        document.getElementById(`tab-${t}`).style.display = (t === name) ? 'block' : 'none';
      });
      document.querySelectorAll('.tab-btn').forEach((b, i) => {
        b.classList.toggle('active', (name === 'match' && i === 0) || (name === 'history' && i === 1) || (name === 'stats' && i === 2));
      });
      if (name === 'history') loadHistory();
      if (name === 'stats') loadStats();
    }

    function handleFileSelect(file) {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please choose a valid PDF file.');
        return;
      }
      selectedFile = file;
      const dz = document.getElementById('drop-zone');
      dz.classList.add('file-selected');
      document.getElementById('drop-title').textContent = file.name;
      document.getElementById('drop-sub').textContent = `${(file.size / 1024).toFixed(1)} KB — Ready to analyze`;
    }

    function updateCharCount() {
      const len = document.getElementById('jd-input').value.length;
      document.getElementById('char-count').textContent = `${len} / 5000 chars`;
    }

    function loadSample(type) {
      if (type === 'python') {
        document.getElementById('jd-input').value = `We are looking for a Senior Python Developer with 3+ years of experience in backend development.
Required Technical Skills: Python, FastAPI, Docker, PostgreSQL, REST APIs, Git, Redis.
Responsibilities: Design and implement high-performance APIs, collaborate with ML engineers, maintain test coverage.
Education: Bachelor's degree in Computer Science, Software Engineering, or related technical field.`;
      } else if (type === 'data') {
        document.getElementById('jd-input').value = `Seeking a skilled Data Analyst / Machine Learning Specialist to derive actionable insights from complex datasets.
Required Technical Skills: Python, Pandas, NumPy, Scikit-learn, SQL, PowerBI, Data Visualization, Statistics.
Experience: 2+ years working with relational databases and predictive modeling.
Qualifications: Bachelor's degree in Data Science, Mathematics, or Computer Science.`;
      } else if (type === 'accountant') {
        document.getElementById('jd-input').value = `Urgent hiring: Senior General Accountant to oversee financial statements, ledger entries, and tax compliance.
Required Skills: GAAP, Financial Reporting, QuickBooks, Excel, Tax Audit, Accounts Payable/Receivable.
Experience: Minimum 4 years in corporate accounting or banking.
Education: Bachelor's degree in Accounting, Finance, or CPA certification.`;
      }
      updateCharCount();
    }

    async function handleMatchSubmit(e) {
      e.preventDefault();
      const errBox = document.getElementById('form-error');
      errBox.style.display = 'none';

      const jd = document.getElementById('jd-input').value.trim();
      if (!selectedFile) {
        errBox.textContent = 'Please select a candidate CV PDF file.';
        errBox.style.display = 'block';
        return;
      }
      if (!jd) {
        errBox.textContent = 'Please provide the Job Description text.';
        errBox.style.display = 'block';
        return;
      }

      const btn = document.getElementById('btn-submit');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Analyzing Compatibility...';

      try {
        const formData = new FormData();
        formData.append('pdf_file', selectedFile);
        formData.append('jd_text', jd);

        const res = await fetch('/api/v1/match', {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.message || `Server responded with code ${res.status}`);
        }

        const data = await res.json();
        renderResults(data);
      } catch (err) {
        errBox.textContent = err.message || 'An error occurred during evaluation.';
        errBox.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>
          <span>Analyze Compatibility</span>`;
      }
    }

    function renderResults(data) {
      document.getElementById('empty-state').style.display = 'none';
      document.getElementById('active-results').style.display = 'block';

      const score = data.matching_score || 0;
      const label = data.compatibility_label || 'No Fit';

      // Update Gauge
      document.getElementById('score-text').textContent = score.toFixed(1);
      const circumference = 351.85; // 2 * PI * 56
      const offset = circumference * (1 - Math.min(100, Math.max(0, score)) / 100);
      const circle = document.getElementById('gauge-circle');

      const isGood = label === 'Good Fit';
      const isPotential = label === 'Potential Fit';
      const color = isGood ? '#16a34a' : isPotential ? '#d97706' : '#dc2626';

      circle.style.stroke = color;
      circle.style.strokeDashoffset = offset;
      document.getElementById('score-text').style.color = color;

      // Badge
      const badge = document.getElementById('compat-badge');
      badge.textContent = label;
      badge.className = `badge-compat ${isGood ? 'badge-good' : isPotential ? 'badge-potential' : 'badge-nofit'}`;

      // Experience Box
      const expBox = document.getElementById('exp-summary-box');
      if (data.experience_match_summary) {
        document.getElementById('exp-summary-text').textContent = data.experience_match_summary;
        expBox.style.display = 'block';
      } else {
        expBox.style.display = 'none';
      }

      // Sub-Scores
      const subBox = document.getElementById('subscores-box');
      const subGrid = document.getElementById('subscores-grid');
      if (data.sub_scores) {
        const sub = data.sub_scores;
        subGrid.innerHTML = `
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.78rem; font-weight:600; margin-bottom:4px;">
              <span>Tech Skills (45%)</span><strong style="color:#0284c7;">${(sub.tech_skill_score || 0).toFixed(1)}%</strong>
            </div>
            <div style="background:#e2e8f0; height:6px; border-radius:99px; overflow:hidden;">
              <div style="width:${Math.min(100, sub.tech_skill_score || 0)}%; height:100%; background:#0284c7;"></div>
            </div>
          </div>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.78rem; font-weight:600; margin-bottom:4px;">
              <span>Experience (30%)</span><strong style="color:#0891b2;">${(sub.experience_score || 0).toFixed(1)}%</strong>
            </div>
            <div style="background:#e2e8f0; height:6px; border-radius:99px; overflow:hidden;">
              <div style="width:${Math.min(100, sub.experience_score || 0)}%; height:100%; background:#0891b2;"></div>
            </div>
          </div>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.78rem; font-weight:600; margin-bottom:4px;">
              <span>Education (15%)</span><strong style="color:#7c3aed;">${(sub.other_req_score || 0).toFixed(1)}%</strong>
            </div>
            <div style="background:#e2e8f0; height:6px; border-radius:99px; overflow:hidden;">
              <div style="width:${Math.min(100, sub.other_req_score || 0)}%; height:100%; background:#7c3aed;"></div>
            </div>
          </div>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.78rem; font-weight:600; margin-bottom:4px;">
              <span>ML Inference (10%)</span><strong style="color:#059669;">${(sub.ml_model_score || 0).toFixed(1)}%</strong>
            </div>
            <div style="background:#e2e8f0; height:6px; border-radius:99px; overflow:hidden;">
              <div style="width:${Math.min(100, sub.ml_model_score || 0)}%; height:100%; background:#059669;"></div>
            </div>
          </div>
        `;
        subBox.style.display = 'block';
      }

      // Skills
      const matched = data.matched_skills || [];
      const missing = data.missing_skills || [];
      document.getElementById('matched-count').textContent = matched.length;
      document.getElementById('missing-count').textContent = missing.length;

      document.getElementById('matched-chips').innerHTML = matched.length
        ? matched.map(s => `<span class="chip chip-green">${s}</span>`).join('')
        : '<span class="chip chip-gray">No matched technical skills detected</span>';

      document.getElementById('missing-chips').innerHTML = missing.length
        ? missing.map(s => `<span class="chip chip-red">${s}</span>`).join('')
        : '<span class="chip chip-gray">No technical skill gaps identified</span>';

      // Other Reqs
      const otherSection = document.getElementById('other-reqs-section');
      const otherComp = data.other_requirements_comparison || {};
      const matchedOther = otherComp.matched || [];
      const missingOther = otherComp.missing || [];
      const edu = otherComp.education;

      if (matchedOther.length > 0 || missingOther.length > 0 || edu) {
        if (edu) {
          document.getElementById('edu-comparison-text').innerHTML =
            `<strong>Degree:</strong> Candidate (${edu.candidate || 'N/A'}) vs Required (${edu.required || 'N/A'}) — ${edu.satisfied ? 'Satisfied' : 'Gap'}`;
        }
        let html = '';
        matchedOther.forEach(item => { html += `<span class="chip chip-green">${item}</span>`; });
        missingOther.forEach(item => { html += `<span class="chip chip-red">${item}</span>`; });
        document.getElementById('other-chips').innerHTML = html;
        otherSection.style.display = 'block';
      } else {
        otherSection.style.display = 'none';
      }

      // Explanation
      document.getElementById('explanation-text').textContent = data.llm_explanation || 'No explanation generated.';
      const llmBadge = document.getElementById('llm-badge');
      llmBadge.textContent = data.llm_status === 'success' ? 'LLM' : 'Auto-Rule';
      llmBadge.style.background = data.llm_status === 'success' ? 'var(--color-primary)' : 'var(--color-warning)';
    }

    async function loadHistory() {
      const tbody = document.getElementById('history-body');
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem; color:var(--color-muted);">Loading evaluation records...</td></tr>';
      try {
        const res = await fetch('/api/v1/history?limit=50');
        const data = await res.json();
        const results = data.results || [];
        if (!results.length) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem; color:var(--color-muted);">No evaluation records found.</td></tr>';
          return;
        }
        tbody.innerHTML = results.map((r, i) => {
          const isGood = r.compatibility_label === 'Good Fit';
          const isPot = r.compatibility_label === 'Potential Fit';
          const bg = isGood ? '#dcfce7' : isPot ? '#fef3c7' : '#fee2e2';
          const fg = isGood ? '#16a34a' : isPot ? '#d97706' : '#dc2626';
          const skills = (r.matched_skills || []).slice(0, 3).map(s => `<span class="chip chip-green" style="font-size:0.7rem; padding:0.1rem 0.4rem;">${s}</span>`).join(' ');
          const date = r.created_at ? new Date(r.created_at).toLocaleString('vi-VN') : '—';
          return `<tr>
            <td style="color:var(--color-muted);">${results.length - i}</td>
            <td><strong>${r.cv_filename || 'Unknown'}</strong></td>
            <td><span class="pill" style="background:${bg}; color:${fg};">${(r.matching_score || 0).toFixed(1)}</span></td>
            <td><strong style="color:${fg};">${r.compatibility_label}</strong></td>
            <td>${skills}</td>
            <td style="font-size:0.8rem; color:var(--color-muted);">${date}</td>
          </tr>`;
        }).join('');
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--color-destructive); padding:1rem;">Failed to load history: ${err.message}</td></tr>`;
      }
    }

    async function loadStats() {
      try {
        const res = await fetch('/api/v1/stats');
        const data = await res.json();
        document.getElementById('stat-total').textContent = data.total_matches || 0;
        document.getElementById('stat-avg').textContent = data.avg_score ? data.avg_score.toFixed(1) : '—';
        document.getElementById('stat-cvs').textContent = data.total_cvs || 0;
        document.getElementById('stat-jds').textContent = data.total_jds || 0;

        const dist = data.label_distribution || {};
        const total = data.total_matches || 1;
        const colors = { 'Good Fit': 'var(--color-accent)', 'Potential Fit': 'var(--color-warning)', 'No Fit': 'var(--color-destructive)' };

        document.getElementById('dist-bars').innerHTML = Object.entries(dist).map(([label, count]) => {
          const pct = ((count / total) * 100).toFixed(1);
          return `<div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.75rem;">
            <div style="width:110px; font-weight:600; font-size:0.85rem;">${label}</div>
            <div style="flex:1; height:10px; background:#f1f5f9; border-radius:999px; overflow:hidden;">
              <div style="width:${pct}%; height:100%; background:${colors[label] || '#94a3b8'}; border-radius:999px;"></div>
            </div>
            <div style="width:60px; text-align:right; font-size:0.85rem; color:var(--color-muted);">${count} (${pct}%)</div>
          </div>`;
        }).join('');
      } catch (e) { console.log(e); }
    }
  </script>
</body>
</html>
"""
