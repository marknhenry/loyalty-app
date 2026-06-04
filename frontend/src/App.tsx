import { Routes, Route } from 'react-router-dom';
import { Nav } from './components/Nav/Nav';
import { DashboardPage } from './pages/DashboardPage';
import { ExchangePage } from './pages/ExchangePage';
import { RedemptionPage } from './pages/RedemptionPage';
import './App.css';

function App() {
  return (
    <div className="app-shell">
      <Nav />
      <main className="app-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/exchange" element={<ExchangePage />} />
          <Route path="/redeem" element={<RedemptionPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
