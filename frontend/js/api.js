/**
 * API fetch wrapper with JWT auth and loading indicator.
 */
const API_BASE = '';

let loadingCount = 0;

function showLoading() {
  loadingCount++;
  const el = document.getElementById('loading-overlay');
  if (el) el.classList.add('active');
}

function hideLoading() {
  loadingCount = Math.max(0, loadingCount - 1);
  if (loadingCount === 0) {
    const el = document.getElementById('loading-overlay');
    if (el) el.classList.remove('active');
  }
}

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  showLoading();
  try {
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (res.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/index.html';
      throw new Error('Unauthorized');
    }
    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }
    if (!res.ok) {
      const msg = data?.detail || (typeof data === 'string' ? data : 'Request failed');
      throw new Error(Array.isArray(msg) ? msg.map((e) => e.msg || e).join(', ') : msg);
    }
    return data;
  } finally {
    hideLoading();
  }
}
