import {
  state,
  getConfig,
  setSessionToken,
  setUser,
  setProfile,
  setStats,
  setBalance,
  setBalanceHistory,
  setTasks,
  setTaskHistory,
  setOrders,
  setPayments,
  setReferrals,
} from './state.js';
import { api, authWithTelegram, authWithMockUser, setAuthToken } from './api.js';
import {
  switchView,
  updateUserChip,
  renderDashboard,
  renderTasks,
  renderTaskHistory,
  renderOrders,
  renderPayments,
  renderProfileSummary,
  populateProfileForm,
  renderReferrals,
  showToast,
  applyThemeFromTelegram,
  setLoading,
} from './ui.js';

const tg = window.Telegram?.WebApp;

function resolveInitData() {
  if (tg?.initData) {
    return tg.initData;
  }
  const params = new URLSearchParams(window.location.search);
  const direct = params.get('init_data') || params.get('tgWebAppData') || params.get('mockInitData');
  if (direct) {
    return direct;
  }
  const configInit = getConfig().mockInitData;
  return typeof configInit === 'string' ? configInit : '';
}

function parseBooleanFlag(value) {
  if (typeof value !== 'string') {
    return false;
  }
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
}

function shouldUseMockAuth(searchParams, config) {
  if (!config) {
    return false;
  }

  const explicitMock =
    parseBooleanFlag(searchParams.get('mock')) ||
    parseBooleanFlag(searchParams.get('debug')) ||
    parseBooleanFlag(searchParams.get('useMockAuth'));

  if (explicitMock) {
    return true;
  }

  return Boolean(config.mockAuthEnabled);
}

function buildMockAuthParams(searchParams, config) {
  const baseUser = config && typeof config.mockAuthUser === 'object' ? config.mockAuthUser : {};
  const baseParams = config && typeof config.mockAuthParams === 'object' ? config.mockAuthParams : {};

  const overrides = {};
  const telegramId = searchParams.get('telegram_id') || searchParams.get('user_id');
  if (telegramId) {
    const parsedId = Number(telegramId);
    if (!Number.isNaN(parsedId)) {
      overrides.telegram_id = parsedId;
    }
  }

  if (searchParams.get('username')) {
    overrides.username = searchParams.get('username');
  }
  if (searchParams.get('first_name')) {
    overrides.first_name = searchParams.get('first_name');
  }
  if (searchParams.get('last_name')) {
    overrides.last_name = searchParams.get('last_name');
  }

  const languageOverride = searchParams.get('language_code') || searchParams.get('language');
  if (languageOverride) {
    overrides.language_code = languageOverride;
  }

  return { ...baseParams, ...baseUser, ...overrides };
}

function composeDisplayName(user) {
  if (!user) return 'Пользователь';
  if (user.username) return `@${user.username}`;
  if (user.first_name || user.last_name) {
    return [user.first_name, user.last_name].filter(Boolean).join(' ');
  }
  return `ID ${user.telegram_id || user.id}`;
}

function buildHistoryEvents() {
  const events = [];
  state.payments.forEach((payment) => {
    events.push({
      date: payment.created_at || payment.updated_at,
      title: payment.status === 'completed' ? 'Пополнение зачислено' : 'Заявка на пополнение',
      meta: `${payment.method || payment.type || 'manual'} • ${payment.status || 'pending'} • ${payment.amount_uzt ?? payment.amount ?? 0} UZT`,
    });
  });

  state.balanceHistory.forEach((entry) => {
    events.push({
      date: entry.created_at || entry.timestamp,
      title: entry.type === 'credit' ? 'Начисление' : 'Списание',
      meta: `${entry.description || ''} • ${entry.amount ? `${entry.amount} UZT` : ''}`.trim(),
    });
  });

  return events
    .filter((item) => item.date)
    .sort((a, b) => new Date(b.date) - new Date(a.date));
}

