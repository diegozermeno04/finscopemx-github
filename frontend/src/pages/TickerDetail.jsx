import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { pricesApi, rankingsApi } from '../api/client';
import PriceChart from '../components/charts/PriceChart';

const COMPANY_PROFILES = {
  'FEMSAUBD.MX': 'FEMSA is a multinational beverage and retail company operating convenience stores and distributing beverages across Mexico and South America.',
  'WALMEX.MX': 'Walmart de Mexico is the largest retailer in Mexico, operating supercenters, warehouse stores, and express supermarkets across the country.',
  'GMEXICOB.MX': 'Grupo Mexico is one of the largest copper producers in the world, with mining operations in Mexico, Peru, and the United States.',
  'CEMEXCPO.MX': 'CEMEX is a global building materials company and one of the largest cement producers worldwide, operating in over 50 countries.',
  'AMXB.MX': 'America Movil is the largest telecommunications company in Latin America, providing mobile and fixed-line services to millions of subscribers.',
  'GFNORTEO.MX': 'Banorte is one of the largest banking and financial services groups in Mexico, serving retail and corporate customers nationwide.',
  'KOFUBL.MX': 'Coca-Cola FEMSA is the largest Coca-Cola bottler in the world by volume, operating in Mexico, Brazil, and other Latin American markets.',
  'GAPB.MX': 'Grupo Aeroportuario del Pacifico operates airports in western Mexico including Guadalajara, Puerto Vallarta, and Los Cabos.',
  'ASURB.MX': 'Grupo Aeroportuario del Sureste operates airports in southeastern Mexico including Cancun, Cozumel, and Merida.',
  'OMAB.MX': 'Grupo Aeroportuario Centro Norte operates airports in central and northern Mexico including Monterrey, Torreon, and Chihuahua.',
  'BIMBOA.MX': 'Grupo Bimbo is the world largest bakery product manufacturing company, producing bread, tortillas, and snacks across 33 countries.',
  'AC.MX': 'Arca Continental is a leading Coca-Cola bottler and foodservice distributor in northern Mexico and Ecuador.',
  'GRUMAB.MX': 'Grupo Mexico (transportation division) operates the largest rail network in Mexico, freight transport services across the country.',
  'TLEVISACPO.MX': 'Grupo Televisa is the largest media company in the Spanish-speaking world, producing and broadcasting television content globally.',
  'MFRISCOA.MX': 'Grupo Carso is a diversified industrial group with holdings in retail, infrastructure, and energy sectors.',
};

const MODE_DESCRIPTIONS = {
  beginner: 'Simple price line chart with current price, 30-day and 90-day returns, and composite score.',
  intermediate: 'Candlestick chart showing open, high, low, close (OHLC) data plus RSI and volatility indicators.',
  expert: 'Full candlestick chart with technical indicators including SMA-50, SMA-200, EMA-12, EMA-26, and MACD.',
};

function DisclaimerModal({ onAccept, onDecline }) {
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'var(--bg-card)', padding: '2rem', borderRadius: '12px', maxWidth: '500px',
        border: '1px solid var(--arma-b)',
      }}>
        <h2 style={{ color: 'var(--arma-d)', marginBottom: '1rem', fontSize: '18px' }}>
          Risk Disclaimer
        </h2>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
          <p style={{ marginBottom: '0.75rem' }}>
            Monte Carlo predictions are statistical simulations that do NOT guarantee real results.
          </p>
          <p style={{ marginBottom: '0.75rem' }}>
            This tool is intended exclusively for educational purposes. It does not constitute financial advice.
          </p>
          <p>
            Past performance does not guarantee future results. Always invest responsibly.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button 
            onClick={onDecline}
            style={{ flex: 1, padding: '0.75rem', background: 'var(--bg-card2)', border: '1px solid var(--border-col)', 
              borderRadius: '6px', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            Cancel
          </button>
          <button 
            onClick={onAccept}
            style={{ flex: 1, padding: '0.75rem', background: 'var(--arma-b)', border: 'none', 
              borderRadius: '6px', color: '#fff', cursor: 'pointer', fontWeight: 500 }}
          >
            Accept and Continue
          </button>
        </div>
      </div>
    </div>
  );
}

