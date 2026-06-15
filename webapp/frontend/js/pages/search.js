import { api } from '../api.js?v=2.0.0';
import { state } from '../state.js?v=2.0.0';
import { getNutritionBarHtml, animateStagger } from '../ui.js?v=2.0.0';
import { getNavbarHtml, attachNavbarListeners } from './dashboard.js?v=2.0.0';

export const SearchPage = {
  async render(container, params, queryParams) {
    const user = state.currentUser;
    if (!user) {
      window.location.hash = '#/login';
      return;
    }

    const searchQuery = queryParams.q || '';

    container.innerHTML = `
      ${getNavbarHtml()}
      
      <main class="search-content" style="max-width: 1200px; margin: 0 auto; padding: 40px 20px; width: 100%;">
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 2rem; font-family: var(--font-serif); font-weight: 500; margin-bottom: 8px;">Hasil Pencarian</h2>
          <p style="color: var(--text-secondary); font-size: 14px;">
            Menampilkan resep sehat untuk kata kunci: <strong style="color: var(--text-primary);">"${searchQuery}"</strong>
          </p>
        </div>

        <div id="search-loading" style="text-align: center; color: var(--text-secondary); padding: 40px 0;">
          <i class="ph-bold ph-spinner spinner" style="font-size: 32px; margin-bottom: 12px;"></i>
          <p>Mencari resep...</p>
        </div>

        <div id="search-results-grid" class="recommendation-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 24px; display: none;">
          <!-- Search results render here -->
        </div>

        <div id="search-empty" style="display: none; text-align: center; padding: 40px 0; color: var(--text-secondary);">
          <i class="ph-bold ph-magnifying-glass" style="font-size: 48px; margin-bottom: 16px; color: var(--border);"></i>
          <p style="font-size: 15px;">Tidak ditemukan resep sehat yang cocok dengan kata kunci "${searchQuery}".</p>
          <a href="#/" class="btn btn-secondary" style="margin-top: 16px;">Kembali ke Beranda</a>
        </div>
      </main>
    `;

    attachNavbarListeners(container);

    const navSearchInput = container.querySelector('#nav-search-input');
    if (navSearchInput) {
      navSearchInput.value = searchQuery;
    }

    const loadingDiv = container.querySelector('#search-loading');
    const gridDiv = container.querySelector('#search-results-grid');
    const emptyDiv = container.querySelector('#search-empty');

    try {
      const results = await api.searchRecipes(searchQuery, '', 40, 0);

      loadingDiv.style.display = 'none';

      if (!results || results.length === 0) {
        emptyDiv.style.display = 'block';
        return;
      }

      gridDiv.innerHTML = results.map(r => renderSearchRecipeCard(r)).join('');
      gridDiv.style.display = 'grid';

      animateStagger('#search-results-grid', '.recipe-card');

    } catch (err) {
      console.error('Failed to run search:', err);
      loadingDiv.innerHTML = `
        <i class="ph-bold ph-warning-circle" style="font-size: 32px; color: var(--pale-red-text); margin-bottom: 12px;"></i>
        <p>Gagal memproses pencarian: ${err.message}</p>
      `;
    }

    function renderSearchRecipeCard(recipe) {
      const calories = recipe.calories !== undefined ? recipe.calories : 0;
      const score = recipe.nutrition_score !== undefined ? recipe.nutrition_score : 50.0;
      
      return `
        <div class="recipe-card" data-id="${recipe.recipe_id || recipe.id}">
          <div class="recipe-card-img-placeholder">
            <i class="ph-bold ph-image" style="font-size: 28px; color: var(--border);"></i>
          </div>
          <div class="recipe-card-body">
            <h4 class="recipe-card-title">${recipe.name}</h4>
            <div class="recipe-card-meta">
              <span>${recipe.minutes} Mnt</span>
              <span>&middot;</span>
              <span>${recipe.n_ingredients} Bahan</span>
              <span>&middot;</span>
              <span>${Math.round(calories)} kkal</span>
            </div>
            <div style="margin-top: auto;">
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px; font-weight: 500;">
                <span>Kesehatan</span>
                <span style="font-weight: 600;">${Math.round(score)}</span>
              </div>
              ${getNutritionBarHtml(score)}
            </div>
          </div>
        </div>
      `;
    }

    container.addEventListener('click', (e) => {
      const card = e.target.closest('.recipe-card');
      if (card) {
        const id = card.getAttribute('data-id');
        window.location.hash = `#/recipe/${id}`;
      }
    });
  }
};
