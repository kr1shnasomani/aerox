import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import ProcessPage from './pages/ProcessPage';
import AgencyListPage from './pages/AgencyListPage';
import AgencyDetailPage from './pages/AgencyDetailPage';
import NegotiatePage from './pages/NegotiatePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/process" element={<ProcessPage />} />
          <Route path="/agencies" element={<AgencyListPage />} />
          <Route path="/agencies/:companyId" element={<AgencyDetailPage />} />
          <Route path="/negotiate" element={<NegotiatePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
