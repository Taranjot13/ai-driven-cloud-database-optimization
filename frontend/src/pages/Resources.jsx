import { useEffect, useState } from 'react';
import { api } from '../api/client';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';
import MetricCard from '../components/MetricCard';

function Resources() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadData() {
    try {
      setError('');
      const data = await api.resources();
      setPayload(data);
    } catch (loadError) {
      setError(loadError.message || 'Unable to load resource health data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading) return <LoadingState message="Loading resource metrics…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>Resource data unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <Header title="Resources" lastUpdated={new Date().toLocaleString()} onRefresh={loadData} refreshing={loading} status={payload?.status || 'Operational'} />

      <section className="stats-grid compact">
        <MetricCard label="Active connections" value={payload?.active_connections ?? '—'} detail="Current open sockets" />
        <MetricCard label="Max connections" value={payload?.max_connections ?? '—'} detail="Configured cap" />
        <MetricCard label="Connection utilization" value={payload?.connection_utilization != null ? `${Number(payload.connection_utilization).toFixed(2)}%` : '0.00%'} detail="Resource pressure" />
        <MetricCard label="Cache hit ratio" value={payload?.cache_hit_ratio != null ? `${Number(payload.cache_hit_ratio).toFixed(2)}%` : '0.00%'} detail="Read efficiency" />
        <MetricCard label="Rollback rate" value={payload?.rollback_rate != null ? `${Number(payload.rollback_rate).toFixed(2)}%` : '0.00%'} detail="Query stability" />
        <MetricCard label="Database size" value={payload?.database_size_gb != null ? `${Number(payload.database_size_gb).toFixed(4)} GB` : '0.0000 GB'} detail="Storage impact" />
      </section>

      <div className="panel">
        <div className="panel-header"><h3>Resource status and recommendations</h3></div>
        <div className="detail-grid">
          <div><span>Resource status</span><strong>{payload?.status || 'UNKNOWN'}</strong></div>
          <div><span>Recommendations</span><strong>{payload?.recommendations?.length ? payload.recommendations.join('; ') : 'No specific resource warnings.'}</strong></div>
        </div>
      </div>
    </>
  );
}

export default Resources;
