import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { rankingsApi, pricesApi } from '../api/client';
import PriceChart from '../components/charts/PriceChart';
import siteData from '../content/siteData.json';

const GLOBAL_SYMBOLS = ["GC=F", "SI=F", "^IXIC", "^GSPC", "BTC-USD"];

export default function Dashboard() {
  const navigate = useNavigate();
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState('GMEXICOB.MX');
  const [guestPlays, setGuestPlays] = useState(0);

  const bmvRankings = rankings.filter(r => !GLOBAL_SYMBOLS.includes(r.ticker));
  const globalRankings = rankings.filter(r => GLOBAL_SYMBOLS.includes(r.ticker));

  useEffect(() => {
    async function loadData() {
      try {
        const r = await rankingsApi.getRankings(15, 90);
        setRankings(r);
        
        const priceResponse = await pricesApi.getHistory(selectedTicker, null, null);
        const hist = priceResponse?.data || priceResponse;
        if (hist && hist.length > 0) {
          const last30 = hist.slice(-30);
          setChartData(last30);
        }
      } catch (e) {
        console.error('Failed to load dashboard data:', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedTicker]);

  useEffect(() => {
    try {
      const plays = parseInt(localStorage.getItem('guest_plays') || '0', 10);
      setGuestPlays(plays);
    } catch {}
  }, []);

  const texts = {
    pt: 'Market Overview',
    ps: 'Live data from the Mexican Stock Exchange',
    ml1: 'Best Score Today',
    ml2: 'Top Gainer (30d)',
    ml3: 'Top Loser (30d)',
    ml4: 'Loaded Instruments',
    ms4: '1 year of history',
    ct1: 'BMV Rankings',
    cs1: 'Score computed with weighted Min-Max - RSI, Volatility, Return, SMA-200',
    th1: 'Instrument',
    th2: 'Ret. 30d',
    th3: 'Ret. 90d',
    th4: 'Ann. Vol.',
    th5: 'Score',
    ct2: 'BMV Instruments',
    ct3: 'Global Assets (Extras)',
    gi_desc: 'Click on any instrument to view detailed analysis',
    gl1: 'Free rounds remaining',
    game_btn: 'Play now',
  };

  const getScoreColor = (score) => {
    if (score >= 70) return { bg: 'rgba(76,175,130,0.15)', color: '#4caf82' };
    if (score >= 50) return { bg: 'rgba(218,165,32,0.12)', color: '#DAA520' };
    return { bg: 'rgba(224,91,91,0.12)', color: '#e05b5b' };
  };

  const getRsiClass = (rsi) => {
    if (rsi >= 70) return 'hot';
    if (rsi <= 30) return 'cold';
    return '';
  };

  const bestScore = bmvRankings.length > 0 ? bmvRankings[0] : null;
  const topGainer = bmvRankings.length > 0 ? [...bmvRankings].sort((a, b) => (b.return_30d || 0) - (a.return_30d || 0))[0] : null;
  const topLoser = bmvRankings.length > 0 ? [...bmvRankings].sort((a, b) => (a.return_30d || 0) - (b.return_30d || 0))[0] : null;

  const handleChartTickerChange = async (ticker) => {
    setSelectedTicker(ticker);
    setLoading(true);
    try {
      const priceResponse = await pricesApi.getHistory(ticker, null, null);
      const hist = priceResponse?.data || priceResponse;
      if (hist && hist.length > 0) {
        const last30 = hist.slice(-30);
        setChartData(last30);
      }
    } catch (e) {
      console.error('Failed to load chart data:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading && rankings.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ 
            width: 40, height: 40, 
            border: '3px solid var(--border-col)', 
            borderTopColor: 'var(--arma-b)',
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem'
          }}></div>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading market data...</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-title">{texts.pt}</div>
      <div className="page-sub">{texts.ps}</div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <select 
              value={selectedTicker}
              onChange={(e) => handleChartTickerChange(e.target.value)}
              style={{
                background: 'var(--bg-card2)',
                border: '1px solid var(--border-col)',
                borderRadius: '6px',
                padding: '0.5rem 1rem',
                color: 'var(--text-main)',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              {siteData.tickers.map(ticker => (
                <option key={ticker} value={ticker}>{ticker}</option>
              ))}
            </select>
            <div className="card-title">
              {siteData.tickerNames[selectedTicker]?.en || selectedTicker}
            </div>
          </div>
        </div>
        <div style={{ padding: '0 1rem 1rem' }}>
          {loading ? (
            <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card2)', borderRadius: '10px' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading chart...</div>
            </div>
          ) : (
            <PriceChart data={chartData} height={280} />
          )}
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">{texts.ml1}</div>
          <div className="metric-val gold">{bestScore ? bestScore.score?.toFixed(1) : '-'}</div>
          <div className="metric-sub">{bestScore ? bestScore.ticker : '-'}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">{texts.ml2}</div>
          <div className="metric-val green">{topGainer && topGainer.return_30d ? `+${(topGainer.return_30d * 100).toFixed(1)}%` : '-'}</div>
          <div className="metric-sub">{topGainer ? topGainer.ticker : '-'}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">{texts.ml3}</div>
          <div className="metric-val red">{topLoser && topLoser.return_30d ? `${(topLoser.return_30d * 100).toFixed(1)}%` : '-'}</div>
          <div className="metric-sub">{topLoser ? topLoser.ticker : '-'}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">{texts.ml4}</div>
          <div className="metric-val">{bmvRankings.length}</div>
          <div className="metric-sub">{texts.ms4}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">{texts.ct1}</div>
            <div className="card-subtitle">{texts.cs1}</div>
          </div>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>{texts.th1}</th>
                <th className="right">{texts.th2}</th>
                <th className="right">{texts.th3}</th>
                <th className="right">RSI 14</th>
                <th className="right">{texts.th4}</th>
                <th className="right">{texts.th5}</th>
              </tr>
            </thead>
            <tbody>
              {bmvRankings.map(item => {
                const sc = getScoreColor(item.score);
                const fillW = Math.round(item.score * 0.8);
                const rsiClass = getRsiClass(item.rsi);
                return (
                  <tr key={item.ticker} onClick={() => navigate(`/app/ticker/${item.ticker}`)}>
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
                      <span className={`rsi-chip ${rsiClass}`}>{item.rsi ? item.rsi.toFixed(1) : '-'}</span>
                    </td>
                    <td className="right" style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      {item.annualized_volatility ? `${(item.annualized_volatility * 100).toFixed(1)}%` : '-'}
                    </td>
                    <td className="right">
                      <div className="score-bar-wrap" style={{ justifyContent: 'flex-end' }}>
                        <div className="score-bar-bg">
                          <div className="score-bar-fill" style={{ width: `${fillW}%`, background: sc.color }}></div>
                        </div>
                        <span className="score-num" style={{ color: sc.color }}>{item.score?.toFixed(0) || '0'}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {globalRankings.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">{texts.ct3}</div>
              <div className="card-subtitle">Gold, Silver, NASDAQ, S&P 500, Bitcoin</div>
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Instrument</th>
                  <th className="right">Return 30d</th>
                  <th className="right">Return 90d</th>
                  <th className="right">Ann. Vol.</th>
                  <th className="right">Score</th>
                </tr>
              </thead>
              <tbody>
                {globalRankings.map(item => {
                  const sc = getScoreColor(item.score);
                  return (
                    <tr key={item.ticker} onClick={() => navigate(`/app/ticker/${item.ticker}`)}>
                      <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{item.rank}</td>
                      <td>
                        <div className="ticker-name">{item.ticker}</div>
                        <div className="ticker-sector">{item.display_name || siteData.tickerNames[item.ticker]?.en || item.ticker}</div>
                      </td>
                      <td className="right">
                        <span className={`badge ${item.return_30d >= 0 ? 'badge-green' : 'badge-red'}`}>
                          {item.return_30d ? `${item.return_30d > 0 ? '+' : ''}${(item.return_30d * 100).toFixed(1)}%` : '-'}
                        </span>
                      </td>
                      <td className="right" style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                        {item.return_90d ? `${item.return_90d > 0 ? '+' : ''}${(item.return_90d * 100).toFixed(1)}%` : '-'}
                      </td>
                      <td className="right" style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                        {item.annualized_volatility ? `${(item.annualized_volatility * 100).toFixed(1)}%` : '-'}
                      </td>
                      <td className="right">
                        <span style={{ fontWeight: 600, color: sc.color }}>{item.score?.toFixed(0) || '0'}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid-2">
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div className="card-title">{texts.ct2}</div>
          </div>
          <div style={{ padding: '1rem 1.25rem' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>{texts.gi_desc}</div>
            {siteData.tickers.slice(0, 5).map(g => (
              <div key={g} className="global-card-item" onClick={() => navigate(`/app/ticker/${g}`)}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-main)' }}>
                    {siteData.tickerNames[g]?.en || g}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{g}</div>
                </div>
                <span className="badge badge-green" style={{ fontSize: '10px' }}>Available</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <div className="card-title">Paper Trading Simulation</div>
          </div>
          <div style={{ padding: '1rem 1.25rem' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Test your market prediction skills using historical BMV data. Make predictions based on blinded price charts.
            </div>
            <div style={{ background: 'var(--bg-card2)', borderRadius: '10px', padding: '14px', border: '0.5px solid var(--border-col)', marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>{texts.gl1}</div>
              <div className="game-rounds">
                <div className={`round-dot ${guestPlays < 1 ? 'active' : 'inactive'}`}></div>
                <div className={`round-dot ${guestPlays < 2 ? 'active' : 'inactive'}`}></div>
                <div className={`round-dot ${guestPlays < 3 ? 'active' : 'inactive'}`}></div>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>
                {3 - guestPlays} of 3 available
              </div>
            </div>
            <button className="btn-primary" style={{ width: '100%', fontSize: '13px' }} onClick={() => navigate('/game')}>
              {texts.game_btn}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
