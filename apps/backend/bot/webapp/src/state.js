const DEFAULT_CONFIG = {
  apiBaseUrl: '/api/v1',
  botToken: '',
  locale: 'ru',
};

function parseEmbeddedConfig() {
  const node = document.getElementById('boost-config');
  if (!node) {
    return {};
  }
  try {
    return JSON.parse(node.textContent || '{}');
  } catch (error) {
    console.warn('[Boost] Failed to parse embedded config', error);
    return {};
  }
}

function normalizeConfig(config) {
  const normalized = { ...DEFAULT_CONFIG, ...config };
  if (normalized.apiBaseUrl.endsWith('/')) {
    normalized.apiBaseUrl = normalized.apiBaseUrl.slice(0, -1);
  }
  return normalized;
}

const windowConfig = typeof window !== 'undefined' && window.__BOOST_CONFIG ? window.__BOOST_CONFIG : {};

export const state = {
  config: normalizeConfig({ ...parseEmbeddedConfig(), ...windowConfig }),
  sessionToken: null,
  user: null,
  profile: null,
  stats: {
    public: null,
    user: null,
    orders: null,
  },
  balance: null,
  balanceHistory: [],
  tasks: [],
  taskHistory: [],
  orders: [],
  payments: [],
  referrals: [],
};

export function getConfig() {
  return state.config;
}

export function updateConfig(partial) {
  state.config = normalizeConfig({ ...state.config, ...partial });
}

export function setSessionToken(token) {
  state.sessionToken = token;
}

export function setUser(user) {
  state.user = user;
}

export function setProfile(profile) {
  state.profile = profile;
}

export function setStats(partial) {
  state.stats = { ...state.stats, ...partial };
}

export function setBalance(balance) {
  state.balance = balance;
}

export function setBalanceHistory(history) {
  state.balanceHistory = Array.isArray(history) ? history : [];
}

export function setTasks(tasks) {
  state.tasks = Array.isArray(tasks) ? tasks : [];
}

export function setTaskHistory(history) {
  state.taskHistory = Array.isArray(history) ? history : [];
}

export function setOrders(orders) {
  state.orders = Array.isArray(orders) ? orders : [];
}

export function setPayments(payments) {
  state.payments = Array.isArray(payments) ? payments : [];
}

export function setReferrals(referrals) {
  state.referrals = Array.isArray(referrals) ? referrals : [];
}

export function resetSession() {
  state.sessionToken = null;
  state.user = null;
  state.profile = null;
  state.stats = { public: null, user: null, orders: null };
  state.balance = null;
  state.balanceHistory = [];
  state.tasks = [];
  state.taskHistory = [];
  state.orders = [];
  state.payments = [];
  state.referrals = [];
}
