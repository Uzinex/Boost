import { setLoading, showToast } from '../ui.js';

function bindOrderFilters() {
  const buttons = Array.from(document.querySelectorAll('[data-order-filter]'));
  const list = document.getElementById('orders-list');
  if (!buttons.length) return;

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      buttons.forEach((btn) => btn.classList.toggle('is-active', btn === button));
      if (list) {
        list.dataset.filter = button.dataset.orderFilter || 'all';
      }
    });
  });
}

export function initOrdersView({ onRefresh } = {}) {
  bindOrderFilters();

  const refreshBtn = document.getElementById('orders-refresh');
  if (refreshBtn && typeof onRefresh === 'function') {
    refreshBtn.addEventListener('click', async () => {
      setLoading(refreshBtn, true);
      try {
        await onRefresh();
        showToast({ type: 'success', title: 'Заказы обновлены' });
      } catch (error) {
        console.error('[Boost] orders refresh failed', error);
        showToast({
          type: 'error',
          title: 'Не удалось обновить заказы',
          message: error.message || 'Попробуйте позже.',
        });
      } finally {
        setLoading(refreshBtn, false);
      }
    });
  }

  const createBtn = document.getElementById('orders-create');
  if (createBtn) {
    createBtn.addEventListener('click', () => {
      showToast({
        type: 'info',
        title: 'Создание заказа',
        message: 'Функция будет доступна после подключения бэкенда.',
      });
    });
  }

  const ordersList = document.getElementById('orders-list');
  if (ordersList) {
    ordersList.addEventListener('click', (event) => {
      const button = event.target.closest('[data-action="open-order"]');
      if (!button) return;
      const orderId = button.dataset.orderId;
      showToast({
        type: 'info',
        title: 'Заказ',
        message: orderId ? `Открываем заказ #${orderId}` : 'Открываем заказ',
        duration: 3200,
      });
    });
  }
}
