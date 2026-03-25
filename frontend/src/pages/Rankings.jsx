import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { rankingsApi } from '../api/client';

export default function Rankings() {
  const { lang } = useApp();
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    rankingsApi.getRankings(10, 90)
      .then(setRankings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const t = {
    es: { pt: 'Rankings', ps: 'Tabla de rankings por score compuesto', th1: 'Instrumento', th2: 'Ret. 30d', th3: 'Ret. 90d', th4: 'Vol.', th5: 'Score' },
    en: { pt: 'Rankings', ps: 'Rankings table by composite score', th1: 'Instrument', th2: 'Ret. 30d', th3: 'Ret. 90d', th4: 'Vol.', th5: 'Score' }
  };
  const texts = t[lang];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div>
      <div className="page-title">{texts.pt}</div>
      <div className="page-sub">{texts.ps}</div>
      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr><th>#</th><th>{texts.th1}</th><th className="right">{texts.th2}</th><th className="right">{texts.th3}</th><th className="right">{texts.th4}</th><th className="right">{texts.th5}</th></tr>
            </thead>
            <tbody>
              {rankings.map(r => (
                <tr key={r.ticker}>
                  <td>{r.rank}</td>
                  <td><div className="ticker-name">{r.ticker}</div><div className="ticker-sector">{r.display_name}</div></td>
                  <td className="right"><span className={`badge ${r.return_30d >= 0 ? 'badge-green' : 'badge-red'}`}>{r.return_30d ? `${(r.return_30d * 100).toFixed(1)}%` : '-'}</span></td>
                  <td className="right">{r.return_90d ? `${(r.return_90d * 100).toFixed(1)}%` : '-'}</td>
                  <td className="right">{r.annualized_volatility ? `${(r.annualized_volatility * 100).toFixed(1)}%` : '-'}</td>
                  <td className="right">{r.score.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
