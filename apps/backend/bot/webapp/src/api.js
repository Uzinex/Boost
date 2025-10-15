import { getConfig } from './state.js';

let authToken = null;

function resolveBaseUrl() {
  const { apiBaseUrl } = getConfig();
  if (/^https?:/i.test(apiBaseUrl)) {
    return apiBaseUrl;
  }
  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://localhost';
  return `${origin.replace(/\/$/, '')}${apiBaseUrl.startsWith('/') ? '' : '/'}${apiBaseUrl}`;
}

function buildUrl(path, params) {
  if (/^https?:/i.test(path)) {
    const directUrl = new URL(path);
    if (params && typeof params === 'object') {
      Object.entries(params)
        .filter(([, value]) => value !== undefined && value !== null && value !== '')
        .forEach(([key, value]) => directUrl.searchParams.set(key, String(value)));
    }
    return directUrl;
  }
  const base = resolveBaseUrl();
  const baseWithSlash = base.endsWith('/') ? base : `${base}/`;
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path;
  const url = new URL(normalizedPath, baseWithSlash);
  if (params && typeof params === 'object') {
    Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .forEach(([key, value]) => url.searchParams.set(key, String(value)));
  }
  return url;
}

async function parseJson(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    console.warn('[Boost] Failed to parse JSON response', error);
    return null;
  }
}

export function setAuthToken(token) {
  authToken = token;
}

export async function authWithTelegram(initData, overrideBotToken) {
  const { botToken } = getConfig();
  const tokenToUse = overrideBotToken || botToken;
  if (!tokenToUse) {
    throw new Error('Не настроен токен Telegram-бота для авторизации.');
  }
  const url = buildUrl('/telegram/auth/webapp', {
    init_data: initData,
    bot_token: tokenToUse,
  });
  const response = await fetch(url.toString(), { method: 'POST' });
  const payload = await parseJson(response);
  if (!response.ok || !payload?.ok) {
    const detail = payload?.detail || payload?.message || 'Авторизация через Telegram не удалась';
    throw new Error(detail);
  }
  return payload;
}

export async function authWithMockUser(params = {}) {
  const { mockAuthEndpoint = '/telegram/auth/mock' } = getConfig();
  if (!mockAuthEndpoint) {
    throw new Error('Mock-эндпоинт авторизации не сконфигурирован.');
  }

  const sanitizedParams = {};
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }
    sanitizedParams[key] = value;
  });

  const url = buildUrl(mockAuthEndpoint, sanitizedParams);
  const response = await fetch(url.toString(), { method: 'POST' });
  const payload = await parseJson(response);

  if (!response.ok || !payload?.ok) {
    const detail = payload?.detail || payload?.message || 'Mock-авторизация WebApp не удалась';
    throw new Error(detail);
  }

  return payload;
}

export async function apiRequest(path, options = {}) {
  const { method = 'GET', body, params, headers = {} } = options;
  const url = buildUrl(path, params);
  const requestInit = {
    method,
    headers: {
      Accept: 'application/json',
      ...headers,
    },
    credentials: 'omit',
  };

  if (authToken) {
    requestInit.headers.Authorization = `Bearer ${authToken}`;
  }

  if (body !== undefined && body !== null) {
    if (body instanceof FormData) {
      requestInit.body = body;
    } else {
      requestInit.headers['Content-Type'] = 'application/json';
      requestInit.body = JSON.stringify(body);
    }
  }

  let response;
  try {
    response = await fetch(url.toString(), requestInit);
  } catch (error) {
    console.error('[Boost] API network error', error);
    throw new Error('Сеть недоступна. Проверьте подключение к интернету.');
  }

  const payload = await parseJson(response);

  if (!response.ok) {
    const detail = payload?.detail || payload?.message || `Ошибка ${response.status}`;
    throw new Error(detail);
  }

  return payload;
}

export const api = {
  fetchPublicStats() {
    return apiRequest('/stats/public');
  },
  fetchUserStats() {
    return apiRequest('/stats/user');
  },
  fetchProfile() {
    return apiRequest('/users/me');
  },
  updateProfile({ username, language }) {
    return apiRequest('/users/update', {
      method: 'POST',
      params: { username, language },
    });
  },
  fetchReferrals() {
    return apiRequest('/users/referrals');
  },
  deleteAccount() {
    return apiRequest('/users/delete', { method: 'DELETE' });
  },
  fetchBalance() {
    return apiRequest('/balance/');
  },
  fetchBalanceHistory(limit = 10) {
    return apiRequest('/balance/history', { params: { limit } });
  },
  syncBalance() {
    return apiRequest('/balance/sync', { method: 'POST' });
  },
  fetchTasks(limit = 10) {
    return apiRequest('/tasks/', { params: { limit } });
  },
  completeTask(taskId) {
    return apiRequest(`/tasks/${taskId}/complete`, { method: 'POST' });
  },
  fetchTaskHistory(limit = 20) {
    return apiRequest('/tasks/history', { params: { limit } });
  },
  fetchOrders() {
    return apiRequest('/orders/');
  },
  fetchOrderSummary() {
    return apiRequest('/orders/stats/summary');
  },
  createOrder({ orderType, targetUrl, quantity }) {
    return apiRequest('/orders/', {
      method: 'POST',
      params: {
        order_type: orderType,
        target_url: targetUrl,
        quantity,
      },
    });
  },
  cancelOrder(orderId) {
    return apiRequest(`/orders/${orderId}/cancel`, { method: 'POST' });
  },
  fetchPaymentsHistory() {
    return apiRequest('/payments/history');
  },
  createManualPayment({ amount, checkPhotoUrl }) {
    return apiRequest('/payments/manual', {
      method: 'POST',
      params: {
        amount,
        check_photo_url: checkPhotoUrl,
      },
    });
  },
  cancelPayment(invoiceId) {
    return apiRequest(`/payments/${invoiceId}/cancel`, { method: 'POST' });
  },
  fetchPaymentStatus(invoiceId) {
    return apiRequest(`/payments/${invoiceId}/status`);
  },
  fetchRates() {
    return apiRequest('/payments/rates');
  },
};
