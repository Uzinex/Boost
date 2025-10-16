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

function setupOrderModal({ onCreateOrder } = {}) {
  const modal = document.getElementById('order-create-modal');
  const form = document.getElementById('order-create-form');
  const submitBtn = document.getElementById('order-create-submit');
  const createBtn = document.getElementById('orders-create');
  if (!modal || !form || !createBtn) {
    return;
  }

  let keydownHandler = null;

  const setModalVisibility = (isVisible) => {
    modal.toggleAttribute('hidden', !isVisible);
    modal.setAttribute('aria-hidden', isVisible ? 'false' : 'true');
    document.body.classList.toggle('is-modal-open', isVisible);
  };

  setModalVisibility(!modal.hidden);

  const closeModal = () => {
    setModalVisibility(false);
    if (keydownHandler) {
      document.removeEventListener('keydown', keydownHandler);
      keydownHandler = null;
    }
  };

  const openModal = () => {
    setModalVisibility(true);
    form.reset();
    const firstField = form.querySelector('input, select, textarea');
    if (firstField) firstField.focus();
    if (!keydownHandler) {
      keydownHandler = (event) => {
        if (event.key === 'Escape') {
          event.preventDefault();
          closeModal();
        }
      };
      document.addEventListener('keydown', keydownHandler);
    }
  };

  modal.addEventListener('click', (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });

  const closeButtons = Array.from(modal.querySelectorAll('[data-modal-close]'));
  closeButtons.forEach((button) => {
    button.addEventListener('click', () => closeModal());
  });

  createBtn.addEventListener('click', (event) => {
    event.preventDefault();
    openModal();
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (typeof onCreateOrder !== 'function') {
      showToast({
        type: 'warning',
        title: 'Создание недоступно',
        message: 'Попробуйте обновить страницу или обратитесь в поддержку.',
      });
      return;
    }

    const formData = new FormData(form);
    const orderType = String(formData.get('order_type') || '').trim();
    const targetUrlRaw = String(formData.get('target_url') || '').trim();
    const quantityValue = Number(formData.get('quantity'));
    const quantity = Number.isFinite(quantityValue) ? Math.round(quantityValue) : NaN;

    if (!orderType) {
      showToast({ type: 'warning', title: 'Укажите тип заказа' });
      return;
    }

    let normalizedUrl = '';
    try {
      const parsed = new URL(targetUrlRaw);
      normalizedUrl = parsed.toString();
    } catch (error) {
      console.warn('[Boost] invalid order target url', error);
      showToast({
        type: 'warning',
        title: 'Некорректная ссылка',
        message: 'Введите полноценную ссылку, начиная с https://',
      });
      return;
    }

    if (!Number.isFinite(quantity) || quantity < 10 || quantity > 10000) {
      showToast({
        type: 'warning',
        title: 'Некорректное количество',
        message: 'Допустимый диапазон — от 10 до 10000.',
      });
      return;
    }

    setLoading(submitBtn, true);
    try {
      await onCreateOrder({ orderType, targetUrl: normalizedUrl, quantity });
      form.reset();
      closeModal();
    } catch (error) {
      console.error('[Boost] order create failed', error);
      showToast({
        type: 'error',
        title: 'Не удалось создать заказ',
        message: error.message || 'Попробуйте ещё раз позже.',
      });
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

export function initOrdersView({ onRefresh, onCreateOrder } = {}) {
  bindOrderFilters();
  setupOrderModal({ onCreateOrder });

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
