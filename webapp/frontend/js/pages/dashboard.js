import { api } from '../api.js?v=2.0.0';
import { state } from '../state.js?v=2.0.0';
import { getNutritionBarHtml, getSignalBadgeHtml, animateStagger } from '../ui.js?v=2.0.0';

export function getNavbarHtml() {
  const user = state.currentUser;
  return `
    <header class="app-header">
      <div class="logo-section" onclick="window.location.hash = '#/'" style="cursor: pointer;">
        <i class="ph-fill ph-bowl-food" style="font-size: 24px; color: var(--text-primary);"></i>
        <h1>NutriCook</h1>
      </div>
      
      <div class="search-section">
        <form id="nav-search-form" style="display: flex; align-items: center; border: 1px solid var(--border); border-radius: 20px; padding: 4px 16px; background: var(--canvas); width: 300px;">
          <input type="text" id="nav-search-input" placeholder="Cari resep sehat..." style="border: none; background: transparent; outline: none; flex: 1; font-size: 13px; color: var(--text-primary);" required>
          <button type="submit" style="background: none; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--text-secondary);">
            <i class="ph-bold ph-magnifying-glass"></i>
          </button>
        </form>
      </div>
      
      <div class="user-section" style="display: flex; align-items: center; gap: 16px;">
        <div class="user-profile" style="display: flex; align-items: center; gap: 8px;">
          <div class="avatar-small" style="background: var(--text-primary); color: var(--surface); width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px;">
            ${user ? user.display_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <span style="font-size: 13px; font-weight: 500; color: var(--text-primary); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${user ? user.display_name.split(' (')[0] : 'User'}
          </span>
        </div>
        <button class="btn btn-secondary" id="btn-logout" style="font-size: 12px; padding: 6px 12px; border-radius: 20px;">
          <i class="ph-bold ph-sign-out" style="margin-right: 6px;"></i>
          Logout
        </button>
      </div>
    </header>
  `;
}

export function attachNavbarListeners(container) {
  const logoutBtn = container.querySelector('#btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      state.currentUser = null;
      window.location.hash = '#/login';
    });
  }

  const searchForm = container.querySelector('#nav-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const query = container.querySelector('#nav-search-input').value.trim();
      if (query) {
        window.location.hash = `#/search?q=${encodeURIComponent(query)}`;
      }
    });
  }
}

