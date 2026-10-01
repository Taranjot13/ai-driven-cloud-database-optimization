import StatusBadge from './StatusBadge';

function Header({ title, lastUpdated, onRefresh, refreshing, status }) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">Database Observability</p>
        <h2>{title}</h2>
      </div>

      <div className="header-actions">
        <StatusBadge value={status || 'Operational'} />
        <button className="secondary-button" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="last-updated">Last updated: {lastUpdated || '—'}</div>
    </header>
  );
}

export default Header;
