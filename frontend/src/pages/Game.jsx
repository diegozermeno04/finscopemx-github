import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts';
import { pricesApi, gameApi as apiGameApi } from '../api/client';
import siteData from '../content/siteData.json';

function BlindedChart({ 
  data, 
  showActual, 
  actualData,
  height = 300 
}) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !data || data.length === 0) return;

    if (chartRef.current) {
      try {
        chartRef.current.remove();
      } catch (e) {
        console.warn('Failed to remove chart:', e);
      }
      chartRef.current = null;
    }

    try {
      const chart = createChart(containerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#8a8fa8',
        },
        grid: {
          vertLines: { color: 'rgba(255,255,255,0.05)' },
          horzLines: { color: 'rgba(255,255,255,0.05)' },
        },
        width: containerRef.current.clientWidth,
        height: height,
        timeScale: {
          timeVisible: false,
          secondsVisible: false,
        },
        rightPriceScale: {
          borderColor: 'rgba(255,255,255,0.08)',
        },
        crosshair: {
          mode: CrosshairMode.Normal,
        },
      });

      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#8FBC8F',
        downColor: '#e05b5b',
        borderUpColor: '#8FBC8F',
        borderDownColor: '#e05b5b',
        wickUpColor: '#8FBC8F',
        wickDownColor: '#e05b5b',
      });

      const chartData = data
        .filter(d => d && d.close != null && !isNaN(d.close))
        .map((d, i) => ({
          time: i + 1,
          open: (d.open != null && !isNaN(d.open)) ? d.open : d.close,
          high: (d.high != null && !isNaN(d.high)) ? d.high : d.close,
          low: (d.low != null && !isNaN(d.low)) ? d.low : d.close,
          close: d.close,
        }));

      if (chartData.length === 0) {
        console.warn('No valid data for blinded chart');
        chart.remove();
        return;
      }

      candlestickSeries.setData(chartData);
      chart.timeScale().fitContent();

      chartRef.current = chart;

      const handleResize = () => {
        if (containerRef.current && chartRef.current) {
          try {
            chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
          } catch (e) {
            console.warn('Failed to resize chart:', e);
          }
        }
      };
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartRef.current) {
          try {
            chartRef.current.remove();
          } catch (e) {
            console.warn('Failed to remove chart on cleanup:', e);
          }
          chartRef.current = null;
        }
      };
    } catch (e) {
      console.error('Failed to create blinded chart:', e);
    }
  }, [data, showActual, actualData, height]);

  return (
    <div ref={containerRef} style={{ width: '100%', height }} />
  );
}

