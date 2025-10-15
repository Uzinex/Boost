const navButtons = () => Array.from(document.querySelectorAll('.nav-btn'));
const views = () => Array.from(document.querySelectorAll('.view'));

function formatNumber(value, options = {}) {
  const num = Number(value);
  const formatter = new Intl.NumberFormat('ru-RU', {
    maximumFractionDigits: 2,
    minimumFractionDigits: options.minimumFractionDigits ?? 0,
  });
  return formatter.format(Number.isNaN(num) ? 0 : num);
}

function formatCurrency(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return '0,00 UZT';
  const f = new Intl.NumberFormat('ru-RU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${f.format(num)} UZT`;
}

function formatDateTime(value) {
  if (!value) return '';
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
}

function composeDisplayName(user) {
  if (!user) return 'Пользователь';
  if (user.username) return `@${user.username}`;
  if (user.first_name || user.last_name) {
    return [user.first_name, user.last_name].filter(Boolean).join(' ') || 'Пользователь';
  }
  return user.telegram_id ? `ID ${user.telegram_id}` : 'Пользователь';
}

// ✅ теперь setText ВСЕГДА перезаписывает текст, даже если раньше стоял прочерк
function setText(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  if (text === undefined || text === null || text === '' || text === '—') {
    el.textContent = '0';
  } else {
    el.textContent = String(text);
  }
}

export function switchView(viewId) {
  views().forEach((view) => {
    const active = view.dataset.view === viewId;
    view.toggleAttribute('hidden', !active);
  });
  navButtons().forEach((btn) => {
    const active = btn.dataset.view === viewId;
    btn.classList.toggle('is-active', active);
  });
}

export function updateUserChip({ name, balance }) {
  setText('chip-name', name || '—');
  setText('chip-balance', formatCurrency(balance ?? 0));
}

export function renderDashboard({ balance, totalEarned, ordersCount, referralsCount, tasks, history }) {
  // 🔹 всегда преобразуем в числа
  balance = Number(balance ?? 0);
  totalEarned = Number(totalEarned ?? 0);
  ordersCount = Number(ordersCount ?? 0);
  referralsCount = Number(referralsCount ?? 0);

  // 🔹 жёстко обновляем карточки
  setText('metric-balance', formatCurrency(balance));
  setText('metric-earned', formatCurrency(totalEarned));
  setText('metric-orders', formatNumber(ordersCount));
  setText('metric-referrals', formatNumber(referralsCount));

  // остальная логика (задания и история)
  const listEl = document.getElementById('dashboard-tasks');
  const emptyEl = document.getElementById('dashboard-tasks-empty');
  if (listEl) {
    listEl.innerHTML = '';
    if (tasks && tasks.length) {
      emptyEl?.setAttribute('hidden', '');
      const tpl = document.getElementById('task-item-template');
      tasks.slice(0, 5).forEach((task) => {
        const node = tpl?.content.firstElementChild?.cloneNode(true);
        if (!node) return;
        node.dataset.taskId = task.id;
        node.querySelector('.list__title').textContent =
          task.title || task.name || `Задание #${task.id}`;
        node.querySelector('.list__meta').textContent = `${task.reward ?? task.price ?? 0} UZT • ${
          task.category || task.type || 'Задание'
        }`;
        const btn = node.querySelector('button');
        if (btn) {
          btn.textContent = 'Открыть';
          btn.dataset.action = 'open-task';
          btn.dataset.taskId = task.id;
        }
        listEl.appendChild(node);
      });
    } else emptyEl?.removeAttribute('hidden');
  }

  const histBox = document.getElementById('dashboard-history');
  const histEmpty = document.getElementById('dashboard-history-empty');
  if (histBox) {
    histBox.innerHTML = '';
    if (history && history.length) {
      histEmpty?.setAttribute('hidden', '');
      const tpl = document.getElementById('history-item-template');
      history.slice(0, 6).forEach((it) => {
        const node = tpl?.content.firstElementChild?.cloneNode(true);
        if (!node) return;
        node.querySelector('.timeline__time').textContent = formatDateTime(it.date) || '—';
        node.querySelector('.timeline__title').textContent = it.title || 'Операция';
        node.querySelector('.timeline__meta').textContent = it.meta || '';
        histBox.appendChild(node);
      });
    } else histEmpty?.removeAttribute('hidden');
  }
}

function renderList({ containerId, emptyId, items, buildItem }) {
  const listEl = containerId ? document.getElementById(containerId) : null;
  const emptyEl = emptyId ? document.getElementById(emptyId) : null;

  if (!listEl && !emptyEl) return;

  if (listEl) {
    listEl.innerHTML = '';
  }

  if (!items || !items.length) {
    emptyEl?.removeAttribute('hidden');
    return;
  }

  emptyEl?.setAttribute('hidden', '');

  if (!listEl) return;

  items.forEach((item) => {
    const node = buildItem(item);
    if (node) {
      listEl.appendChild(node);
    }
  });
}

function cloneTemplate(id, fallbackTag = 'li') {
  const tpl = document.getElementById(id);
  if (tpl?.content?.firstElementChild) {
    return tpl.content.firstElementChild.cloneNode(true);
  }
  return document.createElement(fallbackTag);
}

function fillTaskNode(node, task) {
  node.classList.add('list__item');
  const titleEl = node.querySelector('.list__title') || node.appendChild(document.createElement('p'));
  titleEl.classList.add('list__title');
  titleEl.textContent = task.title || task.name || `Задание #${task.id ?? ''}`.trim();

  const metaEl = node.querySelector('.list__meta') || node.appendChild(document.createElement('p'));
  metaEl.classList.add('list__meta');
  const metaParts = [];
  if (task.reward ?? task.price) metaParts.push(`${task.reward ?? task.price} UZT`);
  if (task.category || task.type) metaParts.push(task.category || task.type);
  if (task.status) metaParts.push(task.status);
  metaEl.textContent = metaParts.filter(Boolean).join(' • ');

  const btn = node.querySelector('button');
  if (btn) {
    btn.dataset.taskId = task.id ?? '';
    btn.dataset.action = btn.dataset.action || 'open-task';
  }
  return node;
}

export function renderTasks(tasks = []) {
  renderList({
    containerId: 'tasks-list',
    emptyId: 'tasks-empty',
    items: tasks,
    buildItem: (task) => fillTaskNode(cloneTemplate('task-item-template'), task),
  });
}

function fillHistoryNode(node, item) {
  node.classList.add('timeline__item');
  const timeEl = node.querySelector('.timeline__time') || node.appendChild(document.createElement('span'));
  timeEl.classList.add('timeline__time');
  timeEl.textContent = formatDateTime(item.date) || '—';

  const titleEl = node.querySelector('.timeline__title') || node.appendChild(document.createElement('p'));
  titleEl.classList.add('timeline__title');
  titleEl.textContent = item.title || 'Операция';

  const metaEl = node.querySelector('.timeline__meta') || node.appendChild(document.createElement('p'));
  metaEl.classList.add('timeline__meta');
  metaEl.textContent = item.meta || '';
  return node;
}

export function renderTaskHistory(history = []) {
  renderList({
    containerId: 'tasks-history',
    emptyId: 'tasks-history-empty',
    items: history,
    buildItem: (item) => fillHistoryNode(cloneTemplate('history-item-template', 'div'), item),
  });
}

export function renderOrders(orders = []) {
  renderList({
    containerId: 'orders-list',
    emptyId: 'orders-empty',
    items: orders,
    buildItem: (order) => {
      const node = cloneTemplate('order-item-template');
      node.classList.add('list__item');
      const title = node.querySelector('.list__title') || node.appendChild(document.createElement('p'));
      title.classList.add('list__title');
      title.textContent = order.title || order.name || `Заказ #${order.id ?? ''}`.trim();

      const meta = node.querySelector('.list__meta') || node.appendChild(document.createElement('p'));
      meta.classList.add('list__meta');
      const parts = [];
      if (order.status) parts.push(order.status);
      if (typeof order.progress === 'number') parts.push(`${order.progress}%`);
      if (order.budget ?? order.amount) parts.push(`${order.budget ?? order.amount} UZT`);
      meta.textContent = parts.filter(Boolean).join(' • ');
      return node;
    },
  });
}

export function renderPayments(payments = []) {
  renderList({
    containerId: 'payments-list',
    emptyId: 'payments-empty',
    items: payments,
    buildItem: (payment) => {
      const node = cloneTemplate('payment-item-template');
      node.classList.add('list__item');
      const title = node.querySelector('.list__title') || node.appendChild(document.createElement('p'));
      title.classList.add('list__title');
      title.textContent = payment.title || payment.method || payment.type || 'Пополнение';

      const meta = node.querySelector('.list__meta') || node.appendChild(document.createElement('p'));
      meta.classList.add('list__meta');
      const parts = [];
      if (payment.amount_uzt ?? payment.amount) parts.push(`${payment.amount_uzt ?? payment.amount} UZT`);
      if (payment.status) parts.push(payment.status);
      if (payment.created_at) parts.push(formatDateTime(payment.created_at));
      meta.textContent = parts.filter(Boolean).join(' • ');
      return node;
    },
  });
}

export function renderProfileSummary(profile = {}, { balance, totalEarned } = {}) {
  const name = profile.username || composeDisplayName(profile);
  setText('profile-summary-name', name);
  setText('profile-summary-balance', formatCurrency(balance ?? profile.balance ?? 0));
  setText('profile-summary-earned', formatCurrency(totalEarned ?? profile.total_earned_uzt ?? 0));
  setText('profile-summary-language', profile.language || profile.language_code || 'ru');
}

export function populateProfileForm(profile = {}) {
  const usernameInput = document.querySelector('input[name="username"], #profile-username');
  if (usernameInput) {
    usernameInput.value = profile.username || '';
  }

  const languageInput = document.querySelector('select[name="language"], #profile-language');
  if (languageInput) {
    languageInput.value = profile.language || profile.language_code || languageInput.value || 'ru';
  }
}

export function renderReferrals(referrals = []) {
  renderList({
    containerId: 'referrals-list',
    emptyId: 'referrals-empty',
    items: referrals,
    buildItem: (referral) => {
      const node = cloneTemplate('referral-item-template');
      node.classList.add('list__item');
      const title = node.querySelector('.list__title') || node.appendChild(document.createElement('p'));
      title.classList.add('list__title');
      title.textContent = referral.username || composeDisplayName(referral);

      const meta = node.querySelector('.list__meta') || node.appendChild(document.createElement('p'));
      meta.classList.add('list__meta');
      const parts = [];
      if (referral.joined_at) parts.push(formatDateTime(referral.joined_at));
      if (referral.earnings) parts.push(`${referral.earnings} UZT`);
      meta.textContent = parts.filter(Boolean).join(' • ');
      return node;
    },
  });
}

export function showToast({ title, message, type = 'info', duration = 3600 }) {
  const c = document.querySelector('.toast-container');
  if (!c) return () => {};
  const t = document.createElement('div');
  t.className = `toast toast--${type}`;
  if (title) {
    const p = document.createElement('p');
    p.className = 'toast__title';
    p.textContent = title;
    t.appendChild(p);
  }
  if (message) {
    const m = document.createElement('p');
    m.className = 'toast__message';
    m.textContent = message;
    t.appendChild(m);
  }
  c.appendChild(t);
  const timer = setTimeout(() => t.remove(), duration);
  return () => {
    clearTimeout(timer);
    t.remove();
  };
}

export function applyThemeFromTelegram(params = {}, scheme = 'light') {
  const root = document.documentElement;
  root.dataset.theme = scheme;
  Object.entries(params).forEach(([k, v]) => {
    const cssVar = `--tg-${k.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)}`;
    root.style.setProperty(cssVar, v);
  });
}

export function setLoading(sel, flag) {
  const el = typeof sel === 'string' ? document.querySelector(sel) : sel;
  if (el) el.toggleAttribute('disabled', !!flag);
}
