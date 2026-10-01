function StatusBadge({ value }) {
  const normalized = String(value || 'Operational').toUpperCase();
  const tone =
    normalized.includes('CRITICAL') || normalized.includes('HIGH') || normalized.includes('ROLLBACK') || normalized.includes('ERROR')
      ? 'danger'
      : normalized.includes('WARNING') || normalized.includes('MEDIUM') || normalized.includes('POTENTIAL')
        ? 'warning'
        : normalized.includes('UNHEALTHY') || normalized.includes('FAIL')
          ? 'danger'
          : 'success';

  return <span className={`status-badge badge-${tone}`}>{normalized}</span>;
}

export default StatusBadge;
