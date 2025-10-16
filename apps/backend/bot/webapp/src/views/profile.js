import { setLoading, showToast } from '../ui.js';

async function copyToClipboard(text) {
  if (!text) {
    showToast({ type: 'warning', title: 'Нет данных для копирования' });
    return;
  }

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const temp = document.createElement('textarea');
      temp.value = text;
      temp.setAttribute('readonly', '');
      temp.style.position = 'absolute';
      temp.style.left = '-9999px';
      document.body.appendChild(temp);
      temp.select();
      document.execCommand('copy');
      document.body.removeChild(temp);
    }
    showToast({ type: 'success', title: 'Ссылка скопирована' });
  } catch (error) {
    console.error('[Boost] copy referral failed', error);
    showToast({
      type: 'error',
      title: 'Не удалось скопировать ссылку',
      message: error.message || 'Попробуйте вручную.',
    });
  }
}

export function initProfileView({ onRefresh, onUpdateProfile } = {}) {
  const refreshBtn = document.getElementById('profile-refresh');
  if (refreshBtn && typeof onRefresh === 'function') {
    refreshBtn.addEventListener('click', async () => {
      setLoading(refreshBtn, true);
      try {
        await onRefresh();
        showToast({ type: 'success', title: 'Профиль обновлён' });
      } catch (error) {
        console.error('[Boost] profile refresh failed', error);
        showToast({
          type: 'error',
          title: 'Не удалось обновить профиль',
          message: error.message || 'Попробуйте позже.',
        });
      } finally {
        setLoading(refreshBtn, false);
      }
    });
  }

  const form = document.getElementById('profile-form');
  if (form && typeof onUpdateProfile === 'function') {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const submitBtn = form.querySelector('button[type="submit"]');
      const formData = new FormData(form);
      const payload = {
        username: formData.get('username')?.toString().trim() || '',
        language: formData.get('language')?.toString().trim() || 'ru',
      };

      if (submitBtn) setLoading(submitBtn, true);
      try {
        await onUpdateProfile(payload);
      } catch (error) {
        console.error('[Boost] update profile failed', error);
        showToast({
          type: 'error',
          title: 'Не удалось сохранить профиль',
          message: error.message || 'Попробуйте позже.',
        });
      } finally {
        if (submitBtn) setLoading(submitBtn, false);
      }
    });
  }

  const copyBtn = document.getElementById('profile-copy-ref');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const link = document.getElementById('profile-referral-link');
      copyToClipboard(link?.textContent?.trim() || '');
    });
  }

  const deleteBtn = document.getElementById('profile-delete');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
      showToast({
        type: 'warning',
        title: 'Удаление аккаунта',
        message: 'Для удаления аккаунта обратитесь к поддержке Uzinex.',
        duration: 5000,
      });
    });
  }
}
