import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Rankings from './pages/Rankings';
import Predictions from './pages/Predictions';
import Simulation from './pages/Simulation';
import Game from './pages/Game';
import Layout from './components/Layout';
import TickerDetail from './pages/TickerDetail';
import CompanyProfiles from './pages/CompanyProfiles';
import Formulas from './pages/Formulas';

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="rankings" element={<Rankings />} />
            <Route path="predictions" element={<Predictions />} />
            <Route path="simulation" element={<Simulation />} />
            <Route path="game" element={<Game />} />
            <Route path="profiles" element={<CompanyProfiles />} />
            <Route path="formulas" element={<Formulas />} />
            <Route path="app/ticker/:symbol" element={<TickerDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
