import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { simulationApi, pricesApi } from '../api/client';

export default function Simulation() {
  const { lang } = useApp();
  const [tickers, setTickers] = useState([]);
  const [selected, setSelected] = useState('');
  const [action, setAction] = useState('BUY');
  const [amount, setAmount] = useState(10000);
  const [simulations, setSimulations] = useState([]);
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    pricesApi.listTickers().then(setTickers).catch(console.error);
    loadSimulations();
  }, []);

  async function loadSimulations() {
    try {
      const [s, sc] = await Promise.all([simulationApi.list(), simulationApi.getScore()]);
      setSimulations(s);
      setScore(sc);
    } catch (e) { console.error(e); }
  }

  async function createSimulation() {
    if (!selected || amount <= 0) return;
    setLoading(true);
    try {
      await simulationApi.create(selected, action, amount, 100, '');
      await loadSimulations();
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }

  const t = {
    es: { pt: 'Simulador', ps: 'Paper trading', newTrade: 'Nueva operacion', ticker: 'Instrumento', action: 'Accion', amount: 'Monto (MXN)', btn: 'Ejecutar', perf: 'Rendimiento', total: 'Total trades', pnl: 'P&L total' },
    en: { pt: 'Simulator', ps: 'Paper trading', newTrade: 'New trade', ticker: 'Instrument', action: 'Action', amount: 'Amount (MXN)', btn: 'Execute', perf: 'Performance', total: 'Total trades', pnl: 'Total P&L' }
  };
  const texts = t[lang];

  return (
    <div>
      <div className="page-title">{texts.pt}</div>
      <div className="page-sub">{texts.ps}</div>
      
      <div className="grid-2">
        <div className="card">
          <div className="card-header"><div className="card-title">{texts.newTrade}</div></div>
          <div style={{ padding: '1rem' }}>
            <select value={selected} onChange={e => setSelected(e.target.value)} style={{ width: '100%', marginBottom: '0.5rem', padding: '0.5rem' }}>
              <option value="">{texts.ticker}</option>
              {tickers.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={action} onChange={e => setAction(e.target.value)} style={{ width: '100%', marginBottom: '0.5rem', padding: '0.5rem' }}>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
            <input type="number" value={amount} onChange={e => setAmount(Number(e.target.value))} placeholder={texts.amount} style={{ width: '100%', marginBottom: '0.5rem', padding: '0.5rem' }} />
            <button className="btn-primary" onClick={createSimulation} disabled={!selected || amount <= 0 || loading} style={{ width: '100%' }}>
              {loading ? '...' : texts.btn}
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><div className="card-title">{texts.perf}</div></div>
          <div style={{ padding: '1rem' }}>
            {score && (
              <>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{texts.total}: <strong>{score.total_trades}</strong></div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{texts.pnl}: <strong style={{ color: score.total_pnl >= 0 ? '#4caf82' : '#e05b5b' }}>${score.total_pnl.toFixed(2)}</strong></div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: '1rem' }}>
        <div className="card-header"><div className="card-title">Historial</div></div>
        <table>
          <thead><tr><th>Ticker</th><th>Accion</th><th>Monto</th><th>Entry</th><th>P&L</th></tr></thead>
          <tbody>
            {simulations.map(s => (
              <tr key={s.id}>
                <td>{s.ticker}</td>
                <td><span className={`badge ${s.action === 'BUY' ? 'badge-green' : 'badge-red'}`}>{s.action}</span></td>
                <td>${s.hypothetical_amount_mxn.toLocaleString()}</td>
                <td>${s.entry_price?.toFixed(2)}</td>
                <td style={{ color: s.hypothetical_pnl >= 0 ? '#4caf82' : '#e05b5b' }}>{s.hypothetical_pnl ? `$${s.hypothetical_pnl.toFixed(2)}` : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
