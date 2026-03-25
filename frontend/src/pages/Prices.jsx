import { useState, useEffect } from 'react';
import { pricesApi } from '../api/client';

export default function Prices() {
  const [tickers, setTickers] = useState([]);
  const [selected, setSelected] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    pricesApi.listTickers().then(setTickers).catch(console.error);
  }, []);

  async function loadPrice() {
    if (!selected) return;
    setLoading(true);
    try {
      const d = await pricesApi.getHistory(selected);
      setData(d);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 style={{ color: '#e6edf3', marginBottom: '2rem' }}>Prices</h1>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <select value={selected} onChange={e => setSelected(e.target.value)} style={{ padding: '0.75rem', background: '#0d1117', border: '1px solid #30363d', borderRadius: '6px', color: '#e6edf3', minWidth: '200px' }}>
          <option value="">Select ticker</option>
          {tickers.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <button onClick={loadPrice} disabled={!selected || loading} style={{ padding: '0.75rem 1.5rem', background: '#238636', border: 'none', borderRadius: '6px', color: '#fff', cursor: selected && !loading ? 'pointer' : 'not-allowed', opacity: selected && !loading ? 1 : 0.5 }}>Load</button>
      </div>
      {data && (
        <div style={{ background: '#161b22', padding: '1.5rem', borderRadius: '6px', border: '1px solid #21262d', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #21262d' }}>
                <th style={{ textAlign: 'left', padding: '0.75rem', color: '#8b949e' }}>Date</th>
                <th style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>Open</th>
                <th style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>High</th>
                <th style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>Low</th>
                <th style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>Close</th>
                <th style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>Volume</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '0.75rem', color: '#e6edf3' }}>{row.date}</td>
                  <td style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>{row.open?.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>{row.high?.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>{row.low?.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>{row.close?.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', padding: '0.75rem', color: '#8b949e' }}>{row.volume?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
