const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

function getHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  return headers;
}

async function fetchWithAuth(url, options = {}) {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    credentials: 'include',
    headers: { ...getHeaders(), ...options.headers },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
}

export const authApi = {
  login: (username, password) =>
    fetchWithAuth('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  register: (username, password) =>
    fetchWithAuth('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => fetchWithAuth('/auth/me'),
  updateMe: (data) =>
    fetchWithAuth('/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  logout: () => fetchWithAuth('/auth/logout', { method: 'POST' }),
};

export const pricesApi = {
  listTickers: () => fetchWithAuth('/prices/tickers'),
  getHistory: (ticker, startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return fetchWithAuth(`/prices/${ticker}${params.toString() ? '?' + params : ''}`);
  },
  listExtendedTickers: (category) => {
    const params = category ? `?category=${category}` : '';
    return fetchWithAuth(`/prices/extended/tickers${params}`);
  },
  getExtendedHistory: (symbol, startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return fetchWithAuth(`/prices/extended/${symbol}${params.toString() ? '?' + params : ''}`);
  },
  requestExtended: (symbol, years) => 
    fetchWithAuth('/prices/extended/request', {
      method: 'POST',
      body: JSON.stringify({ symbol, requested_years: years }),
    }),
};

export const rankingsApi = {
  getRankings: (limit = 10, days = 90) => 
    fetchWithAuth(`/rankings?limit=${limit}&days=${days}`),
};

export const predictionsApi = {
  run: (ticker, horizonDays) => 
    fetchWithAuth('/predictions/run', {
      method: 'POST',
      body: JSON.stringify({ ticker, horizon_days: horizonDays }),
    }),
  history: (limit = 10) => fetchWithAuth(`/predictions/history?limit=${limit}`),
};

export const simulationApi = {
  create: (ticker, action, amount, entryPrice, rationale) =>
    fetchWithAuth('/simulation', {
      method: 'POST',
      body: JSON.stringify({
        ticker,
        action,
        hypothetical_amount_mxn: amount,
        entry_price: entryPrice,
        rationale,
      }),
    }),
  close: (id, exitPrice) =>
    fetchWithAuth(`/simulation/${id}/close`, {
      method: 'POST',
      body: JSON.stringify({ exit_price: exitPrice }),
    }),
  list: () => fetchWithAuth('/simulation'),
  getScore: () => fetchWithAuth('/simulation/score'),
};

export const gameApi = {
  start: () => fetchWithAuth('/game/start', { method: 'POST' }),
  submit: (sessionId, points) =>
    fetchWithAuth('/game/submit', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        prediction_points: points,
      }),
    }),
  leaderboard: (limit = 10) => fetchWithAuth(`/game/leaderboard?limit=${limit}`),
  educational: (ticker) => fetchWithAuth(`/game/educational/${ticker}`),
  recordSimulation: (simulationData) =>
    fetchWithAuth('/game/record-simulation', {
      method: 'POST',
      body: JSON.stringify(simulationData),
    }),
};

export const adminApi = {
  listUsers: (limit = 50, offset = 0) =>
    fetchWithAuth(`/admin/users?limit=${limit}&offset=${offset}`),
  updateRole: (userId, role) =>
    fetchWithAuth(`/admin/users/${userId}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ role }),
    }),
  listEtlRuns: (limit = 20) => fetchWithAuth(`/admin/etl/runs?limit=${limit}`),
  triggerEtl: (runType = 'manual', years = 20) =>
    fetchWithAuth(`/admin/etl/trigger?run_type=${runType}&years=${years}`, {
      method: 'POST',
    }),
};
