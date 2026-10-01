import { useEffect, useMemo, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import DataTable from '../components/DataTable';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';

function Performance() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [lastUpdated, setLastUpdated] = useState('');

  async function loadData() {
    try {
      setError('');
      const payload = await api.performance({ limit: 500 });
      setRecords(payload.records || []);
      setSelected(payload.records?.[0] || null);
      setLastUpdated(new Date().toLocaleString());
    } catch (loadError) {
      setError(loadError.message || 'Unable to load performance records.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const chartData = useMemo(
    () =>
      records.map((record, index) => ({
        name: `#${index + 1}`,
        latency: Number(record.execution_time_ms || 0),
      })),
    [records],
  );

  if (loading) return <LoadingState message="Loading query performance data…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>Performance data unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <Header title="Performance" lastUpdated={lastUpdated || 'Just now'} onRefresh={loadData} refreshing={loading} status="Operational" />

      <div className="panel">
        <div className="panel-header"><h3>Execution latency trend</h3></div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="perfFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.6} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2c3950" />
              <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="latency" stroke="#22c55e" fill="url(#perfFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><h3>Query performance table</h3></div>
        <DataTable
          title="Query observations"
          rows={records}
          onRowClick={(row) => setSelected(row)}
          columns={[
            { key: 'metric_id', label: 'Metric ID' },
            { key: 'execution_time_ms', label: 'Execution time' },
            { key: 'rows_returned', label: 'Rows returned' },
            { key: 'recorded_at', label: 'Timestamp' },
            { key: 'slow_query', label: 'Slow query', render: (value) => (value ? 'Yes' : 'No') },
          ]}
          emptyLabel="No performance data is available."
        />
      </div>

      {selected ? (
        <div className="panel detail-panel">
          <div className="panel-header"><h3>Query detail</h3></div>
          <div className="detail-grid">
            <div><span>SQL text</span><strong>{selected.query_text || 'No query text recorded.'}</strong></div>
            <div><span>Execution time</span><strong>{Number(selected.execution_time_ms || 0).toFixed(3)} ms</strong></div>
            <div><span>Rows returned</span><strong>{selected.rows_returned ?? '—'}</strong></div>
            <div><span>Query plan status</span><strong>{selected.query_plan_status || 'Not available in current schema'}</strong></div>
            <div><span>Index information</span><strong>{selected.index_information || 'No index metadata recorded.'}</strong></div>
            <div><span>Recommendation</span><strong>{selected.recommendation || 'No recommendation available.'}</strong></div>
            <div><span>Autonomous decision</span><strong>{selected.autonomous_decision || 'Monitoring only'}</strong></div>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default Performance;
