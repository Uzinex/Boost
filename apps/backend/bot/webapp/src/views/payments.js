import { setLoading, showToast } from '../ui.js';

function bindPaymentMethods() {
  const methods = Array.from(document.querySelectorAll('[data-payment-method]'));
  if (!methods.length) return;

  methods.forEach((button) => {
    button.addEventListener('click', () => {
      const method = button.dataset.paymentMethod || 'card';
      const messages = {
        card: 'Оплата банковской картой будет доступна после подключения платёжного провайдера.',
        crypto: 'Для пополнения в USDT свяжитесь с менеджером — курс обновляется автоматически.',
        manual: 'Создайте заявку и приложите чек, менеджер проверит её в течение 15 минут.',
      };
      showToast({
        type: 'info',
        title: 'Пополнение',
        message: messages[method] || messages.card,
        duration: 5000,
      });
    });
  });
}

export function initPaymentsView({ onRefresh } = {}) {
  bindPaymentMethods();

  const refreshBtn = document.getElementById('payments-refresh');
  if (refreshBtn && typeof onRefresh === 'function') {
    refreshBtn.addEventListener('click', async () => {
      setLoading(refreshBtn, true);
      try {
        await onRefresh();
        showToast({ type: 'success', title: 'Платежи обновлены' });
      } catch (error) {
        console.error('[Boost] payments refresh failed', error);
        showToast({
          type: 'error',
          title: 'Не удалось обновить платежи',
          message: error.message || 'Попробуйте позже.',
        });
      } finally {
        setLoading(refreshBtn, false);
      }
    });
  }

  const openBtn = document.getElementById('payments-open');
  if (openBtn) {
    openBtn.addEventListener('click', () => {
      showToast({
        type: 'info',
        title: 'Пополнение',
        message: 'Выберите способ пополнения ниже, чтобы оставить заявку.',
      });
    });
  }

  const paymentsList = document.getElementById('payments-list');
  if (paymentsList) {
    paymentsList.addEventListener('click', (event) => {
      const button = event.target.closest('[data-action="open-payment"]');
      if (!button) return;
      showToast({
        type: 'info',
        title: 'Статус платежа',
        message: 'Детальная страница появится в финальной версии WebApp.',
        duration: 3600,
      });
    });
  }
}
