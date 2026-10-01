import { Route, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Performance from './pages/Performance';
import Anomalies from './pages/Anomalies';
import Predictions from './pages/Predictions';
import Optimizations from './pages/Optimizations';
import Resources from './pages/Resources';
import Costs from './pages/Costs';
import System from './pages/System';

function App() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="content-shell">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/performance" element={<Performance />} />
          <Route path="/anomalies" element={<Anomalies />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/optimizations" element={<Optimizations />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/costs" element={<Costs />} />
          <Route path="/system" element={<System />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
