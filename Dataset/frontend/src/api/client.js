const API_BASE = '/api'

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })
  } catch (e) {
    throw new Error('Unable to connect to server')
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    if (path === '/auth/login' && (response.status === 400 || response.status === 401)) {
      const error = new Error('Invalid username or password')
      error.status = response.status
      error.data = data
      throw error
    }

    if (response.status >= 500 && Object.keys(data).length === 0) {
      const error = new Error('Unable to connect to server')
      error.status = response.status
      error.data = data
      throw error
    }

    const detail = data.detail
    const message =
      typeof detail === 'object' && detail?.message
        ? detail.message
        : typeof detail === 'string'
          ? detail
          : 'Request failed'
    const error = new Error(message)
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export const api = {
  register: (body) => request('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  login: (body) => request('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  getStats: () => request('/stats'),
  getHealth: () => request('/health'),
  getAnalyticsTrends: () => request('/analytics/trends'),
  analyzeText: (text) => request('/analyze/text', { method: 'POST', body: JSON.stringify({ text }) }),
  analyzeYouTube: (url) => request('/analyze/youtube', { method: 'POST', body: JSON.stringify({ url }) }),
  getHistory: () => request('/history'),
  getHistoryDetail: (id) => request(`/history/${id}`),
  deleteHistory: (id) => request(`/history/${id}`, { method: 'DELETE' }),
  exportJson: (id) => `${API_BASE}/history/${id}/export/json`,
  exportTxt: (id) => `${API_BASE}/history/${id}/export/txt`,
  createReport: (body) => request('/reports', { method: 'POST', body: JSON.stringify(body) }),
  getReports: () => request('/reports'),
  getReportAnalytics: () => request('/reports/analytics'),
}

export async function downloadExport(url, filename) {
  const response = await fetch(url, { credentials: 'include' })
  if (!response.ok) throw new Error('Export failed')
  const blob = await response.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}
