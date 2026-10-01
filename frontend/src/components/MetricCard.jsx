function MetricCard({ label, value, detail, tone = 'neutral' }) {
  return (
    <div className={`metric-card tone-${tone}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value ?? '—'}</div>
      {detail ? <div className="metric-detail">{detail}</div> : null}
    </div>
  );
}

export default MetricCard;
