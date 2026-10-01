import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';
import MetricCard from '../components/MetricCard';

function Anomalies() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadData() {
    try {
      setError('');
      const data = await api.anomalies();
      setPayload(data);
    } catch (loadError) {
      setError(loadError.message || 'Unable to load anomaly data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const chartData = useMemo(() => {
    const counts = { Normal: 0, Anomaly: 0 };
    (payload?.records || []).forEach((record) => {
      const label = record.status || 'Normal';
      counts[label] = (counts[label] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [payload]);

  if (loading) return <LoadingState message="Loading anomaly detection results…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>Anomaly data unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <Header title="Anomalies" lastUpdated={new Date().toLocaleString()} onRefresh={loadData} refreshing={loading} status="Monitoring" />

      <section className="stats-grid compact">
        <MetricCard label="Total anomalies" value={payload?.total ?? 0} detail="Isolation Forest flagged records" tone="danger" />
        <MetricCard label="Normal observations" value={Math.max(0, (payload?.records || []).length - (payload?.total || 0))} detail="Non-anomalous records" />
        <MetricCard label="Anomaly ratio" value={payload?.total ? `${((payload.total / Math.max((payload.records || []).length, 1)) * 100).toFixed(2)}%` : '0.00%'} detail="Detected outliers" />
      </section>

      <div className="chart-grid double-wide">
        <div className="panel">
          <div className="panel-header"><h3>Normal vs anomalous observations</h3></div>
          <div className="chart-wrap small-chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2c3950" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="#f97316" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><h3>Anomaly distribution</h3></div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={48} outerRadius={84} paddingAngle={2}>
                  {chartData.map((entry, index) => (
                    <Cell key={`${entry.name}-${index}`} fill={index === 0 ? '#22c55e' : '#f97316'} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><h3>Anomaly records</h3></div>
        <table>
          <thead>
            <tr>
              <th>Metric ID</th>
              <th>Execution time</th>
              <th>Rows returned</th>
              <th>Recorded at</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {(payload?.records || []).slice(0, 25).map((record) => (
              <tr key={record.metric_id || record.recorded_at}>
                <td>{record.metric_id ?? '—'}</td>
                <td>{Number(record.execution_time_ms || 0).toFixed(3)} ms</td>
                <td>{record.rows_returned ?? '—'}</td>
                <td>{record.recorded_at || '—'}</td>
                <td><span className={`status-badge badge-${record.status === 'Anomaly' ? 'danger' : 'success'}`}>{record.status || 'Normal'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default Anomalies;
