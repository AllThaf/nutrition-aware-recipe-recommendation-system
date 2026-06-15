import { initRouter } from './router.js';
import { showToast } from './ui.js';

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

function initApp() {
  window.addEventListener('api-error', (e) => {
    showToast(e.detail, 'error');
  });

  const appContainer = document.getElementById('app');
  if (appContainer) {
    initRouter(appContainer);
  } else {
    console.error('App container element (#app) not found!');
  }
}
