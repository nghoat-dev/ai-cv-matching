@echo off
title AI CV-Job Matching System
echo =================================================================
echo        AI CV-JOB MATCHING SYSTEM - LOCAL RUNNER
echo =================================================================
echo.
echo Server starting at: http://localhost:8000
echo Open your browser and navigate to: http://localhost:8000
echo.
echo Press Ctrl + C to stop the server.
echo.
.venv\Scripts\uvicorn backend.app.main:app --reload --port 8000
pause
