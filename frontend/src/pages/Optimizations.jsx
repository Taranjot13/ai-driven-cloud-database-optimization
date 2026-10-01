import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';
import MetricCard from '../components/MetricCard';

function Optimizations() {
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [executing, setExecuting] = useState(false);

  async function loadData() {
    try {
      setError('');
      const [summaryData, historyData] = await Promise.all([
        api.optimizationSummary(),
        api.optimizationHistory({ limit: 200 }),
      ]);
      setSummary(summaryData);
      setHistory(historyData.records || []);
    } catch (loadError) {
      setError(loadError.message || 'Unable to load optimization data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const latestMetricId = useMemo(() => history[0]?.metric_id || null, [history]);

  async function handleAnalyze() {
    if (!latestMetricId) {
      setError('No metric is available for analysis.');
      return;
    }

    setAnalyzing(true);
    try {
      const result = await api.analyzeOptimization(latestMetricId);
      setAnalysis(result);
    } catch (loadError) {
      setError(loadError.message || 'Unable to analyze optimization at this moment.');
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleExecute() {
    if (!analysis?.decision?.action) {
      setError('Run analysis before executing an optimization.');
      return;
    }

    const confirmed = window.confirm('This action may execute a safe optimization change. Continue?');
    if (!confirmed) return;

    setExecuting(true);
    try {
      const result = await api.executeOptimization({
        metricId: analysis.metric_id || latestMetricId,
        expectedAction: analysis.decision.action,
        confirmed: true,
      });
      setAnalysis({ ...analysis, execution: result.execution, final_status: result.final_status, status: result.status });
    } catch (loadError) {
      setError(loadError.message || 'Optimization execution was rejected or failed.');
    } finally {
      setExecuting(false);
    }
  }

  if (loading) return <LoadingState message="Loading optimization history…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>Optimization history unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <Header title="Optimizations" lastUpdated={new Date().toLocaleString()} onRefresh={loadData} refreshing={loading} status="Operational" />

      <section className="stats-grid compact">
        <MetricCard label="Total attempts" value={summary?.attempts ?? 0} detail="Optimization history entries" />
        <MetricCard label="Successful / verified" value={summary?.successful ?? 0} detail="Confirmed wins" tone="success" />
        <MetricCard label="Rollbacks" value={summary?.rollbacks ?? 0} detail="Safety reversions" tone="warning" />
        <MetricCard label="Success rate" value={summary?.success_rate != null ? `${Number(summary.success_rate).toFixed(2)}%` : '0.00%'} detail="Outcome efficiency" />
        <MetricCard label="Average successful improvement" value={summary?.average_successful_improvement != null ? `${Number(summary.average_successful_improvement).toFixed(2)}%` : '0.00%'} detail="Positive optimization gain" />
      </section>

      <div className="panel action-panel">
        <div className="panel-header inline-header">
          <h3>Explicit action panel</h3>
        </div>
        <div className="action-row">
          <button className="primary-button" onClick={handleAnalyze} disabled={analyzing || !latestMetricId}>
            {analyzing ? 'Analyzing...' : 'Analyze current opportunity'}
          </button>
          <button className="secondary-button" onClick={handleExecute} disabled={executing || !analysis?.decision?.action}>
            {executing ? 'Executing...' : 'Execute optimization'}
          </button>
        </div>
        {analysis ? (
          <div className="decision-card">
            <div><span>Selected action</span><strong>{analysis.decision?.action || 'MONITOR'}</strong></div>
            <div><span>Why selected</span><strong>{analysis.reason || 'No justification available.'}</strong></div>
            <div><span>Learning risk</span><strong>{analysis.decision?.learning_risk || 'UNKNOWN'}</strong></div>
            <div><span>Policy</span><strong>{analysis.decision?.policy || 'Cautious'}</strong></div>
            <div><span>Target table</span><strong>{analysis.decision?.target?.table_name || 'N/A'}</strong></div>
            <div><span>Target column</span><strong>{analysis.decision?.target?.column_name || 'N/A'}</strong></div>
          </div>
        ) : null}
      </div>

      <div className="panel">
        <div className="panel-header"><h3>Optimization history</h3></div>
        <table>
          <thead>
            <tr>
              <th>Optimization ID</th>
              <th>Metric ID</th>
              <th>Type</th>
              <th>Table</th>
              <th>Column</th>
              <th>Baseline</th>
              <th>Optimized</th>
              <th>Improvement</th>
              <th>Decision</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {history.slice(0, 30).map((item) => (
              <tr key={item.optimization_id || item.created_at}>
                <td>{item.optimization_id ?? '—'}</td>
                <td>{item.metric_id ?? '—'}</td>
                <td>{item.optimization_type || '—'}</td>
                <td>{item.table_name || '—'}</td>
                <td>{item.column_name || '—'}</td>
                <td>{item.baseline_time_ms != null ? `${Number(item.baseline_time_ms).toFixed(3)} ms` : '—'}</td>
                <td>{item.optimized_time_ms != null ? `${Number(item.optimized_time_ms).toFixed(3)} ms` : '—'}</td>
                <td>{item.improvement_percent != null ? `${Number(item.improvement_percent).toFixed(2)}%` : '—'}</td>
                <td><span className={`status-badge badge-${item.decision === 'ROLLBACK' ? 'warning' : item.decision === 'KEEP' || item.decision === 'EXISTING INDEX VERIFIED' ? 'success' : 'neutral'}`}>{item.decision || 'Unknown'}</span></td>
                <td>{item.created_at || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default Optimizations;
