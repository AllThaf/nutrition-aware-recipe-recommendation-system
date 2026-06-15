import { api } from '../api.js?v=2.0.0';
import { state } from '../state.js?v=2.0.0';
import { showToast, observeFadeIn } from '../ui.js?v=2.0.0';
import { getNavbarHtml, attachNavbarListeners } from './dashboard.js?v=2.0.0';

let selectedRating = 0;

export const DetailPage = {
  async render(container, params) {
    const recipeId = parseInt(params.id, 10);
    const user = state.currentUser;
    
    if (!user) {
      window.location.hash = '#/login';
      return;
    }

    container.innerHTML = `
      ${getNavbarHtml()}
      
      <main class="detail-content" style="max-width: 1000px; margin: 0 auto; padding: 40px 20px; width: 100%;">
        <!-- Breadcrumbs & Back Button -->
        <div style="margin-bottom: 24px; display: flex; align-items: center; gap: 8px; font-size: 13px;">
          <a href="#/" style="color: var(--text-secondary); display: inline-flex; align-items: center; gap: 4px;">
            <i class="ph-bold ph-arrow-left"></i> Kembali ke Beranda
          </a>
          <span style="color: var(--border);">&middot;</span>
          <span style="color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 300px;" id="recipe-breadcrumb">Resep</span>
        </div>

        <div id="recipe-detail-loading" style="text-align: center; color: var(--text-secondary); padding: 40px 0;">
          <i class="ph-bold ph-spinner spinner" style="font-size: 32px; margin-bottom: 12px;"></i>
          <p>Memuat detail resep...</p>
        </div>

        <div id="recipe-detail-container" style="display: none;">
          <!-- Detail content loaded dynamically -->
        </div>
      </main>
    `;

    attachNavbarListeners(container);

    const loadingDiv = container.querySelector('#recipe-detail-loading');
    const detailDiv = container.querySelector('#recipe-detail-container');

    try {
      const recipe = await api.getRecipeDetail(recipeId);
      selectedRating = 0;

      const cleanName = recipe.name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      
      // Update breadcrumb
      container.querySelector('#recipe-breadcrumb').textContent = cleanName;

      // Build tags
      const tagsHtml = recipe.tags.slice(0, 10).map(tag => `
        <span class="badge" style="background: var(--canvas); color: var(--text-secondary); font-size: 10px; border: 1px solid var(--border); padding: 4px 10px;">
          ${tag}
        </span>
      `).join(' ');

      // Nutrition details
      const nutDetails = recipe.nutrition;
      const nutritionDetails = [
        { name: 'Kalori', value: Math.round(nutDetails.calories), unit: 'kkal', max: 2000, desc: 'Energi dasar harian' },
        { name: 'Lemak Total', value: Math.round(nutDetails.total_fat_pdv), unit: '% DV', max: 100, desc: 'Lemak harian direkomendasikan' },
        { name: 'Gula', value: Math.round(nutDetails.sugar_pdv), unit: '% DV', max: 100, desc: 'Kandungan gula tambahan' },
        { name: 'Sodium', value: Math.round(nutDetails.sodium_pdv), unit: '% DV', max: 100, desc: 'Asupan garam (Sodium)' },
        { name: 'Protein', value: Math.round(nutDetails.protein_pdv), unit: '% DV', max: 100, desc: 'Protein pembangun otot' },
        { name: 'Lemak Jenuh', value: Math.round(nutDetails.saturated_fat_pdv), unit: '% DV', max: 100, desc: 'Lemak jenuh harian' },
        { name: 'Karbohidrat', value: Math.round(nutDetails.carbs_pdv), unit: '% DV', max: 100, desc: 'Karbohidrat harian' }
      ];

      const nutritionListHtml = nutritionDetails.map((nut) => {
        let colorClass = 'fill-high';
        if (nut.name === 'Gula' || nut.name === 'Sodium' || nut.name === 'Lemak Jenuh') {
          if (nut.value > 50) colorClass = 'fill-low';
          else if (nut.value > 25) colorClass = 'fill-medium';
        } else if (nut.name === 'Protein') {
          if (nut.value > 30) colorClass = 'fill-high';
          else if (nut.value > 15) colorClass = 'fill-medium';
          else colorClass = 'fill-low';
        } else {
          if (nut.value > 75) colorClass = 'fill-low';
          else if (nut.value > 40) colorClass = 'fill-medium';
        }

        return `
          <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
              <span><strong>${nut.name}</strong> <span style="font-size: 11px; color: var(--text-secondary);">(${nut.desc})</span></span>
              <span style="font-family: var(--font-mono); font-weight: 600;">${nut.value} ${nut.unit}</span>
            </div>
            <div class="nutrition-track" style="height: 4px; margin-top: 0; margin-bottom: 0;">
              <div class="nutrition-fill ${colorClass}" style="width: ${Math.min(nut.value, 100)}%"></div>
            </div>
          </div>
        `;
      }).join('');

      const recInfo = state.recommendations.find(r => r.recipe_id === recipeId);
      let scoreWidgetHtml = '';
      if (recInfo) {
        scoreWidgetHtml = `
          <div class="card" style="padding: 16px; background: var(--canvas); border-radius: var(--radius-md); margin-bottom: 24px; border: 1px solid var(--border);">
            <h4 style="font-family: var(--font-sans); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 12px;">Analisis Skor Rekomendasi</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: center;">
              <div style="border-right: 1px solid var(--border); padding-right: 6px;">
                <div style="font-family: var(--font-mono); font-size: 14px; font-weight: 700;">${recInfo.cf_score.toFixed(2)}</div>
                <div style="font-size: 10px; color: var(--text-secondary);">CF Score</div>
              </div>
              <div style="border-right: 1px solid var(--border); padding-right: 6px;">
                <div style="font-family: var(--font-mono); font-size: 14px; font-weight: 700;">${recInfo.similarity_score.toFixed(2)}</div>
                <div style="font-size: 10px; color: var(--text-secondary);">CBF Score</div>
              </div>
              <div>
                <div style="font-family: var(--font-mono); font-size: 14px; font-weight: 700; color: var(--pale-green-text);">${recInfo.nutrition_score.toFixed(1)}</div>
                <div style="font-size: 10px; color: var(--text-secondary);">Gizi</div>
              </div>
            </div>
            <hr style="margin: 10px 0; border-color: var(--border);">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
              <span>Sinyal Dominan:</span>
              <strong style="font-family: var(--font-sans); color: var(--text-primary);">${recInfo.dominant_signal === 'CF' ? 'Minat Pengguna (CF)' : recInfo.dominant_signal === 'CBF' ? 'Kemiripan Bahan (CBF)' : 'Nilai Gizi (Nutrition)'}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; margin-top: 4px;">
              <span><strong>Skor Akhir:</strong></span>
              <strong style="font-family: var(--font-mono); font-size: 15px; color: var(--text-primary);">${recInfo.final_score.toFixed(4)}</strong>
            </div>
          </div>
        `;
      }

      const ingredientsHtml = recipe.ingredients.map(ing => `
        <li style="list-style: none; display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; font-size: 14px;">
          <input type="checkbox" style="margin-top: 4px; accent-color: var(--text-primary); cursor: pointer;">
          <span style="cursor: pointer;" onclick="const cb = this.previousElementSibling; cb.checked = !cb.checked;">${ing}</span>
        </li>
      `).join('');

      const stepsHtml = recipe.steps.map((step, idx) => `
        <div style="display: flex; gap: 16px; margin-bottom: 20px; align-items: flex-start;">
          <div style="font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: var(--text-secondary); background: var(--canvas); width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            ${idx + 1}
          </div>
          <p style="margin: 0; font-size: 14px; line-height: 1.6; color: var(--text-primary); flex: 1;">${step}</p>
        </div>
      `).join('');

      detailDiv.innerHTML = `
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 2.2rem; font-family: var(--font-serif); font-weight: 500; margin-bottom: 12px; line-height: 1.2;">${cleanName}</h2>
          <p style="font-size: 14px; color: var(--text-secondary); font-style: italic; line-height: 1.5; margin-bottom: 16px;">
            ${recipe.description || 'Tidak ada deskripsi untuk resep ini.'}
          </p>
          <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 24px;">
            ${tagsHtml}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 32px;">
          <div class="card" style="padding: 16px; text-align: center; border-radius: var(--radius-md);">
            <div style="font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Waktu</div>
            <strong style="font-size: 16px;">${recipe.minutes} Menit</strong>
          </div>
          <div class="card" style="padding: 16px; text-align: center; border-radius: var(--radius-md);">
            <div style="font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Total Bahan</div>
            <strong style="font-size: 16px;">${recipe.n_ingredients} Bahan</strong>
          </div>
          <div class="card" style="padding: 16px; text-align: center; border-radius: var(--radius-md);">
            <div style="font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Kalori</div>
            <strong style="font-size: 16px;">${Math.round(nutDetails.calories)} kkal</strong>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1.2fr; gap: 40px; margin-bottom: 40px;">
          <!-- Left Column: Nutrition & Ingredients -->
          <div>
            ${scoreWidgetHtml}

            <div style="margin-bottom: 32px;">
              <h3 style="font-size: 1.4rem; font-family: var(--font-serif); margin-bottom: 16px;">Profil Gizi</h3>
              <div class="card" style="padding: 20px; border-radius: var(--radius-md);">
                ${nutritionListHtml}
              </div>
            </div>

            <div>
              <h3 style="font-size: 1.4rem; font-family: var(--font-serif); margin-bottom: 16px;">Bahan-bahan</h3>
              <div class="card" style="padding: 20px; border-radius: var(--radius-md);">
                <ul style="padding-left: 0; margin-bottom: 0;">
                  ${ingredientsHtml}
                </ul>
              </div>
            </div>
          </div>

          <!-- Right Column: Cooking Steps & Rating -->
          <div>
            <div style="margin-bottom: 32px;">
              <h3 style="font-size: 1.4rem; font-family: var(--font-serif); margin-bottom: 16px;">Instruksi Memasak</h3>
              <div class="card" style="padding: 24px; border-radius: var(--radius-md);">
                ${stepsHtml}
              </div>
            </div>

            <div class="card" style="padding: 24px; border-radius: var(--radius-md); border-top: 2px solid var(--text-primary);">
              <h3 style="font-size: 1.3rem; font-family: var(--font-serif); margin-bottom: 8px;">Beri Ulasan Resep Ini</h3>
              <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 18px;">
                Berikan rating untuk memperbarui model Collaborative Filtering personalisasi Anda secara dinamis.
              </p>
              
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <div class="rating-stars" id="star-rating-widget">
                  <i class="ph-fill ph-star" data-value="1"></i>
                  <i class="ph-fill ph-star" data-value="2"></i>
                  <i class="ph-fill ph-star" data-value="3"></i>
                  <i class="ph-fill ph-star" data-value="4"></i>
                  <i class="ph-fill ph-star" data-value="5"></i>
                </div>
                <button type="button" class="btn btn-primary" id="btn-submit-rating" disabled style="border-radius: 20px; padding: 8px 20px;">Kirim Rating</button>
              </div>
            </div>
          </div>
        </div>
      `;

      const stars = detailDiv.querySelectorAll('#star-rating-widget i');
      const submitBtn = detailDiv.querySelector('#btn-submit-rating');
      
      stars.forEach(star => {
        star.addEventListener('click', () => {
          const val = parseInt(star.dataset.value, 10);
          selectedRating = val;
          
          stars.forEach((s, i) => {
            if (i < val) {
              s.classList.add('active');
            } else {
              s.classList.remove('active');
            }
          });
          
          submitBtn.removeAttribute('disabled');
        });
      });

      submitBtn.addEventListener('click', async () => {
        if (!selectedRating) return;
        
        submitBtn.setAttribute('disabled', 'true');
        submitBtn.innerHTML = '<i class="ph-bold ph-spinner spinner" style="margin-right: 6px;"></i> Mengirim...';

        try {
          await api.postInteraction(user.user_id, recipeId, selectedRating);
          showToast(`Terima kasih! Ulasan ${selectedRating} bintang berhasil disimpan.`, 'success');
          
          selectedRating = 0;
          stars.forEach(s => s.classList.remove('active'));
          submitBtn.textContent = 'Kirim Rating';
        } catch (err) {
          showToast(`Gagal menyimpan rating: ${err.message}`, 'error');
          submitBtn.removeAttribute('disabled');
          submitBtn.textContent = 'Kirim Rating';
        }
      });

      loadingDiv.style.display = 'none';
      detailDiv.style.display = 'block';

      observeFadeIn(detailDiv);

    } catch (err) {
      console.error('Failed to load recipe detail:', err);
      loadingDiv.innerHTML = `
        <i class="ph-bold ph-warning-circle" style="font-size: 32px; color: var(--pale-red-text); margin-bottom: 12px;"></i>
        <p>Gagal memuat detail resep: ${err.message}</p>
      `;
    }
  }
};
