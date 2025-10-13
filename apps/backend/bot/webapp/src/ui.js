const navButtons = () => Array.from(document.querySelectorAll('.nav-btn'));
const views = () => Array.from(document.querySelectorAll('.view'));

function formatNumber(value, options = {}) {
  const formatter = new Intl.NumberFormat('ru-RU', {
    maximumFractionDigits: 2,
    minimumFractionDigits: options.minimumFractionDigits ?? 0,
  });
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—';
  }
  return formatter.format(Number(value));
}

function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—';
  }
  const formatter = new Intl.NumberFormat('ru-RU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${formatter.format(Number(value))} UZT`;
}

function formatDateTime(value) {
  if (!value) {
    return '';
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = text;
  }
}

export function switchView(viewId) {
  views().forEach((view) => {
    const isActive = view.dataset.view === viewId;
    view.toggleAttribute('hidden', !isActive);
  });
  navButtons().forEach((btn) => {
    const isActive = btn.dataset.view === viewId;
    btn.classList.toggle('is-active', isActive);
  });
}

export function updateUserChip({ name, balance }) {
  setText('chip-name', name || '—');
  setText('chip-balance', typeof balance === 'number' ? formatCurrency(balance) : `${balance ?? '—'} UZT`);
}

export function renderDashboard({ balance, totalEarned, ordersCount, referralsCount, tasks, history }) {
  setText('metric-balance', formatCurrency(balance));
  setText('metric-earned', formatCurrency(totalEarned));
  setText('metric-orders', formatNumber(ordersCount));
  setText('metric-referrals', formatNumber(referralsCount));

  const listEl = document.getElementById('dashboard-tasks');
  const emptyEl = document.getElementById('dashboard-tasks-empty');
  if (listEl) {
    listEl.innerHTML = '';
    if (tasks && tasks.length) {
      emptyEl?.setAttribute('hidden', '');
      const template = document.getElementById('task-item-template');
      tasks.slice(0, 5).forEach((task) => {
        const clone = template?.content.firstElementChild?.cloneNode(true);
        if (!clone) {
          return;
        }
        clone.dataset.taskId = task.id;
        clone.querySelector('.list__title').textContent = task.title || task.name || `Задание #${task.id}`;
        clone.querySelector('.list__meta').textContent = `${task.reward ?? task.price ?? 0} UZT • ${task.category || task.type || 'Задание'}`;
        const button = clone.querySelector('button');
        if (button) {
          button.textContent = 'Открыть';
          button.dataset.action = 'open-task';
          button.dataset.taskId = task.id;
        }
        listEl.appendChild(clone);
      });
    } else {
      emptyEl?.removeAttribute('hidden');
    }
  }

  const historyContainer = document.getElementById('dashboard-history');
  const historyEmpty = document.getElementById('dashboard-history-empty');
  if (historyContainer) {
    historyContainer.innerHTML = '';
    if (history && history.length) {
      historyEmpty?.setAttribute('hidden', '');
      const template = document.getElementById('history-item-template');
      history.slice(0, 6).forEach((item) => {
        const clone = template?.content.firstElementChild?.cloneNode(true);
        if (!clone) {
          return;
        }
        clone.querySelector('.timeline__time').textContent = formatDateTime(item.date) || '—';
        clone.querySelector('.timeline__title').textContent = item.title || 'Операция';
        clone.querySelector('.timeline__meta').textContent = item.meta || '';
        historyContainer.appendChild(clone);
      });
    } else {
      historyEmpty?.removeAttribute('hidden');
    }
  }
}

export function renderTasks(tasks) {
  const list = document.getElementById('tasks-list');
  const empty = document.getElementById('tasks-empty');
  if (!list) return;

  list.innerHTML = '';
  if (tasks && tasks.length) {
    empty?.setAttribute('hidden', '');
    const template = document.getElementById('task-item-template');
    tasks.forEach((task) => {
      const clone = template?.content.firstElementChild?.cloneNode(true);
      if (!clone) {
        return;
      }
      clone.dataset.taskId = task.id;
      clone.querySelector('.list__title').textContent = task.title || task.name || `Задание #${task.id}`;
      clone.querySelector('.list__meta').textContent = `${task.reward ?? task.price ?? 0} UZT • ${task.description || ''}`.trim();
      const button = clone.querySelector('button');
      if (button) {
        button.textContent = 'Выполнить';
        button.dataset.action = 'complete-task';
        button.dataset.taskId = task.id;
      }
      list.appendChild(clone);
    });
  } else {
    empty?.removeAttribute('hidden');
  }
}

export function renderTaskHistory(history) {
  const list = document.getElementById('tasks-history');
  const empty = document.getElementById('tasks-history-empty');
  if (!list) return;

  list.innerHTML = '';
  if (history && history.length) {
    empty?.setAttribute('hidden', '');
    history.forEach((item) => {
      const li = document.createElement('li');
      li.className = 'list__item list__item--neutral';
      const title = document.createElement('p');
      title.className = 'list__title';
      title.textContent = item.title || item.name || `Задание #${item.id}`;
      const meta = document.createElement('p');
      meta.className = 'list__meta';
      meta.textContent = `${formatDateTime(item.completed_at || item.created_at)} • +${item.reward ?? 0} UZT`;
      li.append(title, meta);
      list.appendChild(li);
    });
  } else {
    empty?.removeAttribute('hidden');
  }
}

