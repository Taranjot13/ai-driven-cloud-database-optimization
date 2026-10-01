import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/performance', label: 'Performance' },
  { to: '/anomalies', label: 'Anomalies' },
  { to: '/predictions', label: 'Predictions' },
  { to: '/optimizations', label: 'Optimizations' },
  { to: '/resources', label: 'Resources' },
  { to: '/costs', label: 'Costs' },
  { to: '/system', label: 'System' },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-mark">DB</div>
        <div>
          <div className="eyebrow">Autonomous platform</div>
          <h1>Optimizer</h1>
        </div>
      </div>

      <nav className="nav-menu" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-note">
        <span className="status-dot success" />
        Read-only monitoring enabled
      </div>
    </aside>
  );
}

export default Sidebar;
