import { useState, useEffect } from 'react';
import { predictionsApi, pricesApi } from '../api/client';
import FanChart from '../components/charts/FanChart';

export default function Predictions() {
  const [tickers, setTickers] = useState([]);
  const [selected, setSelected] = useState('');
  const [horizon, setHorizon] = useState(30);
  const [result, setResult] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    pricesApi.listTickers().then(setTickers).catch(console.error);
  }, []);

  useEffect(() => {
    if (selected) {
      pricesApi.getHistory(selected, 60).then(setHistoricalData).catch(console.error);
    }
  }, [selected]);

  async function runPrediction() {
    if (!selected) return;
    setLoading(true);
    try {
      const r = await predictionsApi.run(selected, horizon);
      setResult(r);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const texts = {
    pt: 'Monte Carlo Predictions',
    ps: 'Run statistical forecast simulations for BMV instruments',
    btn: 'Run Prediction',
    h7: '7 days',
    h30: '30 days',
    h90: '90 days',
    selectTicker: 'Select ticker',
    horizonLabel: 'Forecast Horizon',
  };

  return (
    <div>
      <div className="page-title">{texts.pt}</div>
      <div className="page-sub">{texts.ps}</div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ padding: '1rem' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
            <select 
              value={selected} 
              onChange={e => setSelected(e.target.value)} 
              style={{ padding: '0.5rem 1rem', background: 'var(--bg-card2)', border: '1px solid var(--border-col)', borderRadius: '6px', color: 'var(--text-main)' }}
            >
              <option value="">{texts.selectTicker}</option>
              {tickers.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <select 
              value={horizon} 
              onChange={e => setHorizon(Number(e.target.value))} 
              style={{ padding: '0.5rem 1rem', background: 'var(--bg-card2)', border: '1px solid var(--border-col)', borderRadius: '6px', color: 'var(--text-main)' }}
            >
              <option value={7}>{texts.h7}</option>
              <option value={30}>{texts.h30}</option>
              <option value={90}>{texts.h90}</option>
            </select>
            <button className="btn-primary" onClick={runPrediction} disabled={!selected || loading}>
              {loading ? 'Running...' : texts.btn}
            </button>
          </div>
        </div>
        {result && (
          <div style={{ padding: '1rem', borderTop: '0.5px solid var(--border-col)' }}>
            <div style={{ marginBottom: '1rem' }}>
              <strong>{result.ticker}</strong> - {result.horizon_days} days forecast | Last close: ${result.last_close?.toFixed(2)}
            </div>
            <FanChart 
              historicalData={historicalData}
              percentile25={result.percentile_25} 
              percentile50={result.percentile_50} 
              percentile75={result.percentile_75} 
              horizonDays={result.horizon_days}
              height={320}
            />
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">How Monte Carlo Predictions Work</div>
        </div>
        <div style={{ padding: '1rem', fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          <p style={{ marginBottom: '1rem' }}>
            Monte Carlo simulation is a statistical technique that uses random sampling to generate a range of possible outcomes.
          </p>
          <p style={{ marginBottom: '1rem' }}>
            <strong>Methodology:</strong> The algorithm runs thousands of simulations based on historical price volatility and returns. 
            Each simulation generates a potential future price path. The results are aggregated to produce probability distributions 
            showing the 25th, 50th (median), and 75th percentile outcomes.
          </p>
          <p>
            <strong>Educational Value:</strong> This helps investors understand the range of possible outcomes and the probability 
            of different price movements. It is NOT a prediction of future prices, but rather a tool for risk assessment.
          </p>
        </div>
      </div>
    </div>
  );
}
