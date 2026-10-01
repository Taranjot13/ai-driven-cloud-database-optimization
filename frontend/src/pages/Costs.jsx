import { useEffect, useState } from 'react';
import { api } from '../api/client';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';
import MetricCard from '../components/MetricCard';

function Costs() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadData() {
    try {
      setError('');
      const data = await api.costs();
      setPayload(data);
    } catch (loadError) {
      setError(loadError.message || 'Unable to load cost data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading) return <LoadingState message="Loading cost model data…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>Cost analysis unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <Header title="Costs" lastUpdated={new Date().toLocaleString()} onRefresh={loadData} refreshing={loading} status={payload?.status || 'COST_EFFICIENT'} />

      <section className="stats-grid compact">
        <MetricCard label="Estimated monthly total" value={payload?.estimated_monthly_cost != null ? `$${Number(payload.estimated_monthly_cost).toFixed(2)}` : '$0.00'} detail="Reference total" />
        <MetricCard label="Compute cost" value={payload?.compute_cost != null ? `$${Number(payload.compute_cost).toFixed(2)}` : '$0.00'} detail="Compute layer" />
        <MetricCard label="Storage cost" value={payload?.storage_cost != null ? `$${Number(payload.storage_cost).toFixed(2)}` : '$0.00'} detail="Storage footprint" />
        <MetricCard label="Connection cost" value={payload?.connection_cost != null ? `$${Number(payload.connection_cost).toFixed(2)}` : '$0.00'} detail="Connection overhead" />
        <MetricCard label="Database size" value={payload?.database_size_gb != null ? `${Number(payload.database_size_gb).toFixed(4)} GB` : '0.0000 GB'} detail="Current dataset" />
        <MetricCard label="Cost status" value={payload?.status || 'UNKNOWN'} detail="Cloud-agnostic cost model" tone="success" />
      </section>

      <div className="panel">
        <div className="panel-header"><h3>Cloud-Agnostic Reference Cost Model</h3></div>
        <div className="detail-grid">
          <div><span>Model notice</span><strong>{payload?.billing_notice || 'Estimates are for project evaluation and are not cloud billing.'}</strong></div>
          <div><span>Recommendations</span><strong>{payload?.recommendations?.length ? payload.recommendations.join('; ') : 'No cost recommendations required.'}</strong></div>
        </div>
      </div>
    </>
  );
}

export default Costs;