async function bootstrap() {
  try {
    if (tg) {
      tg.ready();
      tg.expand();
      applyThemeFromTelegram(tg.themeParams || {}, tg.colorScheme || 'light');
      tg.onEvent('themeChanged', (params) => {
        applyThemeFromTelegram(params.theme_params || {}, params.color_scheme || 'light');
      });
    }

    const searchParams = new URLSearchParams(window.location.search);
    const config = getConfig();
    const initData = resolveInitData();
    const useMockAuth = !initData && shouldUseMockAuth(searchParams, config);
    const overrideBotToken = searchParams.get('bot_token') || searchParams.get('botToken') || undefined;

    if (!initData && !useMockAuth) {
      showToast({
        type: 'warning',
        title: 'Нужен initData',
        message: 'Приложение должно запускаться из Telegram WebApp или с тестовым init_data.',
        duration: 6000,
      });
      return;
    }

    const authPayload = initData
      ? await authWithTelegram(initData, overrideBotToken)
      : await authWithMockUser(buildMockAuthParams(searchParams, config));

    const userSnapshot = authPayload.user || {};
    setSessionToken(authPayload.session_token);
    setAuthToken(authPayload.session_token);
    setUser(userSnapshot);
    updateUserChip({ name: composeDisplayName(userSnapshot), balance: userSnapshot.balance });

    await loadInitialData();
    bindEvents();
    switchView('dashboard');

    if (useMockAuth) {
      showToast({
        type: 'info',
        title: 'Демо-режим',
        message: 'Используется тестовый Telegram-профиль (mock auth).',
        duration: 5000,
      });
    }
  } catch (error) {
    console.error(error);
    showToast({ type: 'error', title: 'Ошибка', message: error.message || 'Не удалось запустить WebApp' });
  }
}

async function loadInitialData() {
  try {
    const [profileResp, userStatsResp, publicStatsResp, balanceResp, balanceHistoryResp, tasksResp, taskHistoryResp, ordersResp, paymentsResp, referralsResp] =
      await Promise.all([
        api.fetchProfile().catch(() => null),
        api.fetchUserStats().catch(() => null),
        api.fetchPublicStats().catch(() => null),
        api.fetchBalance().catch(() => null),
        api.fetchBalanceHistory().catch(() => []),
        api.fetchTasks().catch(() => []),
        api.fetchTaskHistory().catch(() => []),
        api.fetchOrders().catch(() => []),
        api.fetchPaymentsHistory().catch(() => []),
        api.fetchReferrals().catch(() => ({ referrals: [] })),
      ]);

    const profile = profileResp?.user || null;
    setProfile(profile);
    setBalance(balanceResp?.balance ?? profile?.balance ?? null);
    setBalanceHistory(Array.isArray(balanceHistoryResp) ? balanceHistoryResp : []);
    setTasks(Array.isArray(tasksResp) ? tasksResp : []);
    setTaskHistory(Array.isArray(taskHistoryResp) ? taskHistoryResp : []);
    setOrders(Array.isArray(ordersResp) ? ordersResp : []);
    setPayments(Array.isArray(paymentsResp) ? paymentsResp : []);
    setReferrals(referralsResp?.referrals || []);
    setStats({
      user: userStatsResp?.data || userStatsResp?.stats || null,
      public: publicStatsResp?.data || null,
    });

    renderAll();
  } catch (error) {
    console.error('[Boost] loadInitialData failed', error);
    showToast({ type: 'error', title: 'Ошибка загрузки', message: error.message });
  }
}

function renderAll() {
  const profile = state.profile;
  const totalEarned = state.stats.user?.total_earned_uzt ?? state.stats.user?.totalEarned ?? 0;
  const referralsCount = state.referrals?.length ?? 0;

  renderDashboard({
    balance: state.balance ?? profile?.balance ?? 0,
    totalEarned,
    ordersCount: state.orders?.length ?? 0,
    referralsCount,
    tasks: state.tasks,
    history: buildHistoryEvents(),
  });
  renderTasks(state.tasks);
  renderTaskHistory(state.taskHistory);
  renderOrders(state.orders);
  renderPayments(state.payments);
  renderProfileSummary(profile, { balance: state.balance, totalEarned });
  populateProfileForm(profile);
  renderReferrals(state.referrals);
  updateUserChip({
    name: composeDisplayName(state.user),
    balance: state.balance ?? profile?.balance ?? state.user?.balance,
  });
}