export function renderOrders(orders) {
  const table = document.getElementById('orders-table');
  const empty = document.getElementById('orders-empty');
  if (!table) return;

  table.innerHTML = '';
  if (orders && orders.length) {
    empty?.setAttribute('hidden', '');
    orders.forEach((order) => {
      const row = document.createElement('div');
      row.dataset.orderId = order.id;
      row.innerHTML = `
        <span>#${order.id}</span>
        <span>${order.order_type || order.type || '—'}</span>
        <span>${order.target_url || order.link || '—'}</span>
        <span>${order.status || '—'}</span>
        <span>${order.progress ? `${order.progress}%` : `${order.completed_actions || 0}/${order.quantity || order.target_quantity || 0}`}</span>
        <span>${order.total_cost ? formatCurrency(order.total_cost) : formatCurrency(order.cost || 0)}</span>
        <span class="table__actions">
          ${order.status === 'active' || order.status === 'pending' ? `<button class="btn btn--ghost" data-action="cancel-order" data-order-id="${order.id}">Отменить</button>` : ''}
        </span>
      `;
      table.appendChild(row);
    });
  } else {
    empty?.removeAttribute('hidden');
  }
}

export function renderPayments(payments) {
  const table = document.getElementById('payments-table');
  const empty = document.getElementById('payments-empty');
  if (!table) return;

  table.innerHTML = '';
  if (payments && payments.length) {
    empty?.setAttribute('hidden', '');
    payments.forEach((payment) => {
      const row = document.createElement('div');
      row.innerHTML = `
        <span>${formatDateTime(payment.created_at || payment.updated_at)}</span>
        <span>${payment.method || payment.type || 'manual'}</span>
        <span>${formatCurrency(payment.amount_uzt ?? payment.amount ?? 0)}</span>
        <span>${payment.status || 'pending'}</span>
        <span>${payment.comment || payment.note || ''}</span>
      `;
      table.appendChild(row);
    });
  } else {
    empty?.removeAttribute('hidden');
  }
}

export function renderProfileSummary(profile, stats) {
  const summary = document.getElementById('profile-summary');
  if (!summary) return;

  const balance = stats?.balance ?? profile?.balance;
  const totalEarned = stats?.totalEarned;
  summary.innerHTML = `
    <dt>ID</dt>
    <dd>${profile?.id ?? '—'}</dd>
    <dt>Telegram</dt>
    <dd>${profile?.username ? `@${profile.username}` : profile?.first_name || '—'}</dd>
    <dt>Язык</dt>
    <dd>${profile?.language ?? 'ru'}</dd>
    <dt>Баланс</dt>
    <dd>${formatCurrency(balance ?? 0)}</dd>
    <dt>Заработано</dt>
    <dd>${formatCurrency(totalEarned ?? 0)}</dd>
  `;
}

export function populateProfileForm(profile) {
  const form = document.getElementById('profile-form');
  if (!form) return;
  const usernameInput = form.querySelector('[name="username"]');
  const languageSelect = form.querySelector('[name="language"]');
  if (usernameInput) {
    usernameInput.value = profile?.username || '';
  }
  if (languageSelect && profile?.language) {
    languageSelect.value = profile.language;
  }
}

export function renderReferrals(referrals) {
  const list = document.getElementById('referrals-list');
  const empty = document.getElementById('referrals-empty');
  if (!list) return;

  list.innerHTML = '';
  if (referrals && referrals.length) {
    empty?.setAttribute('hidden', '');
    const template = document.getElementById('referral-item-template');
    referrals.forEach((ref) => {
      const clone = template?.content.firstElementChild?.cloneNode(true);
      if (!clone) {
        return;
      }
      clone.querySelector('.list__title').textContent = ref.username ? `@${ref.username}` : ref.first_name || `Пользователь #${ref.id}`;
      const joined = formatDateTime(ref.joined_at || ref.created_at);
      clone.querySelector('.list__meta').textContent = `${joined || 'Дата неизвестна'} • ${formatCurrency(ref.total_earned ?? ref.balance ?? 0)}`;
      list.appendChild(clone);
    });
  } else {
    empty?.removeAttribute('hidden');
  }
}

export function showToast({ title, message, type = 'info', duration = 3600 }) {
  const container = document.querySelector('.toast-container');
  if (!container) {
    return () => {};
  }
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;

  if (title) {
    const titleEl = document.createElement('p');
    titleEl.className = 'toast__title';
    titleEl.textContent = title;
    toast.appendChild(titleEl);
  }

  if (message) {
    const messageEl = document.createElement('p');
    messageEl.className = 'toast__message';
    messageEl.textContent = message;
    toast.appendChild(messageEl);
  }

  container.appendChild(toast);

  const timeout = window.setTimeout(() => {
    toast.remove();
  }, duration);

  return () => {
    clearTimeout(timeout);
    toast.remove();
  };
}

export function applyThemeFromTelegram(themeParams = {}, colorScheme = 'light') {
  const root = document.documentElement;
  root.dataset.theme = colorScheme;
  Object.entries(themeParams).forEach(([key, value]) => {
    const cssVar = `--tg-${key.replace(/[A-Z]/g, (match) => `-${match.toLowerCase()}`)}`;
    root.style.setProperty(cssVar, value);
  });
}

export function setLoading(selector, isLoading) {
  const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (!element) return;
  element.toggleAttribute('disabled', Boolean(isLoading));
}