function ResultOverlay({ result, onPlayAgain, onClose }) {
  const isWin = result.direction_matched;
  
  return (
    <div style={{
      position: 'absolute',
      top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: '10px',
      zIndex: 100,
    }}>
      <div style={{
        background: 'var(--bg-card)',
        padding: '2rem',
        borderRadius: '12px',
        maxWidth: '400px',
        textAlign: 'center',
        border: isWin ? '1px solid #4caf82' : '1px solid #e05b5b',
      }}>
        <div style={{ fontSize: '32px', marginBottom: '1rem', fontWeight: 600 }}>
          {isWin ? 'You Won!' : 'You Lost'}
        </div>
        
        <div style={{ fontSize: '48px', fontWeight: 500, color: isWin ? '#4caf82' : '#e05b5b', marginBottom: '1rem' }}>
          {result.total_score}
        </div>
        
        <div style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          {result.direction_matched 
            ? 'Your prediction was correct!'
            : 'The market moved in the opposite direction.'}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ background: 'var(--bg-card2)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Your Prediction</div>
            <div style={{ fontSize: '18px', color: result.predicted_direction === 'up' ? '#4caf82' : '#e05b5b', fontWeight: 600 }}>
              {result.predicted_direction === 'up' ? 'UP' : 'DOWN'}
            </div>
          </div>
          <div style={{ background: 'var(--bg-card2)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Actual Result</div>
            <div style={{ fontSize: '18px', color: '#4caf82', fontWeight: 600 }}>
              {result.actual_direction === 'up' ? 'UP' : 'DOWN'}
            </div>
          </div>
        </div>

        <div style={{ background: 'var(--bg-card2)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', textAlign: 'left' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            <div style={{ marginBottom: '0.5rem' }}>
              <span style={{ color: 'var(--arma-d)' }}>Start Price:</span> ${result.start_price.toFixed(2)}
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              <span style={{ color: 'var(--arma-d)' }}>End Price:</span> ${result.end_price.toFixed(2)}
            </div>
            <div>
              <span style={{ color: 'var(--arma-d)' }}>Price Change:</span>{' '}
              <span style={{ color: result.actual_change >= 0 ? '#4caf82' : '#e05b5b' }}>
                {result.actual_change >= 0 ? '+' : ''}{result.actual_change.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        <button className="btn-primary" onClick={onPlayAgain} style={{ width: '100%', marginBottom: '0.5rem' }}>
          Play Again
        </button>
        <button 
          className="btn-secondary" 
          onClick={onClose} 
          style={{ width: '100%', fontSize: '12px' }}
        >
          View Leaderboard
        </button>
      </div>
    </div>
  );
}

function Legend({ showActual }) {
  return (
    <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem', fontSize: '11px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <div style={{ width: 8, height: 8, background: '#8FBC8F', borderRadius: '2px' }}></div>
        <span style={{ color: 'var(--text-muted)' }}>Historical (Blinded)</span>
      </div>
      {showActual && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: 8, height: 2, background: '#4caf82', borderStyle: 'dashed' }}></div>
          <span style={{ color: 'var(--text-muted)' }}>Actual Result</span>
        </div>
      )}
    </div>
  );
}

export default function Game() {
  const { user } = useApp();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [result, setResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [error, setError] = useState(null);

  const GUEST_PLAY_LIMIT = 3;

  const getGuestPlays = () => {
    try {
      return parseInt(localStorage.getItem('guest_plays') || '0', 10);
    } catch {
      return 0;
    }
  };

  const incrementGuestPlays = () => {
    try {
      const current = getGuestPlays();
      localStorage.setItem('guest_plays', String(current + 1));
    } catch {
      localStorage.setItem('guest_plays', '1');
    }
  };

  const canPlayAsGuest = () => {
    return getGuestPlays() < GUEST_PLAY_LIMIT;
  };

  useEffect(() => {
    async function loadLeaderboard() {
      try {
        const lb = await apiGameApi.leaderboard(10);
        setLeaderboard(lb || []);
      } catch (e) {
        console.error('Failed to load leaderboard:', e);
        setLeaderboard([]);
      }
    }
    loadLeaderboard();
  }, []);

  async function recordSimulationAsync(ticker, startDate, endDate, userPred, actualDir, isCorrect, score) {
    try {
      await apiGameApi.recordSimulation({
        ticker,
        prediction_date: new Date().toISOString().split('T')[0],
        start_date: startDate,
        end_date: endDate,
        user_prediction: userPred,
        predicted_direction: userPred,
        actual_direction: actualDir,
        is_correct: isCorrect,
        score: score,
      });
    } catch (e) {
      console.warn('Guest user: simulation not saved to DB');
    }
  }

  async function startGame() {
    if (!canPlayAsGuest()) {
      setShowLoginModal(true);
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    setPrediction(null);
    setShowResult(false);
    
    try {
      const tickers = siteData.tickers;
      const randomTicker = tickers[Math.floor(Math.random() * tickers.length)];
      
      const priceResponse = await pricesApi.getHistory(randomTicker, null, null);
      const history = priceResponse?.data || priceResponse;
      
      if (!history || !Array.isArray(history) || history.length < 90) {
        setError('Not enough historical data for this ticker');
        setLoading(false);
        return;
      }
      
      const startIndex = Math.floor(Math.random() * (history.length - 90));
      const partialData = history.slice(startIndex, startIndex + 60);
      const actualFuture = history.slice(startIndex + 55, startIndex + 90);
      
      setSession({
        session_id: 'session_' + Date.now(),
        ticker: randomTicker,
        partial_data: partialData,
        actual_future: actualFuture,
        start_date: partialData[0]?.date,
        end_date: actualFuture[actualFuture.length - 1]?.date,
      });
    } catch (e) {
      console.error('Failed to start game:', e);
      setError('Error loading game data');
    } finally {
      setLoading(false);
    }
  }

  function handlePrediction(direction) {
    if (!session) return;

    const startPrice = session.partial_data[session.partial_data.length - 1].close;
    const endPrice = session.actual_future[session.actual_future.length - 1].close;
    const actualChange = (endPrice - startPrice) / startPrice;
    const actualDirection = actualChange >= 0 ? 'up' : 'down';
    const isCorrect = direction === actualDirection;

    const baseScore = isCorrect ? 80 : 30;
    const magnitudeBonus = Math.min(Math.abs(actualChange) * 100, 20);
    const score = Math.min(baseScore + Math.round(magnitudeBonus), 100);

    const r = {
      total_score: score,
      predicted_direction: direction,
      actual_direction: actualDirection,
      direction_matched: isCorrect,
      start_price: startPrice,
      end_price: endPrice,
      actual_change: actualChange * 100,
      actual_prices: session.actual_future,
    };

    setPrediction(direction);
    setResult(r);
    setShowResult(true);
    incrementGuestPlays();

    recordSimulationAsync(
      session.ticker,
      session.start_date,
      session.end_date,
      direction,
      actualDirection,
      isCorrect,
      score
    ).then(() => {
      apiGameApi.leaderboard(10).then(lb => setLeaderboard(lb || [])).catch(() => {});
    });
  }

  function handlePlayAgain() {
    setShowResult(false);
    setResult(null);
    setPrediction(null);
    setSession(null);
    startGame();
  }

  function handleCloseResult() {
    setShowResult(false);
  }

  const texts = {
    pt: 'Paper Trading Simulation',
    ps: 'Test your market prediction skills using historical data',
    btn: 'Start Simulation',
    score: 'Score',
    playAgain: 'Play Again',
    instructions: 'Observe the last 60 days of blinded price data and predict whether the price will go up or down over the next 30 days',
    loginTitle: 'Login to Continue',
    loginMessage: 'You have used all 3 guest plays. Create an account to continue with leaderboards and persistent scores!',
    loadingData: 'Loading data...',
    predictUp: 'Predict UP (Bullish)',
    predictDown: 'Predict DOWN (Bearish)',
  };

  return (
    <div>
      <div className="page-title">{texts.pt}</div>
      <div className="page-sub">{texts.ps}</div>

      <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--bg-card2)', border: '1px solid var(--arma-d)' }}>
        <div style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--arma-d)', marginBottom: '0.75rem' }}>
            About This Simulation
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            This is a paper trading simulation - an educational tool that allows you to test hypothetical investment decisions using historical market data. You will see 60 days of blinded price history and must predict whether the price will go up or down over the next 30 days. Your predictions are compared against actual historical outcomes. No real money is involved.
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card" style={{ position: 'relative' }}>
          <div className="card-header">
            <div className="card-title">{texts.pt}</div>
            {session && (
              <div style={{ fontSize: '11px', color: 'var(--arma-d)' }}>
                {session.ticker}
              </div>
            )}
          </div>
          <div style={{ padding: '1rem' }}>
            {loading && (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <div style={{ 
                  width: 40, height: 40, 
                  border: '3px solid var(--border-col)', 
                  borderTopColor: 'var(--arma-b)',
                  borderRadius: '50%', 
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto 1rem'
                }}></div>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>{texts.loadingData}</div>
              </div>
            )}
            
            {!loading && !session && (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <div style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.6 }}>
                  {texts.instructions}
                </div>
                {error && (
                  <div style={{ fontSize: '12px', color: '#e05b5b', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(224,91,91,0.1)', borderRadius: '6px' }}>
                    {error}
                  </div>
                )}
                <button className="btn-primary" onClick={startGame} disabled={loading} style={{ width: '100%' }}>
                  {loading ? '...' : texts.btn}
                </button>
              </div>
            )}
            
            {!loading && session && (
              <div>
                <Legend showActual={showResult} />
                
                <div style={{ marginBottom: '1rem' }}>
                  <BlindedChart 
                    data={session.partial_data}
                    showActual={showResult}
                    actualData={result?.actual_prices}
                    height={320}
                  />
                </div>

                <div style={{ 
                  marginBottom: '1rem', 
                  padding: '1rem', 
                  background: 'var(--bg-card2)', 
                  borderRadius: '8px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Based on the chart above, what will happen next?
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <button 
                      onClick={() => handlePrediction('up')}
                      disabled={showResult}
                      style={{
                        padding: '1rem',
                        fontSize: '14px',
                        fontWeight: 600,
                        background: showResult && prediction === 'down' 
                          ? 'rgba(76,175,130,0.3)' 
                          : 'rgba(76,175,130,0.15)',
                        color: showResult && prediction === 'down' ? '#4caf82' : '#4caf82',
                        border: showResult && prediction === 'down' 
                          ? '2px solid #4caf82' 
                          : '2px solid rgba(76,175,130,0.3)',
                        borderRadius: '8px',
                        cursor: showResult ? 'default' : 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      {texts.predictUp}
                    </button>
                    
                    <button 
                      onClick={() => handlePrediction('down')}
                      disabled={showResult}
                      style={{
                        padding: '1rem',
                        fontSize: '14px',
                        fontWeight: 600,
                        background: showResult && prediction === 'up' 
                          ? 'rgba(224,91,91,0.3)' 
                          : 'rgba(224,91,91,0.15)',
                        color: showResult && prediction === 'up' ? '#e05b5b' : '#e05b5b',
                        border: showResult && prediction === 'up' 
                          ? '2px solid #e05b5b' 
                          : '2px solid rgba(224,91,91,0.3)',
                        borderRadius: '8px',
                        cursor: showResult ? 'default' : 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      {texts.predictDown}
                    </button>
                  </div>
                </div>

                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center' }}>
                  {3 - getGuestPlays()} of {GUEST_PLAY_LIMIT} guest plays remaining
                </div>

                {showResult && result && (
                  <ResultOverlay 
                    result={result}
                    onPlayAgain={handlePlayAgain}
                    onClose={handleCloseResult}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">Leaderboard</div>
          </div>
          <table>
            <thead><tr><th>#</th><th>User</th><th className="right">Score</th></tr></thead>
            <tbody>
              {leaderboard.length > 0 ? leaderboard.map(e => (
                <tr key={e.rank}>
                  <td>{e.rank}</td>
                  <td>{e.username}</td>
                  <td className="right" style={{ color: '#4caf82' }}>{e.total_score}</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px', padding: '2rem' }}>
                    No data available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showLoginModal && (
        <div className="detail-overlay" style={{ background: 'rgba(0,0,0,0.8)' }}>
          <div className="auth-card" style={{ maxWidth: '420px' }}>
            <div className="auth-title" style={{ fontSize: '18px' }}>{texts.loginTitle}</div>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '1.5rem', lineHeight: 1.6 }}>
              {texts.loginMessage}
            </p>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="btn-secondary" onClick={() => setShowLoginModal(false)} style={{ flex: 1 }}>
                Close
              </button>
              <button className="btn-primary" onClick={() => { setShowLoginModal(false); navigate('/login'); }} style={{ flex: 1 }}>
                Login
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
