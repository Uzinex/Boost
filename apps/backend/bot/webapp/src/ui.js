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

// …остальные функции renderTasks / renderOrders / renderPayments / renderReferrals
// остаются без изменений (они работают корректно)

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