function bindEvents() {
  document.querySelectorAll('.nav-btn').forEach((button) => {
    button.addEventListener('click', (event) => {
      const viewId = event.currentTarget.dataset.view;
      if (viewId) {
        switchView(viewId);
      }
    });
  });

  document.getElementById('open-payments-view')?.addEventListener('click', () => switchView('payments'));

  document.getElementById('refresh-dashboard-tasks')?.addEventListener('click', () => refreshTasks());
  document.getElementById('refresh-dashboard-history')?.addEventListener('click', () => refreshHistory());
  document.getElementById('refresh-tasks')?.addEventListener('click', () => refreshTasks());
  document.getElementById('refresh-task-history')?.addEventListener('click', () => refreshTaskHistory());
  document.getElementById('refresh-orders')?.addEventListener('click', () => refreshOrders());
  document.getElementById('refresh-payments')?.addEventListener('click', () => refreshPayments());
  document.getElementById('refresh-referrals')?.addEventListener('click', () => refreshReferrals());

  document.getElementById('tasks-list')?.addEventListener('click', async (event) => {
    const target = event.target.closest('[data-action="complete-task"]');
    if (!target) return;
    const taskId = target.dataset.taskId;
    if (!taskId) return;
    setLoading(target, true);
    try {
      const result = await api.completeTask(taskId);
      showToast({ type: 'success', title: 'Задание выполнено', message: `Начислено ${result.reward ?? 0} UZT` });
      await Promise.all([refreshTasks(), refreshTaskHistory(), refreshBalance()]);
    } catch (error) {
      showToast({ type: 'error', title: 'Не удалось выполнить', message: error.message });
    } finally {
      setLoading(target, false);
    }
  });

  document.getElementById('dashboard-tasks')?.addEventListener('click', (event) => {
    if (event.target.closest('[data-action="open-task"]')) {
      switchView('tasks');
    }
  });

  const orderForm = document.getElementById('order-form');
  orderForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(orderForm);
    const payload = {
      orderType: formData.get('order_type'),
      targetUrl: formData.get('target_url'),
      quantity: formData.get('quantity'),
    };
    setLoading(orderForm.querySelector('button[type="submit"]'), true);
    try {
      await api.createOrder(payload);
      showToast({ type: 'success', title: 'Заказ создан', message: 'Кампания успешно размещена.' });
      orderForm.reset();
      await Promise.all([refreshOrders(), refreshBalance()]);
    } catch (error) {
      showToast({ type: 'error', title: 'Ошибка создания', message: error.message });
    } finally {
      setLoading(orderForm.querySelector('button[type="submit"]'), false);
    }
  });

  document.getElementById('orders-table')?.addEventListener('click', async (event) => {
    const target = event.target.closest('[data-action="cancel-order"]');
    if (!target) return;
    const orderId = target.dataset.orderId;
    if (!orderId) return;
    setLoading(target, true);
    try {
      await api.cancelOrder(orderId);
      showToast({ type: 'success', title: 'Заказ отменён', message: `Возврат средств оформлен.` });
      await Promise.all([refreshOrders(), refreshBalance()]);
    } catch (error) {
      showToast({ type: 'error', title: 'Не удалось отменить', message: error.message });
    } finally {
      setLoading(target, false);
    }
  });

  const paymentForm = document.getElementById('manual-payment-form');
  paymentForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(paymentForm);
    const payload = {
      amount: formData.get('amount'),
      checkPhotoUrl: formData.get('check_photo_url'),
    };
    const submitBtn = paymentForm.querySelector('button[type="submit"]');
    setLoading(submitBtn, true);
    try {
      await api.createManualPayment(payload);
      showToast({ type: 'success', title: 'Заявка отправлена', message: 'Мы уведомим вас о подтверждении.' });
      paymentForm.reset();
      await refreshPayments();
    } catch (error) {
      showToast({ type: 'error', title: 'Ошибка заявки', message: error.message });
    } finally {
      setLoading(submitBtn, false);
    }
  });

  const profileForm = document.getElementById('profile-form');
  profileForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(profileForm);
    const payload = {
      username: formData.get('username'),
      language: formData.get('language'),
    };
    const submitBtn = profileForm.querySelector('button[type="submit"]');
    setLoading(submitBtn, true);
    try {
      const response = await api.updateProfile(payload);
      const updated = response?.user || response?.data || null;
      if (updated) {
        setProfile({ ...state.profile, ...updated });
        populateProfileForm(state.profile);
        renderProfileSummary(state.profile, { balance: state.balance, totalEarned: state.stats.user?.total_earned_uzt });
        showToast({ type: 'success', title: 'Профиль обновлён', message: 'Изменения сохранены.' });
      }
    } catch (error) {
      showToast({ type: 'error', title: 'Не удалось сохранить', message: error.message });
    } finally {
      setLoading(submitBtn, false);
    }
  });

  document.getElementById('sync-balance')?.addEventListener('click', async (event) => {
    const button = event.currentTarget;
    setLoading(button, true);
    try {
      await api.syncBalance();
      showToast({ type: 'success', title: 'Баланс синхронизирован', message: 'Проверьте уведомление в Telegram.' });
      await refreshBalance();
    } catch (error) {
      showToast({ type: 'error', title: 'Ошибка синхронизации', message: error.message });
    } finally {
      setLoading(button, false);
    }
  });

  document.getElementById('delete-account')?.addEventListener('click', async () => {
    if (!confirm('Удалить аккаунт без возможности восстановления?')) {
      return;
    }
    try {
      await api.deleteAccount();
      showToast({ type: 'success', title: 'Аккаунт удалён', message: 'Сессия будет завершена.' });
      setTimeout(() => {
        window.Telegram?.WebApp?.close();
      }, 1500);
    } catch (error) {
      showToast({ type: 'error', title: 'Ошибка удаления', message: error.message });
    }
  });
}

