/**
 * Shared UI helpers - sidebar, badges, date formatting.
 */

function renderSidebar(activePage) {
  const user = getUser();
  if (!user) return;

  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;

  const pages = [
    { href: '/dashboard.html', label: 'Dashboard', id: 'dashboard' },
    { href: '/customers.html', label: 'Customers', id: 'customers' },
    { href: '/tickets.html', label: 'Tickets', id: 'tickets' },
    { href: '/chatbot.html', label: 'AI Chatbot', id: 'chatbot' },
  ];
  if (user.role === 'manager') {
    pages.push(
      { href: '/notifications.html', label: 'Notifications', id: 'notifications' },
      { href: '/integrations.html', label: 'Integrations', id: 'integrations' },
      { href: '/reports.html', label: 'Reports', id: 'reports' },
      { href: '/users.html', label: 'Users', id: 'users' }
    );
  }

  nav.innerHTML = pages
    .map(
      (p) =>
        `<a href="${p.href}" class="${activePage === p.id ? 'active' : ''}">${p.label}</a>`
    )
    .join('');

  const badge = document.getElementById('role-badge');
  if (badge) badge.textContent = user.role;

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.onclick = logout;
}

function formatDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHTML(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function statusBadge(status) {
  const s = (status || '').replace(' ', '_');
  return `<span class="badge badge-${escapeHTML(s)}">${escapeHTML(status)}</span>`;
}

function priorityBadge(priority) {
  return `<span class="badge badge-${escapeHTML(priority)}">${escapeHTML(priority)}</span>`;
}

function sentimentBadge(sentiment) {
  return `<span class="badge badge-${escapeHTML(sentiment)}">${escapeHTML(sentiment)}</span>`;
}

function showAlert(containerId, message, type = 'error') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type}">${escapeHTML(message)}</div>`;
  setTimeout(() => { el.innerHTML = ''; }, 5000);
}