export const DashboardPage = {
  async render(container) {
    const user = state.currentUser;
    if (!user) {
      window.location.hash = '#/login';
      return;
    }

    container.innerHTML = `
      ${getNavbarHtml()}
      
      <main class="dashboard-content" style="max-width: 1200px; margin: 0 auto; padding: 40px 20px; width: 100%;">
        <div class="dashboard-hero" style="margin-bottom: 32px;">
          <h2 style="font-size: 2.2rem; font-family: var(--font-serif); font-weight: 500; margin-bottom: 8px;">Halo, ${user.display_name}</h2>
          <p style="color: var(--text-secondary); font-size: 14px;">Temukan resep sehat pilihan berdasarkan riwayat dan preferensi nutrisi Anda.</p>
        </div>
        
        <!-- Row 1: Rekomendasi Untukmu -->
        <div class="row-section" style="margin-bottom: 40px; position: relative;">
          <div class="row-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 style="font-size: 1.5rem; font-family: var(--font-serif); font-weight: 500;">Rekomendasi Untukmu</h3>
            <div style="position: relative;">
              <button class="btn btn-secondary" id="btn-filter-toggle" style="padding: 6px 12px; border-radius: 20px; font-size: 12px;">
                <i class="ph-bold ph-sliders-horizontal" style="margin-right: 6px;"></i>
                Filter Nutrisi
              </button>
              
              <!-- Nutrition Filter Overlay -->
              <div class="filter-overlay" id="filter-overlay" style="display: none; position: absolute; right: 0; top: 38px; z-index: 100; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 18px; width: 320px;">
                <h4 style="margin-bottom: 16px; font-size: 14px; font-family: var(--font-sans); font-weight: 600;">Filter Kandungan Nutrisi</h4>
                
                <div class="form-group" style="margin-bottom: 16px;">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <label style="font-size: 12px; font-weight: 500; color: var(--text-primary);">Kalori Maksimum</label>
                    <span id="val-calories" style="font-size: 12px; font-weight: 600; color: var(--text-secondary);">1000 kkal</span>
                  </div>
                  <input type="range" id="filter-calories" min="100" max="2000" step="50" value="1000" style="width: 100%;">
                </div>
                
                <div class="form-group" style="margin-bottom: 20px;">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <label style="font-size: 12px; font-weight: 500; color: var(--text-primary);">Skor Kesehatan Minimum</label>
                    <span id="val-nutrition" style="font-size: 12px; font-weight: 600; color: var(--text-secondary);">60</span>
                  </div>
                  <input type="range" id="filter-nutrition" min="0" max="100" step="5" value="60" style="width: 100%;">
                </div>
                
                <div style="display: flex; gap: 8px;">
                  <button type="button" class="btn btn-outline" id="btn-filter-reset" style="flex: 1; padding: 6px; font-size: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: transparent;">Reset</button>
                  <button type="button" class="btn btn-primary" id="btn-filter-apply" style="flex: 2; padding: 6px; font-size: 12px; border-radius: var(--radius-sm);">Terapkan</button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="horizontal-scroll" id="recs-scroll">
            <div style="padding: 20px; color: var(--text-secondary); text-align: center; width: 100%;">
              <i class="ph-bold ph-spinner spinner" style="font-size: 24px; margin-bottom: 8px;"></i>
              <p style="font-size: 13px;">Memuat rekomendasi resep...</p>
            </div>
          </div>
        </div>
        
        <!-- Row 2: Sedang Populer -->
        <div class="row-section">
          <div class="row-header" style="margin-bottom: 12px;">
            <h3 style="font-size: 1.5rem; font-family: var(--font-serif); font-weight: 500;">Sedang Populer</h3>
          </div>
          <div class="horizontal-scroll" id="popular-scroll">
            <div style="padding: 20px; color: var(--text-secondary); text-align: center; width: 100%;">
              <i class="ph-bold ph-spinner spinner" style="font-size: 24px; margin-bottom: 8px;"></i>
              <p style="font-size: 13px;">Memuat resep populer...</p>
            </div>
          </div>
        </div>
      </main>
    `;

    attachNavbarListeners(container);

    const btnFilterToggle = container.querySelector('#btn-filter-toggle');
    const filterOverlay = container.querySelector('#filter-overlay');
    const sliderCalories = container.querySelector('#filter-calories');
    const valCalories = container.querySelector('#val-calories');
    const sliderNutrition = container.querySelector('#filter-nutrition');
    const valNutrition = container.querySelector('#val-nutrition');
    const btnFilterApply = container.querySelector('#btn-filter-apply');
    const btnFilterReset = container.querySelector('#btn-filter-reset');

    const currentFilters = state.activeFilters;
    if (currentFilters.max_calories) {
      sliderCalories.value = currentFilters.max_calories;
      valCalories.textContent = `${currentFilters.max_calories} kkal`;
    } else {
      sliderCalories.value = 2000;
      valCalories.textContent = 'Tanpa Batas';
    }

    if (currentFilters.min_nutrition_score) {
      sliderNutrition.value = currentFilters.min_nutrition_score;
      valNutrition.textContent = currentFilters.min_nutrition_score;
    } else {
      sliderNutrition.value = 0;
      valNutrition.textContent = 'Tanpa Batas';
    }

    btnFilterToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = filterOverlay.style.display === 'block';
      filterOverlay.style.display = isOpen ? 'none' : 'block';
      if (!isOpen) {
        btnFilterToggle.classList.add('btn-primary');
        btnFilterToggle.classList.remove('btn-secondary');
      } else {
        btnFilterToggle.classList.remove('btn-primary');
        btnFilterToggle.classList.add('btn-secondary');
      }
    });

    document.addEventListener('click', (e) => {
      if (filterOverlay && !filterOverlay.contains(e.target) && e.target !== btnFilterToggle) {
        filterOverlay.style.display = 'none';
        btnFilterToggle.classList.remove('btn-primary');
        btnFilterToggle.classList.add('btn-secondary');
      }
    });

    sliderCalories.addEventListener('input', () => {
      const val = parseInt(sliderCalories.value, 10);
      valCalories.textContent = val === 2000 ? 'Tanpa Batas' : `${val} kkal`;
    });

    sliderNutrition.addEventListener('input', () => {
      const val = parseInt(sliderNutrition.value, 10);
      valNutrition.textContent = val === 0 ? 'Tanpa Batas' : val;
    });

    btnFilterReset.addEventListener('click', () => {
      sliderCalories.value = 2000;
      valCalories.textContent = 'Tanpa Batas';
      sliderNutrition.value = 0;
      valNutrition.textContent = 'Tanpa Batas';
      
      state.resetFilters();
      filterOverlay.style.display = 'none';
      btnFilterToggle.classList.remove('btn-primary');
      btnFilterToggle.classList.add('btn-secondary');
      
      loadRecommendations();
    });

    btnFilterApply.addEventListener('click', () => {
      const maxC = parseInt(sliderCalories.value, 10);
      const minN = parseInt(sliderNutrition.value, 10);
      
      state.activeFilters = {
        max_calories: maxC === 2000 ? null : maxC,
        min_nutrition_score: minN === 0 ? null : minN
      };
      
      filterOverlay.style.display = 'none';
      btnFilterToggle.classList.remove('btn-primary');
      btnFilterToggle.classList.add('btn-secondary');
      
      loadRecommendations();
    });

    async function loadRecommendations() {
      const recsScroll = container.querySelector('#recs-scroll');
      recsScroll.innerHTML = `
        <div style="padding: 20px; color: var(--text-secondary); text-align: center; width: 100%;">
          <i class="ph-bold ph-spinner spinner" style="font-size: 24px; margin-bottom: 8px;"></i>
          <p style="font-size: 13px;">Menghitung ulang rekomendasi...</p>
        </div>
      `;

      try {
        const filters = state.activeFilters;
        const res = await api.postRecommend(user.user_id, 15, filters);
        state.recommendations = res.recommendations;
        renderRecommendationsList(res.recommendations);
      } catch (err) {
        recsScroll.innerHTML = `
          <div style="padding: 20px; color: var(--pale-red-text); text-align: center; width: 100%;">
            <i class="ph-bold ph-warning-circle" style="font-size: 24px; margin-bottom: 8px;"></i>
            <p style="font-size: 13px;">Gagal memuat rekomendasi: ${err.message}</p>
          </div>
        `;
      }
    }

    function renderRecommendationsList(recs) {
      const recsScroll = container.querySelector('#recs-scroll');
      if (!recs || recs.length === 0) {
        recsScroll.innerHTML = `
          <div style="padding: 20px; color: var(--text-secondary); text-align: center; width: 100%;">
            <i class="ph-bold ph-info" style="font-size: 24px; margin-bottom: 8px;"></i>
            <p style="font-size: 13px;">Tidak ada resep yang cocok dengan filter nutrisi Anda.</p>
          </div>
        `;
        return;
      }

      recsScroll.innerHTML = recs.map(r => renderRecipeCard(r, true)).join('');
      animateStagger('#recs-scroll', '.recipe-card');
    }

    async function loadPopular() {
      const popularScroll = container.querySelector('#popular-scroll');
      try {
        const popular = await api.getPopular(15);
        state.popularRecipes = popular;
        popularScroll.innerHTML = popular.map(r => renderRecipeCard(r, false)).join('');
        animateStagger('#popular-scroll', '.recipe-card');
      } catch (err) {
        popularScroll.innerHTML = `
          <div style="padding: 20px; color: var(--pale-red-text); text-align: center; width: 100%;">
            <i class="ph-bold ph-warning-circle" style="font-size: 24px; margin-bottom: 8px;"></i>
            <p style="font-size: 13px;">Gagal memuat resep populer: ${err.message}</p>
          </div>
        `;
      }
    }

    function renderRecipeCard(recipe, isRec = false) {
      const calories = recipe.calories !== undefined ? recipe.calories : 0;
      const score = recipe.nutrition_score !== undefined ? recipe.nutrition_score : 50.0;
      const ratingHtml = recipe.avg_rating !== undefined && recipe.interaction_count > 0 ? `
        <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px; display: flex; align-items: center; gap: 3px;">
          <i class="ph-fill ph-star" style="color: #F59E0B;"></i>
          <strong>${recipe.avg_rating.toFixed(1)}</strong>
          <span>(${recipe.interaction_count})</span>
        </div>
      ` : '';
      
      const explanationHtml = isRec && recipe.dominant_signal ? `
        <div class="card-explanation">
          ${getSignalBadgeHtml(recipe.dominant_signal)}
        </div>
      ` : '';

      return `
        <div class="recipe-card" data-id="${recipe.recipe_id || recipe.id}">
          <div class="recipe-card-img-placeholder">
            <img src="assets/food_placeholder.png" alt="${recipe.name}" style="width: 100%; height: 100%; object-fit: cover;">
          </div>
          <div class="recipe-card-body">
            ${explanationHtml}
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
            ${ratingHtml}
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

    loadRecommendations();
    loadPopular();
  }
};
