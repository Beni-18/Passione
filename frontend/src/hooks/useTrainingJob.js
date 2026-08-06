import { useState, useEffect, useRef } from 'react';
import { startTraining, getJobStatus, checkHealth } from '../services/trainingApi';

export function useTrainingJob() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [rowsTotal, setRowsTotal] = useState(0);
  const [rowsProcessed, setRowsProcessed] = useState(0);
  const [rowsFailed, setRowsFailed] = useState(0);
  const [message, setMessage] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [modelHealth, setModelHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const pollingRef = useRef(null);
  const pollCountRef = useRef(0);
  const MAX_POLLS = 300; // 10 minutes at 2s interval

  const submitJob = async (file, randomSeed) => {
    setLoading(true);
    setError(null);
    setJobId(null);
    setStatus(null);
    setRowsTotal(0);
    setRowsProcessed(0);
    setRowsFailed(0);
    setMessage(null);
    setMetrics(null);
    setModelHealth(null);
    pollCountRef.current = 0;

    try {
      const res = await startTraining(file, randomSeed);
      setJobId(res.job_id);
      setStatus(res.status || 'queued');
      if (res.rows_received) {
        setRowsTotal(res.rows_received);
      }
    } catch (err) {
      setError(err.message || 'Failed to initiate training session.');
    } finally {
      setLoading(false);
    }
  };

  const resetJob = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    setJobId(null);
    setStatus(null);
    setRowsTotal(0);
    setRowsProcessed(0);
    setRowsFailed(0);
    setMessage(null);
    setMetrics(null);
    setModelHealth(null);
    setError(null);
    setLoading(false);
  };

  useEffect(() => {
    if (!jobId) return;

    pollingRef.current = setInterval(async () => {
      pollCountRef.current += 1;
      if (pollCountRef.current > MAX_POLLS) {
        clearInterval(pollingRef.current);
        setStatus('failed');
        setMessage('Training session timeout. Polling limit exceeded.');
        return;
      }

      try {
        const res = await getJobStatus(jobId);
        
        // Update states strictly as returned
        setStatus(res.status);
        setRowsTotal(res.rows_total ?? 0);
        setRowsProcessed(res.rows_processed ?? 0);
        setRowsFailed(res.rows_failed ?? 0);
        setMessage(res.message ?? null);

        if (res.status === 'complete') {
          clearInterval(pollingRef.current);
          setMetrics(res.metrics ?? null);
          
          // Trigger health checks immediately
          try {
            const health = await checkHealth();
            setModelHealth(health);
          } catch (hErr) {
            console.error('Post-training health check failed:', hErr);
          }
        } else if (res.status === 'failed') {
          clearInterval(pollingRef.current);
        }
      } catch (err) {
        console.error('Job status polling error:', err);
      }
    }, 2000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [jobId]);

  return {
    jobId,
    status,
    rowsTotal,
    rowsProcessed,
    rowsFailed,
    message,
    metrics,
    modelHealth,
    loading,
    error,
    submitJob,
    resetJob,
  };
}