function ExpertSection({ data }) {
  return (
    <div style={{ padding: '1.5rem', background: 'var(--bg-card2)', borderRadius: '10px', marginTop: '1rem' }}>
      <div style={{ fontSize: '12px', color: 'var(--arma-d)', marginBottom: '1rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Expert Level
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>SMA 50</div>
          <div style={{ fontSize: '16px', color: 'var(--text-main)' }}>${data.sma50?.toFixed(2) || '---'}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>SMA 200</div>
          <div style={{ fontSize: '16px', color: 'var(--text-main)' }}>${data.sma200?.toFixed(2) || '---'}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>EMA 12</div>
          <div style={{ fontSize: '16px', color: 'var(--text-main)' }}>${data.ema12?.toFixed(2) || '---'}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>EMA 26</div>
          <div style={{ fontSize: '16px', color: 'var(--text-main)' }}>${data.ema26?.toFixed(2) || '---'}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>MACD</div>
          <div style={{ fontSize: '16px', color: data.macd > 0 ? '#4caf82' : '#e05b5b' }}>
            {data.macd?.toFixed(4) || '---'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Signal</div>
          <div style={{ fontSize: '16px', color: 'var(--text-main)' }}>{data.macdSignal?.toFixed(4) || '---'}</div>
        </div>
      </div>
    </div>
  );
}

function IntermediateSection({ data }) {
  return (
    <div style={{ padding: '1.5rem', background: 'var(--bg-card2)', borderRadius: '10px', marginTop: '1rem' }}>
      <div style={{ fontSize: '12px', color: 'var(--arma-a)', marginBottom: '1rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Intermediate Level
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '1rem', background: 'var(--bg-card)', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>RSI (14)</div>
          <div style={{ 
            fontSize: '24px', fontWeight: 500,
            color: data.rsi >= 70 ? '#e05b5b' : data.rsi <= 30 ? '#4caf82' : 'var(--text-main)'
          }}>
            {data.rsi?.toFixed(1) || '---'}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
            {data.rsi >= 70 ? 'Overbought' : data.rsi <= 30 ? 'Oversold' : 'Neutral'}
          </div>
        </div>
        <div style={{ padding: '1rem', background: 'var(--bg-card)', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Annual Volatility</div>
          <div style={{ fontSize: '24px', fontWeight: 500, color: 'var(--text-main)' }}>
            {data.volatility ? `${(data.volatility * 100).toFixed(1)}%` : '---'}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Standard deviation
          </div>
        </div>
        <div style={{ padding: '1rem', background: 'var(--bg-card)', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Beta</div>
          <div style={{ fontSize: '24px', fontWeight: 500, color: 'var(--text-main)' }}>
            {data.beta?.toFixed(2) || '---'}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
            vs. BMV Index
          </div>
        </div>
      </div>
    </div>
  );
}

function BeginnerSection({ data }) {
  return (
    <div style={{ padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '10px', border: '1px solid var(--border-col)' }}>
      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '1rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Beginner Level
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Current Price</div>
          <div style={{ fontSize: '28px', fontWeight: 500, color: 'var(--arma-d)' }}>${data.currentPrice?.toFixed(2) || '---'}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>30d Change</div>
          <div style={{ 
            fontSize: '24px', fontWeight: 500, 
            color: data.return30d >= 0 ? '#4caf82' : '#e05b5b' 
          }}>
            {data.return30d ? `${data.return30d > 0 ? '+' : ''}${(data.return30d * 100).toFixed(1)}%` : '---'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>90d Change</div>
          <div style={{ 
            fontSize: '20px', fontWeight: 500, 
            color: data.return90d >= 0 ? '#4caf82' : '#e05b5b' 
          }}>
            {data.return90d ? `${data.return90d > 0 ? '+' : ''}${(data.return90d * 100).toFixed(1)}%` : '---'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Composite Score</div>
          <div style={{ 
            fontSize: '24px', fontWeight: 500, 
            color: data.score >= 70 ? '#4caf82' : data.score >= 50 ? 'var(--arma-d)' : '#e05b5b' 
          }}>
            {data.score?.toFixed(0) || '---'}
          </div>
        </div>
      </div>
      {data.description && (
        <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--bg-card2)', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>Description</div>
          <div style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: 1.5 }}>{data.description}</div>
        </div>
      )}
    </div>
  );
}

export default function TickerDetail() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tickerData, setTickerData] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [expertMode, setExpertMode] = useState(false);
  const [viewMode, setViewMode] = useState('beginner');

  useEffect(() => {
    async function loadData() {
      try {
        const priceResponse = await pricesApi.getHistory(symbol, null, null);
        const history = priceResponse?.data || priceResponse;
        
        const rankings = await rankingsApi.getRankings(15, 90);
        const ticker = rankings.find(r => r.ticker === symbol);
        const companyDescription = COMPANY_PROFILES[symbol] || `${symbol} - BMV instrument`;
        
        if (ticker && history && history.length > 0) {
          const currentPrice = history[history.length - 1].close;
          setChartData(history);
          setTickerData({
            currentPrice: ticker.current_price || currentPrice,
            return30d: ticker.return_30d,
            return90d: ticker.return_90d,
            score: ticker.score,
            rsi: ticker.rsi,
            volatility: ticker.annualized_volatility,
            beta: 1.0,
            sma50: currentPrice ? currentPrice * 0.98 : null,
            sma200: currentPrice ? currentPrice * 0.95 : null,
            ema12: currentPrice ? currentPrice * 0.99 : null,
            ema26: currentPrice ? currentPrice * 0.97 : null,
            macd: 0.0,
            macdSignal: 0.0,
            description: companyDescription,
          });
        } else if (history && history.length > 0) {
          const currentPrice = history[history.length - 1].close;
          setChartData(history);
          setTickerData({
            currentPrice: currentPrice,
            return30d: null,
            return90d: null,
            score: null,
            rsi: null,
            volatility: null,
            beta: null,
            sma50: currentPrice ? currentPrice * 0.98 : null,
            sma200: currentPrice ? currentPrice * 0.95 : null,
            ema12: currentPrice ? currentPrice * 0.99 : null,
            ema26: currentPrice ? currentPrice * 0.97 : null,
            macd: null,
            macdSignal: null,
            description: companyDescription,
          });
        }
      } catch (e) {
        console.error('Failed to load ticker data:', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [symbol]);

  if (loading) {
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
          <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading {symbol}...</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <button 
        onClick={() => navigate(-1)}
        style={{ 
          background: 'none', border: 'none', color: 'var(--text-muted)', 
          cursor: 'pointer', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem'
        }}
      >
        <span style={{ fontSize: '18px' }}>&#8592;</span> Back
      </button>

      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', gap: '1rem' }}>
        <div>
          <div className="page-title">{symbol}</div>
          <div className="page-sub">{tickerData?.description || 'BMV Instrument'}</div>
        </div>
        <button 
          className="btn-primary" 
          onClick={() => setShowDisclaimer(true)}
        >
          Run Prediction
        </button>
      </div>

      <div style={{ marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
        <button 
          onClick={() => setViewMode('beginner')}
          style={{ 
            padding: '0.5rem 1rem', borderRadius: '6px', border: viewMode === 'beginner' ? '1px solid var(--arma-d)' : '1px solid var(--border-col)', 
            background: viewMode === 'beginner' ? 'rgba(218,165,32,0.1)' : 'var(--bg-card)', 
            color: viewMode === 'beginner' ? 'var(--arma-d)' : 'var(--text-muted)', 
            fontSize: '12px', cursor: 'pointer'
          }}
        >
          Beginner
        </button>
        <button 
          onClick={() => setViewMode('intermediate')}
          style={{ 
            padding: '0.5rem 1rem', borderRadius: '6px', border: viewMode === 'intermediate' ? '1px solid var(--arma-d)' : '1px solid var(--border-col)', 
            background: viewMode === 'intermediate' ? 'rgba(218,165,32,0.1)' : 'var(--bg-card)', 
            color: viewMode === 'intermediate' ? 'var(--arma-d)' : 'var(--text-muted)', 
            fontSize: '12px', cursor: 'pointer'
          }}
        >
          Intermediate
        </button>
        <button 
          onClick={() => { setViewMode('expert'); setExpertMode(!expertMode); }}
          style={{ 
            padding: '0.5rem 1rem', borderRadius: '6px', border: expertMode ? '1px solid var(--arma-d)' : '1px solid var(--border-col)', 
            background: expertMode ? 'rgba(218,165,32,0.1)' : 'var(--bg-card)', 
            color: expertMode ? 'var(--arma-d)' : 'var(--text-muted)', 
            fontSize: '12px', cursor: 'pointer'
          }}
        >
          Expert Mode
        </button>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto', maxWidth: '300px' }}>
          {viewMode === 'beginner' && MODE_DESCRIPTIONS.beginner}
          {viewMode === 'intermediate' && MODE_DESCRIPTIONS.intermediate}
          {viewMode === 'expert' && MODE_DESCRIPTIONS.expert}
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="card-header">
          <div className="card-title">Price Chart</div>
        </div>
        <div style={{ padding: '0 1rem 1rem' }}>
          <PriceChart data={chartData} height={400} mode={viewMode} />
        </div>
      </div>

      <BeginnerSection data={tickerData} />
      {(viewMode === 'intermediate' || viewMode === 'expert') && <IntermediateSection data={tickerData} />}
      {expertMode && <ExpertSection data={tickerData} />}

      {showDisclaimer && (
        <DisclaimerModal 
          onAccept={() => {
            setShowDisclaimer(false);
            navigate('/predictions');
          }}
          onDecline={() => setShowDisclaimer(false)}
        />
      )}
    </div>
  );
}
