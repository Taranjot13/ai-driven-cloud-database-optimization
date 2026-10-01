const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

async function handleRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const contentType = response.headers.get('content-type') || '';
    let message = 'The server request failed.';

    if (contentType.includes('application/json')) {
      const payload = await response.json();
      message = payload?.detail || payload?.message || message;
    } else {
      message = await response.text();
    }

    throw new Error(message || 'Request failed');
  }

  return response.status === 204 ? null : response.json();
}

export const api = {
  health: () => handleRequest('/health'),
  dashboard: () => handleRequest('/dashboard'),
  performance: ({ limit = 500, slowOnly = false, search = '' } = {}) => {
    const params = new URLSearchParams({ limit: String(limit), slow_only: String(slowOnly) });
    if (search) params.set('search', search);
    return handleRequest(`/performance?${params.toString()}`);
  },
  performanceSummary: () => handleRequest('/performance/summary'),
  slowQueries: () => handleRequest('/slow-queries'),
  anomalies: () => handleRequest('/anomalies'),
  predictions: () => handleRequest('/predictions'),
  optimizationHistory: ({ limit = 500 } = {}) => handleRequest(`/optimization/history?limit=${limit}`),
  optimizationSummary: () => handleRequest('/optimization/summary'),
  analyzeOptimization: (metricId) => handleRequest('/optimization/analyze', {
    method: 'POST',
    body: JSON.stringify({ metric_id: metricId }),
  }),
  executeOptimization: ({ metricId, expectedAction, confirmed = true }) => handleRequest('/optimization/execute', {
    method: 'POST',
    body: JSON.stringify({
      metric_id: metricId,
      expected_action: expectedAction,
      confirmed,
    }),
  }),
  resources: () => handleRequest('/resources'),
  costs: () => handleRequest('/costs'),
  systemStatus: () => handleRequest('/system/status'),
};
