const API_BASE = 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  // Setup headers
  options.headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `HTTP Error ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Request failed for ${endpoint}:`, error);
    // Show user-friendly toast or custom UI error
    window.dispatchEvent(new CustomEvent('api-error', { detail: error.message }));
    throw error;
  }
}

export const api = {
  getStats: () => request('/stats'),
  
  getPersonas: () => request('/users/personas'),
  
  getUserHistory: (userId) => request(`/users/${userId}/history`),
  
  searchRecipes: (query = '', tag = '', limit = 10, offset = 0) => {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (tag) params.append('tag', tag);
    params.append('limit', limit);
    params.append('offset', offset);
    return request(`/recipes/search?${params.toString()}`);
  },
  
  getRecipeDetail: (recipeId) => request(`/recipes/${recipeId}`),
  
  postRecommend: (userId, topN = 10, filters = {}) => {
    const body = {
      user_id: userId,
      top_n: topN
    };
    if (filters.min_nutrition_score !== undefined && filters.min_nutrition_score !== null) {
      body.min_nutrition_score = parseFloat(filters.min_nutrition_score);
    }
    if (filters.max_calories !== undefined && filters.max_calories !== null) {
      body.max_calories = parseFloat(filters.max_calories);
    }
    return request('/recommend', {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },
  
  postInteraction: (userId, recipeId, rating) => {
    return request('/interactions', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        recipe_id: recipeId,
        rating: rating
      })
    });
  },

  login: (userId, password) => {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        user_id: parseInt(userId, 10),
        password: password
      })
    });
  },

  getPopular: (limit = 20) => {
    return request(`/recipes/popular?limit=${limit}`);
  }
};
