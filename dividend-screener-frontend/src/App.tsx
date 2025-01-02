import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import ScreenerPage from './pages/ScreenerPage';
import DetailPage from './pages/DetailPage';
import DripPage from './pages/DripPage';
import CalendarPage from './pages/CalendarPage';
import { FC } from 'react';
import { fetchStockDetail, runDripSimulation } from './services/api';

const App: FC = () => {
  return (
    <div>
      <Navbar />
      <div className="container mt-4">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/screener" element={<ScreenerPage />} />
          <Route path="/detail/:code" element={<DetailPage />} />
          <Route path="/drip" element={<DripPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
        </Routes>
      </div>
    </div>
  );
};

export default App;
