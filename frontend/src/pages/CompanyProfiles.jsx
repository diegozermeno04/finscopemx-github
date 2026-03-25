import { useNavigate } from 'react-router-dom';
import { COMPANY_PROFILES } from '../content/companyProfiles';

export default function CompanyProfiles() {
  const navigate = useNavigate();
  
  const tickers = Object.keys(COMPANY_PROFILES);
  
  return (
    <div>
      <div className="page-title">Company Profiles</div>
      <div className="page-sub">Learn about the major companies listed on the Mexican Stock Exchange</div>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
        gap: '1rem',
        marginTop: '1.5rem'
      }}>
        {tickers.map(ticker => {
          const profile = COMPANY_PROFILES[ticker];
          return (
            <div 
              key={ticker}
              className="card"
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/app/ticker/${ticker}`)}
            >
              <div style={{ padding: '1rem' }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'flex-start',
                  marginBottom: '0.75rem'
                }}>
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--arma-d)' }}>
                      {profile.name}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {ticker}
                    </div>
                  </div>
                  <span className="badge badge-green" style={{ fontSize: '10px' }}>BMV</span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                  {profile.description}
                </div>
                <div style={{ 
                  marginTop: '1rem', 
                  paddingTop: '0.75rem', 
                  borderTop: '0.5px solid var(--border-col)',
                  fontSize: '11px',
                  color: 'var(--arma-d)'
                }}>
                  Click to view analysis
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}