async function refreshBalance() {
  try {
    const balanceResp = await api.fetchBalance();
    setBalance(balanceResp?.balance ?? null);
    renderDashboard({
      balance: state.balance ?? state.profile?.balance ?? 0,
      totalEarned: state.stats.user?.total_earned_uzt ?? 0,
      ordersCount: state.orders?.length ?? 0,
      referralsCount: state.referrals?.length ?? 0,
      tasks: state.tasks,
      history: buildHistoryEvents(),
    });
    renderProfileSummary(state.profile, { balance: state.balance, totalEarned: state.stats.user?.total_earned_uzt ?? 0 });
    updateUserChip({ name: composeDisplayName(state.user), balance: state.balance });
  } catch (error) {
    showToast({ type: 'error', title: 'Баланс недоступен', message: error.message });
  }
}

async function refreshTasks() {
  try {
    const tasks = await api.fetchTasks();
    setTasks(tasks);
    renderTasks(state.tasks);
    renderDashboard({
      balance: state.balance ?? state.profile?.balance ?? 0,
      totalEarned: state.stats.user?.total_earned_uzt ?? 0,
      ordersCount: state.orders?.length ?? 0,
      referralsCount: state.referrals?.length ?? 0,
      tasks: state.tasks,
      history: buildHistoryEvents(),
    });
  } catch (error) {
    showToast({ type: 'error', title: 'Не удалось обновить задания', message: error.message });
  }
}

async function refreshTaskHistory() {
  try {
    const history = await api.fetchTaskHistory();
    setTaskHistory(history);
    renderTaskHistory(state.taskHistory);
  } catch (error) {
    showToast({ type: 'error', title: 'История задач недоступна', message: error.message });
  }
}

async function refreshOrders() {
  try {
    const orders = await api.fetchOrders();
    setOrders(orders);
    renderOrders(state.orders);
    renderDashboard({
      balance: state.balance ?? state.profile?.balance ?? 0,
      totalEarned: state.stats.user?.total_earned_uzt ?? 0,
      ordersCount: state.orders?.length ?? 0,
      referralsCount: state.referrals?.length ?? 0,
      tasks: state.tasks,
      history: buildHistoryEvents(),
    });
  } catch (error) {
    showToast({ type: 'error', title: 'Не удалось получить заказы', message: error.message });
  }
}

async function refreshPayments() {
  try {
    const payments = await api.fetchPaymentsHistory();
    setPayments(payments);
    renderPayments(state.payments);
    renderDashboard({
      balance: state.balance ?? state.profile?.balance ?? 0,
      totalEarned: state.stats.user?.total_earned_uzt ?? 0,
      ordersCount: state.orders?.length ?? 0,
      referralsCount: state.referrals?.length ?? 0,
      tasks: state.tasks,
      history: buildHistoryEvents(),
    });
  } catch (error) {
    showToast({ type: 'error', title: 'История операций недоступна', message: error.message });
  }
}

async function refreshReferrals() {
  try {
    const referrals = await api.fetchReferrals();
    setReferrals(referrals?.referrals || []);
    renderReferrals(state.referrals);
    renderDashboard({
      balance: state.balance ?? state.profile?.balance ?? 0,
      totalEarned: state.stats.user?.total_earned_uzt ?? 0,
      ordersCount: state.orders?.length ?? 0,
      referralsCount: state.referrals?.length ?? 0,
      tasks: state.tasks,
      history: buildHistoryEvents(),
    });
  } catch (error) {
    showToast({ type: 'error', title: 'Рефералы недоступны', message: error.message });
  }
}

async function refreshHistory() {
  await Promise.all([refreshPayments(), refreshBalanceHistory()]);
}

async function refreshBalanceHistory() {
  try {
    const history = await api.fetchBalanceHistory();
    setBalanceHistory(history);
    renderDashboard({
      balance: state.balance ?? state.profile?.balance ?? 0,
      totalEarned: state.stats.user?.total_earned_uzt ?? 0,
      ordersCount: state.orders?.length ?? 0,
      referralsCount: state.referrals?.length ?? 0,
      tasks: state.tasks,
      history: buildHistoryEvents(),
    });
  } catch (error) {
    showToast({ type: 'error', title: 'Не удалось обновить историю', message: error.message });
  }
}

document.addEventListener('DOMContentLoaded', bootstrap);
