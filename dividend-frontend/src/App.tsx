import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainPage from './pages/MainPage';
import DividendScreenerPage from './pages/DividendScreenerPage';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/dividend" element={<DividendScreenerPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
