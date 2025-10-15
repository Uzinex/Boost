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

    renderAll();
  } catch (error) {
    console.error('[Boost] loadInitialData failed', error);
    showToast({ type: 'error', title: 'Ошибка загрузки', message: error.message });
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
  renderOrders(state.orders || []);
  renderPayments(state.payments || []);
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

document.addEventListener('DOMContentLoaded', bootstrap);
