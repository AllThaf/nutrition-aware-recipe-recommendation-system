(() => {
  const API_BASE_URL = "http://localhost:8000";

  const $ = (sel) => document.querySelector(sel);

  const els = {
    form: $("#form-recommend"),
    userId: $("#user_id"),
    topN: $("#top_n"),
    topNValue: $("#topn_value"),
    minNutrition: $("#min_nutrition_score"),
    maxCalories: $("#max_calories"),
    refRecipeId: $("#ref_recipe_id"),

    status: $("#status"),
    loading: $("#loading"),
    error: $("#error"),
    cards: $("#cards"),
    empty: $("#empty"),
    resultMeta: $("#result-meta"),

    statTotalRecipes: $("#stat-total-recipes"),
    statTotalUsers: $("#stat-total-users"),
    statTotalInteractions: $("#stat-total-interactions"),
    statSparsity: $("#stat-sparsity"),

    panelDemo: $("#panel-demo"),
    panelEval: $("#panel-eval"),
    tabDemo: $("#tab-demo"),
    tabEval: $("#tab-eval"),
  };

  function setStatus(msg, isError = false) {
    if (!els.status) return;
    els.status.textContent = msg || "";
    els.status.style.color = isError ? "rgba(255,200,200,0.95)" : "";
  }

  function show(el) {
    if (el) el.hidden = false;
  }
  function hide(el) {
    if (el) el.hidden = true;
  }

  function badgeClassForScore(score, type) {
    if (type === "nutrition") {
      if (score >= 75) return "badge--good";
      if (score >= 55) return "badge--mid";
      return "badge--bad";
    }
    if (score >= 0.66) return "badge--good";
    if (score >= 0.4) return "badge--mid";
    return "badge--bad";
  }

  function clamp(n, a, b) {
    return Math.min(b, Math.max(a, n));
  }

  async function safeJson(res) {
    try {
      return await res.json();
    } catch {
      return null;
    }
  }

  async function fetchStats() {
    const url = `${API_BASE_URL}/stats`;
    const res = await fetch(url, { method: "GET" });
    if (!res.ok) throw new Error(`GET /stats failed (${res.status})`);
    return res.json();
  }

  function mockStats() {
    const totalRecipes = 231637;
    const totalUsers = 74277;
    const totalInteractions = 1132367;
    const sparsity = 1 - totalInteractions / (totalUsers * totalRecipes);
    return {
      total_recipes: totalRecipes,
      total_users: totalUsers,
      total_interactions: totalInteractions,
      sparsity,
    };
  }

  function renderStats(stats) {
    if (!stats) return;
    const fmtInt = (n) => Number(n).toLocaleString();
    els.statTotalRecipes.textContent = fmtInt(stats.total_recipes);
    els.statTotalUsers.textContent = fmtInt(stats.total_users);
    els.statTotalInteractions.textContent = fmtInt(stats.total_interactions);
    els.statSparsity.textContent = `${(stats.sparsity * 100).toFixed(2)}%`;
  }

  function foodcomRecipeNames() {
    return [
      "Slow Cooker Chicken Alfredo",
      "Classic Beef Stroganoff",
      "Garlic Parmesan Roasted Broccoli",
      "Lemon Herb Grilled Salmon",
      "Homemade Chicken Noodle Soup",
      "Vegetarian Chili with Beans",
      "Baked Turkey Meatballs",
      "Spicy Shrimp Tacos",
      "Honey Mustard Glazed Salmon",
      "Chocolate Peanut Butter Oatmeal",
      "Crispy Garlic Chicken Wings",
      "Creamy Mushroom Pasta",
      "Thai Peanut Chicken",
      "Easy Beef Tacos",
      "Roasted Garlic Mashed Potatoes",
      "Fresh Tomato Basil Pasta",
      "Sesame Ginger Beef Bowl",
      "BBQ Chicken Stuffed Peppers",
    ];
  }

  function escapeHtml(s) {
    const str = String(s);
    return str
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatNumber(n, digits = 3) {
    if (typeof n !== "number" || Number.isNaN(n)) return String(n);
    return n.toFixed(digits);
  }

  function scoreBadge({ label, value, type }) {
    const cls = badgeClassForScore(value, type);
    return `
      <div class="badge ${cls}">
        <div class="badge__label">${label}</div>
        <div class="badge__value">${type === "nutrition" ? Math.round(value) : formatNumber(value, 3)}</div>
      </div>
    `;
  }

  function whyLabel(dominant_signal) {
    if (dominant_signal === "CF") return "Dominant signal: Collaborative Filtering";
    if (dominant_signal === "CBF") return "Dominant signal: Content-Based Filtering";
    return "Dominant signal: Nutrition scoring";
  }

  function mockRecommendations({ user_id, top_n, min_nutrition_score, max_calories, ref_recipe_id }) {
    const names = foodcomRecipeNames();
    const seed = Math.abs(parseInt(user_id, 10) || 1);
    const pick = (arr, idx) => arr[(idx + seed) % arr.length];

    const tagsPool = [
      "quick",
      "family-friendly",
      "low-carb-ish",
      "high-protein",
      "comfort food",
      "weeknight",
      "gluten-free-ish",
      "dairy-free-ish",
      "spicy",
      "kid-friendly",
      "meal prep",
      "keto-ish",
      "stovetop",
      "baked",
      "healthy-ish",
      "vegetarian",
      "seafood",
      "beef",
      "chicken",
    ];

    const ingredientTemplates = [
      ["olive oil", "onion", "garlic", "chicken breast", "parmesan", "alfredo sauce"],
      ["lean ground beef", "mushrooms", "sour cream", "beef broth", "egg noodles"],
      ["broccoli", "garlic", "parmesan", "olive oil", "lemon"],
      ["salmon", "lemon", "herbs", "olive oil", "garlic"],
      ["chicken", "carrots", "celery", "noodles", "bay leaf"],
      ["kidney beans", "black beans", "tomatoes", "onion", "chili powder"],
      ["turkey", "breadcrumbs", "egg", "garlic", "parmesan"],
      ["shrimp", "taco seasoning", "lime", "cabbage", "cilantro"],
      ["salmon", "honey", "mustard", "garlic", "soy sauce"],
      ["oats", "cocoa powder", "peanut butter", "banana", "milk"],
      ["chicken wings", "garlic", "butter", "paprika", "salt"],
      ["mushrooms", "pasta", "cream", "garlic", "parmesan"],
      ["chicken", "peanut butter", "soy sauce", "ginger", "lime"],
      ["ground beef", "taco shells", "lettuce", "tomato", "cheddar"],
      ["potatoes", "garlic", "butter", "milk", "parmesan"],
      ["tomatoes", "basil", "garlic", "pasta", "olive oil"],
      ["beef", "sesame oil", "ginger", "soy sauce", "rice"],
      ["chicken", "bell peppers", "bbq sauce", "cheddar", "onion"],
    ];

    const recs = [];

    const makeScores = (k) => {
      const t = (seed + k + (ref_recipe_id ? (ref_recipe_id % 97) : 0)) % 1000;
      const cf_score = 0.3 + (((t % 500) / 500) * 0.5);
      const similarity_score = 0.1 + ((((t * 7) % 500) / 500) * 0.5);
      const nutrition_score = 40 + ((((t * 13) % 500) / 500) * 50);
      return {
        cf_score: clamp(cf_score, 0, 1),
        similarity_score: clamp(similarity_score, 0, 1),
        nutrition_score: clamp(nutrition_score, 0, 100),
      };
    };

    const passes = (scores, calories) => {
      if (typeof min_nutrition_score === "number" && !Number.isNaN(min_nutrition_score)) {
        if (scores.nutrition_score < min_nutrition_score) return false;
      }
      if (typeof max_calories === "number" && !Number.isNaN(max_calories)) {
        if (calories > max_calories) return false;
      }
      return true;
    };

    const plausibleCaloriesFromNutrition = (nutrition_score, idx) => {
      const base = 260 + (idx % 7) * 35;
      const modifier = (90 - nutrition_score) * 2.2;
      return clamp(base + modifier, 80, 920);
    };

    let i = 0;
    while (recs.length < top_n && i < top_n * 12) {
      const id = 100000 + ((seed * 13 + i * 77) % 2000000);
      const name = pick(names, i);
      const minutes = 12 + ((seed + i) % 45);

      const tags = [
        tagsPool[(seed + i * 3) % tagsPool.length],
        tagsPool[(seed + i * 5) % tagsPool.length],
        tagsPool[(seed + i * 7) % tagsPool.length],
      ]
        .filter((v, idx2, arr) => arr.indexOf(v) === idx2)
        .slice(0, 3);

      const ingredients = ingredientTemplates[(seed + i) % ingredientTemplates.length];
      const n_ingredients = ingredients.length + ((seed + i) % 3);

      const scoresBase = makeScores(i);
      const calories = plausibleCaloriesFromNutrition(scoresBase.nutrition_score, i);

      const final_score =
        (0.42 * scoresBase.cf_score +
          0.28 * scoresBase.similarity_score +
          0.30 * (scoresBase.nutrition_score / 100)) * 100;

      const dominant_signal =
        Math.max(scoresBase.cf_score, scoresBase.similarity_score, scoresBase.nutrition_score / 100) === scoresBase.cf_score
          ? "CF"
          : Math.max(scoresBase.cf_score, scoresBase.similarity_score) === scoresBase.similarity_score
            ? "CBF"
            : "Nutrition";

      if (passes(scoresBase, calories)) {
        recs.push({
          rank: recs.length + 1,
          recipe_id: id,
          name,
          minutes,
          tags,
          n_ingredients,
          calories,
          nutrition_score: scoresBase.nutrition_score,
          cf_score: scoresBase.cf_score,
          similarity_score: scoresBase.similarity_score,
          final_score,
          dominant_signal,
        });
      }

      i += 1;
    }

    return recs.slice(0, top_n);
  }

  function renderCards(recommendations) {
    els.cards.innerHTML = "";

    if (!recommendations || recommendations.length === 0) {
      show(els.empty);
      return;
    }
    hide(els.empty);

    for (const r of recommendations) {
      const cf = scoreBadge({ label: "CF Score", value: r.cf_score, type: "cf" });
      const cbf = scoreBadge({ label: "Similarity", value: r.similarity_score, type: "cbf" });
      const nut = scoreBadge({ label: "Nutrition", value: r.nutrition_score, type: "nutrition" });

      const rankPill = `<div class="rankPill">Rank <b>#${r.rank}</b></div>`;
      const finalScore = `
        <div class="finalScore">
          <div class="finalScore__label">Final score</div>
          <div class="finalScore__value">${formatNumber(r.final_score, 2)}</div>
        </div>
      `;

      const why = `
        <div class="why">${whyLabel(r.dominant_signal)}
          <span class="badgeDominant">${escapeHtml(r.dominant_signal)}</span>
        </div>
      `;

      const tagChips = (r.tags || [])
        .slice(0, 4)
        .map((t) => `<span class="chip">${escapeHtml(t)}</span>`)
        .join("");

      const card = `
        <div class="card">
          <div class="card__top">
            <div>
              <div class="card__title">${escapeHtml(r.name)}</div>
              <div class="card__meta">
                <span>${r.minutes} min</span>
                <span>•</span>
                <span>${r.n_ingredients} ingredients</span>
                <span>•</span>
                <span>${Math.round(r.calories)} kcal</span>
              </div>
              <div class="chips">${tagChips}</div>
            </div>
          </div>

          <div class="scoreRow">
            ${cf}
            ${cbf}
            ${nut}
          </div>

          <div class="card__rank">
            ${rankPill}
            ${finalScore}
          </div>

          ${why}
        </div>
      `;

      els.cards.insertAdjacentHTML("beforeend", card);
    }
  }

  function setActiveTab(which) {
    const isDemo = which === "demo";
    els.tabDemo.classList.toggle("active", isDemo);
    els.tabEval.classList.toggle("active", !isDemo);

    if (els.panelDemo) els.panelDemo.hidden = !isDemo;
    if (els.panelEval) els.panelEval.hidden = isDemo;

    if (els.panelDemo) els.panelDemo.setAttribute("aria-hidden", String(!isDemo));
    if (els.panelEval) els.panelEval.setAttribute("aria-hidden", String(isDemo));
  }

  async function postRecommend(payload) {
    const url = `${API_BASE_URL}/recommend`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const body = await safeJson(res);
      const msg = body?.detail || body?.message || `HTTP ${res.status}`;
      throw new Error(`POST /recommend failed: ${msg}`);
    }

    return res.json();
  }

  function renderResultMeta(user_id, top_n) {
    els.resultMeta.textContent = `User #${user_id} • Top-N = ${top_n}`;
  }

  async function onSubmit(e) {
    e.preventDefault();

    hide(els.error);
    hide(els.loading);
    els.cards.innerHTML = "";
    hide(els.empty);

    const user_id_raw = els.userId.value.trim();
    const user_id = parseInt(user_id_raw, 10);
    if (!Number.isFinite(user_id)) {
      els.error.textContent = "Please enter a valid integer user_id.";
      show(els.error);
      return;
    }

    const top_n = parseInt(els.topN.value, 10);
    const minNutrition = els.minNutrition.value.trim() === "" ? null : parseFloat(els.minNutrition.value);
    const maxCalories = els.maxCalories.value.trim() === "" ? null : parseFloat(els.maxCalories.value);
    const refRecipeId = els.refRecipeId.value.trim() === "" ? null : parseInt(els.refRecipeId.value, 10);

    const payload = {
      user_id,
      top_n,
      min_nutrition_score: minNutrition === null || Number.isNaN(minNutrition) ? null : minNutrition,
      max_calories: maxCalories === null || Number.isNaN(maxCalories) ? null : maxCalories,
      ref_recipe_id: refRecipeId === null || Number.isNaN(refRecipeId) ? null : refRecipeId,
    };

    Object.keys(payload).forEach((k) => {
      if (payload[k] === null) delete payload[k];
    });

    renderResultMeta(user_id, top_n);
    setStatus("Requesting recommendations…");
    show(els.loading);

    try {
      const data = await postRecommend(payload);
      hide(els.loading);
      setStatus("Recommendations loaded.");
      renderCards(data.recommendations);
    } catch (err) {
      hide(els.loading);
      setStatus("Backend unavailable — using mock demo results.", true);
      els.error.textContent = `${String(err.message || err)}\n(Showing mock results instead.)`;
      show(els.error);

      const mock = mockRecommendations({
        user_id,
        top_n,
        min_nutrition_score: minNutrition,
        max_calories: maxCalories,
        ref_recipe_id: refRecipeId,
      });
      renderCards(mock);
    }
  }

  function renderEvalChart() {
    const models = ["ALS", "BPR", "SVD", "NCF", "CBF_TFIDF"];
    const hr10 = [0.4654, 0.3643, 0.5140, 0.5201, 0.2312];

    if (window.Chart) {
      const ctx = $("#hr10Chart");
      const ncfIdx = models.indexOf("NCF");
      const colors = models.map((_, i) => (i === ncfIdx ? "rgba(110,168,254,0.95)" : "rgba(230,237,247,0.22)"));

      new window.Chart(ctx, {
        type: "bar",
        data: {
          labels: models,
          datasets: [
            {
              label: "HR@10",
              data: hr10,
              backgroundColor: colors,
              borderColor: colors,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: "rgba(230,237,247,0.75)" },
            },
            y: {
              beginAtZero: true,
              grid: { color: "rgba(255,255,255,0.08)" },
              ticks: { color: "rgba(230,237,247,0.75)" },
            },
          },
        },
      });
    } else {
      $("#hr10Chart").insertAdjacentHTML(
        "afterbegin",
        `<div class="small-muted">Chart.js not loaded. HR@10: ALS 0.4654, BPR 0.3643, SVD 0.5140, NCF 0.5201, CBF_TFIDF 0.2312</div>`
      );
    }
  }

  function bootstrap() {
    // stats
    fetchStats().then(renderStats).catch(() => renderStats(mockStats()));

    // chart
    renderEvalChart();

    setActiveTab("demo");
    els.topNValue.textContent = els.topN.value;

    els.tabDemo?.addEventListener("click", () => setActiveTab("demo"));
    els.tabEval?.addEventListener("click", () => setActiveTab("eval"));

    els.topN?.addEventListener("input", () => {
      els.topNValue.textContent = els.topN.value;
    });

    els.form?.addEventListener("submit", onSubmit);

    $("#btn-load-mock")?.addEventListener("click", () => {
      hide(els.error);
      els.cards.innerHTML = "";
      hide(els.empty);

      const user_id_raw = els.userId.value.trim();
      const user_id = parseInt(user_id_raw, 10);
      const top_n = parseInt(els.topN.value, 10);
      if (!Number.isFinite(user_id)) {
        els.error.textContent = "Please enter a valid integer user_id before loading mock results.";
        show(els.error);
        return;
      }

      const minNutrition = els.minNutrition.value.trim() === "" ? null : parseFloat(els.minNutrition.value);
      const maxCalories = els.maxCalories.value.trim() === "" ? null : parseFloat(els.maxCalories.value);
      const refRecipeId = els.refRecipeId.value.trim() === "" ? null : parseInt(els.refRecipeId.value, 10);

      renderResultMeta(user_id, top_n);
      const mock = mockRecommendations({
        user_id,
        top_n,
        min_nutrition_score: minNutrition,
        max_calories: maxCalories,
        ref_recipe_id: refRecipeId,
      });
      renderCards(mock);
      setStatus("Mock results loaded.");
    });
  }

  bootstrap();
})();

