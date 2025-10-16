import { setLoading, showToast } from '../ui.js';

function bindTaskFilters() {
  const buttons = Array.from(document.querySelectorAll('[data-task-filter]'));
  const list = document.getElementById('tasks-list');
  if (!buttons.length) return;

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      buttons.forEach((btn) => btn.classList.toggle('is-active', btn === button));
      if (list) {
        list.dataset.filter = button.dataset.taskFilter || 'all';
      }
    });
  });
}

export function initTasksView({ onRefresh } = {}) {
  bindTaskFilters();

  const refreshBtn = document.getElementById('tasks-refresh');
  if (refreshBtn && typeof onRefresh === 'function') {
    refreshBtn.addEventListener('click', async () => {
      setLoading(refreshBtn, true);
      try {
        await onRefresh();
        showToast({ type: 'success', title: 'Задания обновлены' });
      } catch (error) {
        console.error('[Boost] tasks refresh failed', error);
        showToast({
          type: 'error',
          title: 'Не удалось обновить задания',
          message: error.message || 'Попробуйте позже.',
        });
      } finally {
        setLoading(refreshBtn, false);
      }
    });
  }

  const tasksList = document.getElementById('tasks-list');
  if (tasksList) {
    tasksList.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-action="open-task"]') || event.target.closest('button');
      if (!button) return;
      const taskId = button.dataset.taskId;
      showToast({
        type: 'info',
        title: 'Задание',
        message: taskId ? `Открываем задание #${taskId}` : 'Открываем задание',
        duration: 3000,
      });
    });
  }
}
