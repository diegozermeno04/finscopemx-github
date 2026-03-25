import { useState, useEffect } from 'react';
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';
import { pricesApi, rankingsApi } from '../api/client';

export default function Formulas() {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logReturn, setLogReturn] = useState(null);
  const [rankings, setRankings] = useState([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const ticker = 'WALMEX.MX';
        const history = await pricesApi.getHistory(ticker, null, null);
        const hist = history?.data || history;
        
        if (hist && hist.length >= 2) {
          const latest = hist[hist.length - 1];
          const previous = hist[hist.length - 2];
          
          const latestPrice = parseFloat(latest.close);
          const previousPrice = parseFloat(previous.close);
          const logRet = Math.log(latestPrice / previousPrice);
          
          setMarketData({
            ticker,
            latestPrice,
            previousPrice,
            date: latest.date || latest.Date,
            previousDate: previous.date || previous.Date,
            logReturn: logRet
          });
          setLogReturn(logRet);
        }

        const ranks = await rankingsApi.getRankings(15, 90);
        setRankings(ranks);
      } catch (e) {
        console.error('Failed to fetch market data:', e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const renderLiveExample = () => {
    if (!marketData) return null;
    return (
      <div style={{
        background: 'rgba(76,175,130,0.08)',
        border: '1px solid rgba(76,175,130,0.2)',
        borderRadius: '8px',
        padding: '1rem',
        marginTop: '0.75rem'
      }}>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
          Live Example using {marketData.ticker}
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text-main)', fontFamily: 'monospace' }}>
          <div>P<sub>t</sub> (today's close): <strong>${marketData.latestPrice.toFixed(2)}</strong></div>
          <div>P<sub>t-1</sub> (yesterday's close): <strong>${marketData.previousPrice.toFixed(2)}</strong></div>
          <div style={{ marginTop: '0.5rem', color: marketData.logReturn >= 0 ? '#4caf82' : '#e05b5b' }}>
            r<sub>t</sub> = ln({marketData.latestPrice.toFixed(2)} / {marketData.previousPrice.toFixed(2)}) = 
            <strong> {(marketData.logReturn * 100).toFixed(4)}%</strong>
          </div>
        </div>
      </div>
    );
  };

  const FormulaSection = ({ title, latex, explanation, liveExample, color }) => (
    <div style={{
      background: 'var(--bg-card2)',
      borderRadius: '12px',
      padding: '1.5rem',
      border: '0.5px solid var(--border-col)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{
          width: 36, height: 36,
          borderRadius: '10px',
          background: color,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 700, fontSize: '16px'
        }}>
          {title.charAt(0)}
        </div>
        <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)' }}>
          {title}
        </div>
      </div>
      
      <div style={{
        background: 'var(--bg-card)',
        borderRadius: '8px',
        padding: '1.25rem',
        marginBottom: '1rem',
        overflowX: 'auto'
      }}>
        <BlockMath>{latex}</BlockMath>
      </div>
      
      <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.7 }}>
        {explanation}
      </div>
      
      {liveExample && renderLiveExample()}
    </div>
  );

  return (
    <div>
      <div className="page-title">Formulas & Methodology</div>
      <div className="page-sub">Academic foundations and live market data examples from the Mexican Stock Exchange</div>

      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '200px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              width: 32, height: 32, 
              border: '3px solid var(--border-col)', 
              borderTopColor: 'var(--arma-b)',
              borderRadius: '50%', 
              animation: 'spin 1s linear infinite',
              margin: '0 auto 1rem'
            }}></div>
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Loading live market data...</div>
          </div>
        </div>
      )}

      {!loading && (
        <>
          <div style={{ marginBottom: '2rem' }}>
            <FormulaSection
              title="A. Stochastic Differential Equations (SDEs)"
              color="rgba(138,143,168,0.9)"
              latex="dS_t = \mu S_t \, dt + \sigma S_t \, dW_t"
              explanation={
                <span>
                  This is the <strong>Geometric Brownian Motion (GBM)</strong> model, the foundational framework for equity price dynamics. 
                  The asset price <InlineMath>S_t</InlineMath> follows a stochastic process where <InlineMath>\mu</InlineMath> represents 
                  the drift (expected return) and <InlineMath>\sigma</InlineMath> the volatility. The term <InlineMath>dW_t</InlineMath> 
                  is a Wiener process increment, capturing the random, unpredictable component of market movements.
                </span>
              }
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <FormulaSection
              title="B. Logarithmic Returns (Discrete)"
              color="rgba(76,175,130,0.9)"
              latex="r_t = \ln\left(\frac{P_t}{P_{t-1}}\right) = \ln(P_t) - \ln(P_{t-1})"
              explanation={
                <span>
                  Log returns are preferred over simple returns in quantitative finance due to their time-additivity and 
                  statistical properties. They approximate percentage changes and transform multiplicative processes 
                  into additive ones, enabling easier aggregation across time periods.
                </span>
              }
              liveExample={true}
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <FormulaSection
              title="C. Annualized Volatility"
              color="rgba(224,91,91,0.9)"
              latex="\sigma_{annual} = \sqrt{252} \cdot \sqrt{\frac{1}{N-1} \sum_{t=1}^{N} (r_t - \bar{r})^2}"
              explanation={
                <span>
                  Volatility measures the dispersion of returns and is a key risk metric. Daily returns are calculated 
                  from log prices, then their standard deviation is computed. This is annualized by multiplying by 
                  <InlineMath>\sqrt{252}</InlineMath> (the approximate number of trading days per year in Mexico), 
                  allowing comparison across instruments with different trading calendars.
                </span>
              }
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <FormulaSection
              title="D. Min-Max Normalization"
              color="rgba(218,165,32,0.9)"
              latex="X_{norm} = \frac{X - X_{min}}{X_{max} - X_{min}}"
              explanation={
                <span>
                  To combine heterogeneous metrics (RSI, volatility, returns, momentum) into a single score, 
                  each feature is normalized to the <strong>[0, 1]</strong> range using the observed minimum and maximum 
                  values across all instruments. This preserves the rank ordering while enabling weighted aggregation 
                  of fundamentally different quantities.
                </span>
              }
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <FormulaSection
              title="E. Weighted Aggregation Score"
              color="rgba(33,150,243,0.9)"
              latex="Score = \sum_{i=1}^{n} w_i \cdot X_{i,norm}"
              explanation={
                <span>
                  The final score is a weighted sum of normalized features. Our implementation uses three strategic 
                  pillars: <strong>Return</strong> (momentum), <strong>Risk</strong> (inverse of volatility), and 
                  <strong>RSI/SMA</strong> (technical signals). Each component receives a weight that reflects 
                  its predictive importance, producing a composite ranking from 0-100.
                </span>
              }
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <FormulaSection
              title="F. Technical Indicators"
              color="rgba(156,39,176,0.9)"
              latex="\text{RSI} = 100 - \frac{100}{1 + RS}, \quad RS = \frac{\text{Average Gain}}{\text{Average Loss}}"
              explanation={
                <span>
                  <strong>RSI (Relative Strength Index)</strong> with a 14-day lookback measures momentum on a 0-100 scale. 
                  Values above 70 indicate overbought conditions; below 30 indicate oversold. 
                  <br /><br />
                  <strong>SMA-200 (Simple Moving Average)</strong> with a 200-day lookback is the cornerstone of long-term 
                  trend analysis. Prices above the SMA-200 suggest bullish momentum; below suggests bearish.
                </span>
              }
            />
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <FormulaSection
              title="G. Database Security (ACID)"
              color="rgba(0,150,136,0.9)"
              latex="\text{ACID} = \{ \text{Atomicity}, \text{Consistency}, \text{Isolation}, \text{Durability} \}"
              explanation={
                <span>
                  All market data and user simulations are stored in a PostgreSQL database ensuring the ACID transactional model:
                  <ul style={{ marginTop: '0.5rem', marginBottom: '0.5rem', paddingLeft: '1.25rem' }}>
                    <li><strong>Atomicity:</strong> Each price update or simulation trade executes completely or not at all.</li>
                    <li><strong>Consistency:</strong> All constraints are enforced, preventing invalid state transitions.</li>
                    <li><strong>Isolation:</strong> Concurrent user simulations do not interfere with each other.</li>
                    <li><strong>Durability:</strong> Once committed, Yahoo Finance data and user predictions persist even after system restart.</li>
                  </ul>
                </span>
              }
            />
          </div>

          {marketData && rankings.length > 0 && (
            <div style={{
              background: 'var(--bg-card2)',
              borderRadius: '12px',
              padding: '1.5rem',
              border: '0.5px solid var(--border-col)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{
                  width: 36, height: 36,
                  borderRadius: '10px',
                  background: 'rgba(255,152,0,0.9)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontWeight: 700, fontSize: '16px'
                }}>
                  <span style={{ fontSize: '20px' }}>*</span>
                </div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)' }}>
                  Current Rankings (Live Data)
                </div>
              </div>
              
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                Top instruments by composite score using today's market data
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Instrument</th>
                      <th className="right">Return 30d</th>
                      <th className="right">Return 90d</th>
                      <th className="right">RSI 14</th>
                      <th className="right">Ann. Vol.</th>
                      <th className="right">Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankings.slice(0, 10).map(item => (
                      <tr key={item.ticker}>
                        <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{item.rank}</td>
                        <td>
                          <div className="ticker-name">{item.ticker}</div>
                          <div className="ticker-sector">{item.display_name}</div>
                        </td>
                        <td className="right">
                          <span className={`badge ${item.return_30d >= 0 ? 'badge-green' : 'badge-red'}`}>
                            {item.return_30d ? `${item.return_30d > 0 ? '+' : ''}${(item.return_30d * 100).toFixed(1)}%` : '-'}
                          </span>
                        </td>
                        <td className="right" style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                          {item.return_90d ? `${item.return_90d > 0 ? '+' : ''}${(item.return_90d * 100).toFixed(1)}%` : '-'}
                        </td>
                        <td className="right">
                          <span className={`rsi-chip ${item.rsi >= 70 ? 'hot' : item.rsi <= 30 ? 'cold' : ''}`}>
                            {item.rsi ? item.rsi.toFixed(1) : '-'}
                          </span>
                        </td>
                        <td className="right" style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                          {item.annualized_volatility ? `${(item.annualized_volatility * 100).toFixed(1)}%` : '-'}
                        </td>
                        <td className="right">
                          <span style={{ 
                            fontWeight: 600,
                            color: item.score >= 70 ? '#4caf82' : item.score >= 50 ? '#DAA520' : '#e05b5b'
                          }}>
                            {item.score?.toFixed(0) || '0'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
