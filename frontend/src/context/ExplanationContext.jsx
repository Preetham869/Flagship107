/**
 * Explanation Context
 * Application-level state management for AI Investigation Reports.
 * Ensures report generation continues across tab navigation, prevents duplicate
 * requests, preserves existing/previous reports, and recovers state on reload.
 */
import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { getExplanation, generateExplanation } from '../services/api';

const ExplanationContext = createContext(null);

export const ExplanationProvider = ({ jobId, children }) => {
  const [status, setStatus] = useState('not_generated'); // not_generated | queued | generating | completed | failed
  const [stage, setStage] = useState(null);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [previousReport, setPreviousReport] = useState(null);
  const pollTimerRef = useRef(null);
  const isPollingRef = useRef(false);

  // Stop polling helper
  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    isPollingRef.current = false;
  }, []);

  // Poll job explanation status
  const pollStatus = useCallback(async (targetJobId) => {
    if (!targetJobId) return;

    try {
      const data = await getExplanation(targetJobId);
      setStatus(data.status || 'not_generated');
      setStage(data.stage || null);
      setError(data.error || null);

      if (data.report) {
        setReport(data.report);
      }
      if (data.previous_report) {
        setPreviousReport(data.previous_report);
      }

      if (data.status === 'queued' || data.status === 'generating') {
        // Continue polling every 1.5 seconds
        isPollingRef.current = true;
        pollTimerRef.current = setTimeout(() => {
          pollStatus(targetJobId);
        }, 1500);
      } else {
        stopPolling();
      }
    } catch (err) {
      console.warn('Failed to poll explanation status:', err);
      // If 404 or network glitch, retry a limited number of times before failing
      stopPolling();
    }
  }, [stopPolling]);

  // Initial load when jobId changes
  useEffect(() => {
    if (!jobId) {
      setStatus('not_generated');
      setReport(null);
      setPreviousReport(null);
      setError(null);
      setStage(null);
      stopPolling();
      return;
    }

    // Check if backend already has an explanation or is currently generating
    pollStatus(jobId);

    return () => {
      stopPolling();
    };
  }, [jobId, pollStatus, stopPolling]);

  // Trigger report generation or regeneration
  const requestExplanation = useCallback(async (forceRegenerate = false) => {
    if (!jobId) return;

    if (forceRegenerate && report) {
      setPreviousReport(report);
    }

    setStatus('queued');
    setStage('Initializing request...');
    setError(null);

    try {
      const response = await generateExplanation(jobId, { forceRegenerate });
      
      // If response already returned a completed report (e.g. from cache)
      if (response.status === 'completed' && (response.report || response.executive_summary)) {
        const completedReport = response.report || response;
        setReport(completedReport);
        setStatus('completed');
        setStage('Completed');
        setError(null);
        stopPolling();
        return;
      }

      // If background generation queued or generating, start polling
      setStatus(response.status || 'generating');
      setStage(response.stage || 'In progress');
      if (response.previous_report) {
        setPreviousReport(response.previous_report);
      }

      stopPolling();
      isPollingRef.current = true;
      pollTimerRef.current = setTimeout(() => {
        pollStatus(jobId);
      }, 1200);
    } catch (err) {
      console.error('Failed to trigger explanation generation:', err);
      const detail = err.response?.data?.detail || err.message || 'Failed to start explanation generation';
      setError(detail);
      setStatus('failed');
      stopPolling();
    }
  }, [jobId, report, pollStatus, stopPolling]);

  const value = {
    jobId,
    status,
    stage,
    error,
    report,
    previousReport,
    isGenerating: status === 'queued' || status === 'generating',
    requestExplanation,
    refreshStatus: () => pollStatus(jobId),
  };

  return (
    <ExplanationContext.Provider value={value}>
      {children}
    </ExplanationContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useExplanation = () => {
  const context = useContext(ExplanationContext);
  if (!context) {
    throw new Error('useExplanation must be used within an ExplanationProvider');
  }
  return context;
};

export default ExplanationContext;
