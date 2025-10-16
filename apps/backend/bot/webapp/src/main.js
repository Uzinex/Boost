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
  toNumber,
} from './ui.js';
import { initTasksView } from './views/tasks.js';
import { initOrdersView } from './views/orders.js';
import { initPaymentsView } from './views/payments.js';
import { initProfileView } from './views/profile.js';

const tg = window.Telegram?.WebApp;
const AVAILABLE_VIEWS = ['dashboard', 'tasks', 'orders', 'payments', 'profile'];

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
  if (typeof value !== 'string') return false;
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
}

function shouldUseMockAuth(searchParams, config) {
  if (!config) return false;
  const explicitMock =
    parseBooleanFlag(searchParams.get('mock')) ||
    parseBooleanFlag(searchParams.get('debug')) ||
    parseBooleanFlag(searchParams.get('useMockAuth'));
  return explicitMock || Boolean(config.mockAuthEnabled);
}

function buildMockAuthParams(searchParams, config) {
  const baseUser = config && typeof config.mockAuthUser === 'object' ? config.mockAuthUser : {};
  const baseParams = config && typeof config.mockAuthParams === 'object' ? config.mockAuthParams : {};
  const overrides = {};

  const telegramId = searchParams.get('telegram_id') || searchParams.get('user_id');
  if (telegramId) {
    const parsedId = Number(telegramId);
    if (!Number.isNaN(parsedId)) overrides.telegram_id = parsedId;
  }

  if (searchParams.get('username')) overrides.username = searchParams.get('username');
  if (searchParams.get('first_name')) overrides.first_name = searchParams.get('first_name');
  if (searchParams.get('last_name')) overrides.last_name = searchParams.get('last_name');

  const languageOverride = searchParams.get('language_code') || searchParams.get('language');
  if (languageOverride) overrides.language_code = languageOverride;

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

function normalizeViewId(value) {
  return typeof value === 'string' ? value.trim().toLowerCase() : '';
}

function resolveInitialView({ searchParams } = {}) {
  const fromQuery = normalizeViewId(searchParams?.get?.('view'));
  if (AVAILABLE_VIEWS.includes(fromQuery)) {
    return fromQuery;
  }

  const fromBody = normalizeViewId(document.body?.dataset?.defaultView);
  if (AVAILABLE_VIEWS.includes(fromBody)) {
    return fromBody;
  }

  const pathMatch = window.location.pathname.match(/([a-z-]+)\.html$/i);
  if (pathMatch) {
    const candidate = normalizeViewId(pathMatch[1]);
    if (candidate === 'index') {
      return 'dashboard';
    }
    if (AVAILABLE_VIEWS.includes(candidate)) {
      return candidate;
    }
  }

  return 'dashboard';
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
  return events.filter((item) => item.date).sort((a, b) => new Date(b.date) - new Date(a.date));
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

    // 🔹 Сразу отрисовываем предзагруженные данные (если backend их подставил)
    renderAll();

    const searchParams = new URLSearchParams(window.location.search);
    const initialView = resolveInitialView({ searchParams });
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

    // ⚡️ Обновляем интерфейс базовыми значениями до загрузки данных,
    // чтобы избавиться от «прочерков» в карточках при медленном ответе API.
    renderAll();

    await loadInitialData();
    bindEvents();
    initViewControllers();
    switchView(initialView);

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
    const [
      profileResp,
      userStatsResp,
      publicStatsResp,
      balanceResp,
      balanceHistoryResp,
      tasksResp,
      taskHistoryResp,
      ordersResp,
      paymentsResp,
      referralsResp,
    ] = await Promise.all([
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
    setBalance(balanceResp?.balance ?? profile?.balance ?? 0);
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

  } catch (error) {
    console.error('[Boost] loadInitialData failed', error);
    showToast({ type: 'error', title: 'Ошибка загрузки', message: error.message });
  } finally {
    // ✅ Даже при ошибке гарантирум актуальный рендер (с прежними или дефолтными данными)
    renderAll();
  }
}

/* ✅ Исправлено — теперь все числовые значения гарантированно отображаются */
function renderAll() {
  const profile = state.profile || {};
  const totalEarned = toNumber(
    state.stats.user?.total_earned_uzt ?? state.stats.user?.totalEarned ?? 0,
    0
  );
  const referralsCount = Array.isArray(state.referrals) ? state.referrals.length : 0;
  const ordersCount = Array.isArray(state.orders) ? state.orders.length : 0;
  const balance = toNumber(state.balance ?? profile.balance ?? 0, 0);
  const lastPayment = Array.isArray(state.payments)
    ? state.payments
        .slice()
        .filter((payment) => payment?.created_at || payment?.updated_at)
        .sort((a, b) => new Date(b.created_at || b.updated_at) - new Date(a.created_at || a.updated_at))[0]
    : null;
  const ordersSummary = Array.isArray(state.orders)
    ? state.orders.reduce(
        (acc, order) => {
          const status = (order.status || '').toLowerCase();
          if (status === 'active' || status === 'running') acc.active += 1;
          if (status === 'completed' || status === 'done') acc.completed += 1;
          if (typeof order.budget === 'number') acc.budget += order.budget;
          else if (typeof order.amount === 'number') acc.budget += order.amount;
          return acc;
        },
        { active: 0, completed: 0, budget: 0 }
      )
    : { active: 0, completed: 0, budget: 0 };

  renderDashboard({
    balance: balance,
    totalEarned: totalEarned,
    ordersCount: ordersCount,
    referralsCount: referralsCount,
    tasks: state.tasks || [],
    history: buildHistoryEvents() || [],
  });

  renderTasks(state.tasks || []);
  renderTaskHistory(state.taskHistory || []);
  renderOrders(state.orders || [], { summary: ordersSummary });
  renderPayments(state.payments || [], { balance, lastPayment });
  renderProfileSummary(profile, { balance, totalEarned });
  populateProfileForm(profile);
  renderReferrals(state.referrals || []);
  updateUserChip({
    name: composeDisplayName(state.user),
    balance: balance,
  });
}

function bindEvents() {
  const navButtons = Array.from(document.querySelectorAll('.nav-btn'));
  navButtons.forEach((btn) => {
    btn.addEventListener('click', (event) => {
      const view = event.currentTarget?.dataset?.view;
      if (view) {
        switchView(view);
      }
    });
  });

  const viewToggles = Array.from(document.querySelectorAll('[data-view-target]'));
  viewToggles.forEach((el) => {
    el.addEventListener('click', (event) => {
      const view = event.currentTarget?.dataset?.viewTarget;
      if (view) {
        switchView(view);
      }
    });
  });

  const openPayments = document.getElementById('open-payments-view');
  if (openPayments) {
    openPayments.addEventListener('click', () => switchView('payments'));
  }

  const refreshButtons = [
    document.getElementById('refresh-dashboard-tasks'),
    document.getElementById('refresh-dashboard-history'),
  ].filter(Boolean);

  refreshButtons.forEach((btn) => {
    btn.addEventListener('click', async () => {
      setLoading(btn, true);
      try {
        await loadInitialData();
      } catch (error) {
        console.error('[Boost] refresh failed', error);
        showToast({
          type: 'error',
          title: 'Ошибка обновления',
          message: error.message || 'Не удалось обновить данные',
        });
      } finally {
        setLoading(btn, false);
      }
    });
  });
}

function initViewControllers() {
  const refresh = () => loadInitialData();
  initTasksView({ onRefresh: refresh });
  initOrdersView({ onRefresh: refresh, onCreateOrder: handleOrderCreate });
  initPaymentsView({ onRefresh: refresh });
  initProfileView({ onRefresh: refresh, onUpdateProfile: handleProfileUpdate });
}

async function handleOrderCreate({ orderType, targetUrl, quantity }) {
  const response = await api.createOrder({ orderType, targetUrl, quantity });
  const created = response?.order || response?.data || response || {};
  const orderId =
    created?.id ?? created?.order_id ?? response?.order_id ?? response?.data?.order_id ?? null;
  const totalCostRaw = created?.total_cost ?? response?.total_cost ?? response?.data?.total_cost;
  const costNumber = Number(totalCostRaw);
  const details = [];
  if (orderId !== null && orderId !== undefined) {
    details.push(`№${orderId}`);
  }
  if (Number.isFinite(costNumber)) {
    details.push(`Списано ${costNumber.toFixed(2)} UZT`);
  }
  showToast({
    type: 'success',
    title: 'Заказ создан',
    message: details.length ? details.join(' • ') : 'Кампания отправлена на модерацию.',
  });
  await loadInitialData();
  return created;
}

async function handleProfileUpdate({ username, language }) {
  const payload = { username, language };
  const response = await api.updateProfile(payload);
  const updated = response?.user || response?.profile || response?.data || null;
  if (updated) {
    setProfile(updated);
    setUser(updated);
  }
  showToast({ type: 'success', title: 'Профиль сохранён' });
  await loadInitialData();
}

document.addEventListener('DOMContentLoaded', bootstrap);
