import { api } from '../api.js?v=2.0.0';
import { state } from '../state.js?v=2.0.0';
import { showToast } from '../ui.js?v=2.0.0';

export const LoginPage = {
  async render(container) {
    container.innerHTML = `
      <div class="login-wrapper">
        <div class="login-card">
          <div class="login-header">
            <div class="logo-large">
              <i class="ph-fill ph-bowl-food"></i>
              <span>NutriCook</span>
            </div>
            <h2>Masuk ke Akun Anda</h2>
            <p class="subtitle">Platform rekomendasi resep sadar nutrisi terpersonalisasi.</p>
          </div>
          
          <form id="login-form">
            <div class="form-group">
              <label for="login-userid">User ID</label>
              <input type="number" id="login-userid" placeholder="Contoh: 1533" required min="1">
            </div>
            <div class="form-group">
              <label for="login-password">Password</label>
              <input type="password" id="login-password" value="nutricook" required>
              <span class="field-hint">Gunakan password universal: <code>nutricook</code></span>
            </div>
            <button type="submit" class="btn btn-primary btn-block" id="btn-login-submit">
              Masuk
            </button>
          </form>
          
          <div class="divider">
            <span>atau gunakan akun demo</span>
          </div>
          
          <div class="demo-accounts" id="demo-accounts-list">
            <div class="loading-inline">Memuat akun demo...</div>
          </div>
        </div>
      </div>
    `;

    const form = container.querySelector('#login-form');
    const userIdInput = container.querySelector('#login-userid');
    const passwordInput = container.querySelector('#login-password');
    const demoList = container.querySelector('#demo-accounts-list');

    try {
      const personas = await api.getPersonas();
      demoList.innerHTML = personas.map(p => `
        <button type="button" class="demo-btn" data-userid="${p.user_id}">
          <div class="demo-avatar" style="background: ${p.avatar_color || 'var(--text-secondary)'}">
            ${p.display_name.charAt(0)}
          </div>
          <div class="demo-info">
            <span class="demo-name">${p.display_name.split(' (')[0]}</span>
            <span class="demo-desc">${p.bio}</span>
          </div>
        </button>
      `).join('');

      demoList.querySelectorAll('.demo-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const userId = btn.getAttribute('data-userid');
          userIdInput.value = userId;
          passwordInput.value = 'nutricook';
          form.dispatchEvent(new Event('submit'));
        });
      });
    } catch (err) {
      console.error('Failed to load personas:', err);
      demoList.innerHTML = `
        <p style="color: var(--text-secondary); text-align: center; font-size: 13px; grid-column: span 2;">
          Gagal memuat akun demo. Anda tetap bisa masuk menggunakan User ID manual (misal: 1533) dan password <code>nutricook</code>.
        </p>
      `;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const userId = userIdInput.value;
      const password = passwordInput.value;
      
      try {
        const btnSubmit = container.querySelector('#btn-login-submit');
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="ph-bold ph-spinner spinner" style="margin-right: 8px;"></i> Masuk...';

        const user = await api.login(userId, password);
        state.currentUser = user;
        showToast(`Selamat datang kembali, ${user.display_name}!`, 'success');
        
        window.location.hash = '#/';
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        const btnSubmit = container.querySelector('#btn-login-submit');
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.innerHTML = 'Masuk';
        }
      }
    });
  }
};
