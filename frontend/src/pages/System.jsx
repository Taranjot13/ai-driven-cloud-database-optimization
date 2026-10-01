import { useEffect, useState } from 'react';
import { api } from '../api/client';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';

function System() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadData() {
    try {
      setError('');
      const data = await api.systemStatus();
      setPayload(data);
    } catch (loadError) {
      setError(loadError.message || 'Unable to load system details.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  if (loading) return <LoadingState message="Loading system status…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>System status unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <Header title="System" lastUpdated={new Date().toLocaleString()} onRefresh={loadData} refreshing={loading} status={payload?.status || 'Operational'} />

      <div className="panel">
        <div className="panel-header"><h3>System health</h3></div>
        <div className="detail-grid">
          <div><span>Backend health</span><strong>{payload?.status || 'Unknown'}</strong></div>
          <div><span>Database connection</span><strong>{payload?.database || 'Unknown'}</strong></div>
          <div><span>Model version</span><strong>1.0.0</strong></div>
          <div><span>Latest autonomous action</span><strong>{payload?.latest_recorded_decision || 'Monitoring only'}</strong></div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><h3>Available modules</h3></div>
        <ul className="module-list">
          {(payload?.modules || []).map((module) => (
            <li key={module}>{module}</li>
          ))}
        </ul>
      </div>

      <div className="panel">
        <div className="panel-header"><h3>Architecture overview</h3></div>
        <div className="architecture-flow">
          <span>Observe</span>
          <span>Analyze</span>
          <span>Predict</span>
          <span>Decide</span>
          <span>Act</span>
          <span>Verify</span>
          <span>Learn</span>
        </div>
      </div>
    </>
  );
}

export default System;
