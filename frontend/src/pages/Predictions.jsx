import { useEffect, useState } from 'react';
import { api } from '../api/client';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';
import MetricCard from '../components/MetricCard';

function Predictions() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadData() {
    try {
      setError('');
      const data = await api.predictions();
      setPayload(data);
    } catch (loadError) {
      setError(loadError.message || 'Unable to load prediction data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading) return <LoadingState message="Loading prediction analysis…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>Prediction analysis unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <Header title="Predictions" lastUpdated={new Date().toLocaleString()} onRefresh={loadData} refreshing={loading} status={payload?.status || 'Ready'} />

      <section className="stats-grid compact">
        <MetricCard label="Historical observations" value={payload?.observations ?? 0} detail="Monitoring samples" />
        <MetricCard label="Average execution time" value={payload?.average_latency_ms != null ? `${Number(payload.average_latency_ms).toFixed(3)} ms` : 'N/A'} detail="Historical average" />
        <MetricCard label="Maximum execution time" value={payload?.maximum_latency_ms != null ? `${Number(payload.maximum_latency_ms).toFixed(3)} ms` : 'N/A'} detail="Observed worst sample" />
        <MetricCard label="Predicted next execution time" value={payload?.predicted_latency_ms != null ? `${Number(payload.predicted_latency_ms).toFixed(3)} ms` : 'N/A'} detail="Forecasted workload" />
      </section>

      <div className="panel alert-panel">
        <div className="panel-header"><h3>Prediction interpretation</h3></div>
        <p>{payload?.interpretation || 'No prediction available.'}</p>
        <div className="status-strip">
          <span className={`status-badge badge-${payload?.status === 'READY' ? 'success' : 'warning'}`}>{payload?.status || 'UNAVAILABLE'}</span>
        </div>
      </div>
    </>
  );
}

export default Predictions;
