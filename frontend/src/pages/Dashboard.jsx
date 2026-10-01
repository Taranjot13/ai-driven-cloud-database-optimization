import { useEffect, useMemo, useState } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api/client';
import Header from '../components/Header';
import LoadingState from '../components/LoadingState';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';

const chartColors = ['#22c55e', '#60a5fa', '#fbbf24', '#f97316', '#a78bfa', '#f43f5e'];

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  async function loadData() {
    try {
      setError('');
      const [dashboard, overview] = await Promise.all([api.dashboard(), api.systemStatus()]);
      const merged = {
        ...dashboard,
        system: overview,
      };
      setData(merged);
      setLastUpdated(new Date().toLocaleString());
    } catch (loadError) {
      setError(loadError.message || 'Unable to load the dashboard.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const latencyData = useMemo(
    () =>
      (data?.performance?.records || []).map((record, index) => ({
        index: index + 1,
        latency: Number(record.execution_time_ms || 0),
        rows: Number(record.rows_returned || 0),
        label: record.recorded_at ? new Date(record.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : `#${index + 1}`,
      })),
    [data],
  );

  const decisionFlow = useMemo(() => {
    const latestDecision = data?.latest_recorded_decision || 'MONITOR';
    const learningRisk = data?.learning?.risk_level || 'UNKNOWN';
    const resourceStatus = data?.resources?.status || 'UNKNOWN';
    const costStatus = data?.costs?.status || 'UNKNOWN';
    return [
      { stage: 'Observe', value: `${data?.performance?.summary?.observations ?? 0} observations` },
      { stage: 'Analyze', value: `${data?.anomalies?.total ?? 0} anomalies` },
      { stage: 'Predict', value: `${data?.prediction?.predicted_latency_ms ?? '—'} ms` },
      { stage: 'Decide', value: latestDecision },
      { stage: 'Act', value: data?.latest_recorded_decision || 'Monitor' },
      { stage: 'Verify', value: data?.optimization?.summary?.successful ?? 0 },
      { stage: 'Learn', value: learningRisk },
      { stage: 'Resources', value: resourceStatus },
      { stage: 'Cost', value: costStatus },
    ];
  }, [data]);

  const optimizationBreakdown = useMemo(
    () =>
      Object.entries(data?.optimization?.summary?.decisions || {}).map(([name, value]) => ({
        name,
        value,
      })),
    [data],
  );

  const resourceBreakdown = [
    { name: 'Connection util.', value: Number(data?.resources?.connection_utilization ?? 0) },
    { name: 'Cache hit ratio', value: Number(data?.resources?.cache_hit_ratio ?? 0) },
    { name: 'Rollback rate', value: Number(data?.resources?.rollback_rate ?? 0) },
  ];

  const costBreakdown = [
    { name: 'Compute', value: Number(data?.costs?.compute_cost ?? 0) },
    { name: 'Storage', value: Number(data?.costs?.storage_cost ?? 0) },
    { name: 'Connection', value: Number(data?.costs?.connection_cost ?? 0) },
  ];

  if (loading) return <LoadingState message="Loading dashboard telemetry…" />;

  if (error) {
    return (
      <div className="panel error-panel">
        <h3>Dashboard unavailable</h3>
        <p>{error}</p>
        <button className="primary-button" onClick={() => { setRefreshing(true); loadData(); }}>
          Retry
        </button>
      </div>
    );
  }

  const summary = data?.performance?.summary || {};
  const optimization = data?.optimization?.summary || {};
  const prediction = data?.prediction || {};
  const resources = data?.resources || {};
  const costs = data?.costs || {};

  return (
    <>
      <Header
        title="System Overview"
        lastUpdated={lastUpdated || 'Just now'}
        onRefresh={() => {
          setRefreshing(true);
          loadData();
        }}
        refreshing={refreshing}
        status={data?.system?.status || 'Operational'}
      />

      <section className="stats-grid">
        <MetricCard label="Average latency" value={`${Number(summary.average || 0).toFixed(3)} ms`} detail="Rolling workload mean" tone="accent" />
        <MetricCard label="Median latency" value={`${Number(summary.median || 0).toFixed(3)} ms`} detail="Central performance value" />
        <MetricCard label="P95 latency" value={`${Number(summary.p95 || 0).toFixed(3)} ms`} detail="High-end latency boundary" tone="warning" />
        <MetricCard label="P99 latency" value={`${Number(summary.p99 || 0).toFixed(3)} ms`} detail="Tail-end latency" />
        <MetricCard label="Maximum latency" value={`${Number(summary.maximum || 0).toFixed(3)} ms`} detail="Worst observed sample" tone="danger" />
        <MetricCard label="Slow queries" value={summary.slow_queries ?? 0} detail="Queries > 5.0 ms" tone="warning" />
      </section>

      <section className="stats-grid compact">
        <MetricCard label="Historical observations" value={summary.observations ?? 0} detail="Recorded metric samples" />
        <MetricCard label="Detected anomalies" value={data?.anomalies?.total ?? 0} detail="Isolation Forest results" />
        <MetricCard label="Predicted next latency" value={prediction.predicted_latency_ms != null ? `${Number(prediction.predicted_latency_ms).toFixed(3)} ms` : 'Not enough data'} detail={prediction.interpretation || 'Awaiting prediction'} />
        <MetricCard label="Prediction status" value={prediction.status || 'UNKNOWN'} detail="ML forecast health" />
        <MetricCard label="Learning success rate" value={data?.learning?.success_rate != null ? `${Number(data.learning.success_rate).toFixed(2)}%` : '0.00%'} detail={data?.learning?.risk_level || 'Unknown risk'} />
      </section>

      <section className="stats-grid compact">
        <MetricCard label="Optimization attempts" value={optimization.attempts ?? 0} detail="History entries" />
        <MetricCard label="Successful / verified" value={optimization.successful ?? 0} detail="Confirmed outcome" tone="success" />
        <MetricCard label="Rollbacks" value={optimization.rollbacks ?? 0} detail="Safety mechanism triggered" tone="warning" />
        <MetricCard label="Avg success improvement" value={optimization.average_successful_improvement != null ? `${Number(optimization.average_successful_improvement).toFixed(2)}%` : '0.00%'} detail="Prosperous optimization variance" />
        <MetricCard label="Success rate" value={optimization.success_rate != null ? `${Number(optimization.success_rate).toFixed(2)}%` : '0.00%'} detail="Overall outcome rate" />
      </section>

      <section className="stats-grid compact">
        <MetricCard label="Connection utilization" value={resources.connection_utilization != null ? `${Number(resources.connection_utilization).toFixed(2)}%` : '0.00%'} detail="Active connection load" />
        <MetricCard label="Cache hit ratio" value={resources.cache_hit_ratio != null ? `${Number(resources.cache_hit_ratio).toFixed(2)}%` : '0.00%'} detail="Buffer efficiency" />
        <MetricCard label="Rollback rate" value={resources.rollback_rate != null ? `${Number(resources.rollback_rate).toFixed(2)}%` : '0.00%'} detail="Operational instability" />
        <MetricCard label="Database size" value={resources.database_size_gb != null ? `${Number(resources.database_size_gb).toFixed(4)} GB` : '0.0000 GB'} detail="Current storage footprint" />
      </section>

      <section className="stats-grid compact">
        <MetricCard label="Estimated monthly total" value={costs.estimated_monthly_cost != null ? `$${Number(costs.estimated_monthly_cost).toFixed(2)}` : '$0.00'} detail="Cloud-agnostic model" />
        <MetricCard label="Compute cost" value={costs.compute_cost != null ? `$${Number(costs.compute_cost).toFixed(2)}` : '$0.00'} />
        <MetricCard label="Storage cost" value={costs.storage_cost != null ? `$${Number(costs.storage_cost).toFixed(2)}` : '$0.00'} />
        <MetricCard label="Connection cost" value={costs.connection_cost != null ? `$${Number(costs.connection_cost).toFixed(2)}` : '$0.00'} />
        <MetricCard label="Cost status" value={costs.status || 'UNKNOWN'} detail="Reference model only" tone={costs.status === 'COST_EFFICIENT' ? 'success' : 'warning'} />
      </section>

      <section className="decision-panel panel">
        <div className="panel-header inline-header">
          <h3>Autonomous decision loop</h3>
          <StatusBadge value={data?.latest_recorded_decision || 'Monitoring'} />
        </div>

        <div className="decision-flow">
          {decisionFlow.map((item) => (
            <div key={item.stage} className="decision-step">
              <div className="stage-name">{item.stage}</div>
              <div className="stage-value">{item.value}</div>
            </div>
          ))}
        </div>

        <div className="decision-details">
          <div className="detail-block">
            <span>Selected action</span>
            <strong>{data?.decision_analysis_status || data?.latest_recorded_decision || 'MONITOR'}</strong>
          </div>
          <div className="detail-block">
            <span>Learning risk</span>
            <strong>{data?.learning?.risk_level || 'UNKNOWN'}</strong>
          </div>
          <div className="detail-block">
            <span>Policy</span>
            <strong>{data?.decision?.policy || 'ACTIVE'}</strong>
          </div>
          <div className="detail-block">
            <span>Target table</span>
            <strong>{data?.decision?.target?.table_name || 'Monitoring only'}</strong>
          </div>
        </div>
      </section>

      <section className="chart-grid">
        <div className="panel">
          <div className="panel-header"><h3>Latency over time</h3></div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={latencyData}>
                <defs>
                  <linearGradient id="latencyFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.7} />
                    <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2c3950" />
                <XAxis dataKey="label" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="latency" stroke="#60a5fa" fill="url(#latencyFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><h3>Optimization decision breakdown</h3></div>
          <div className="chart-wrap small-chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={optimizationBreakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2c3950" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="#22c55e" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><h3>Resource utilization</h3></div>
          <div className="chart-wrap small-chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={resourceBreakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2c3950" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="#a78bfa" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><h3>Cost model breakdown</h3></div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={costBreakdown} dataKey="value" nameKey="name" innerRadius={52} outerRadius={88} paddingAngle={2}>
                  {costBreakdown.map((entry, index) => (
                    <Cell key={`${entry.name}-${index}`} fill={chartColors[index % chartColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
    </>
  );
}

export default Dashboard;
