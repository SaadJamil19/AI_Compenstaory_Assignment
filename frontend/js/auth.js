/**
 * Authentication helpers - login, logout, role checks.
 */

function getUser() {
  const raw = localStorage.getItem('user');
  return raw ? JSON.parse(raw) : null;
}

function isManager() {
  const user = getUser();
  return user && user.role === 'manager';
}

function requireAuth() {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = '/index.html';
    return false;
  }
  return true;
}

function requireRole(role) {
  const user = getUser();
  if (!user || user.role !== role) {
    return false;
  }
  return true;
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/index.html';
}

async function login(email, password) {
  const data = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data.user;
}
