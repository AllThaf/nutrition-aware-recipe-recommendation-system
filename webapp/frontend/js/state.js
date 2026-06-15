const savedUser = sessionStorage.getItem('nutricook_user');

const internalState = {
  currentUser: savedUser ? JSON.parse(savedUser) : null,
  recommendations: [],
  popularRecipes: [],
  history: [],
  stats: null,
  activeFilters: {
    top_n: 10,
    min_nutrition_score: null,
    max_calories: null
  },
  loading: false
};

const listeners = {};

export const state = {
  // Getters
  get currentUser() { return internalState.currentUser; },
  get recommendations() { return internalState.recommendations; },
  get popularRecipes() { return internalState.popularRecipes; },
  get history() { return internalState.history; },
  get stats() { return internalState.stats; },
  get activeFilters() { return internalState.activeFilters; },
  get loading() { return internalState.loading; },

  // Setters with dispatch
  set currentUser(value) {
    internalState.currentUser = value;
    if (value) {
      sessionStorage.setItem('nutricook_user', JSON.stringify(value));
    } else {
      sessionStorage.removeItem('nutricook_user');
      // Clear user data on logout
      internalState.recommendations = [];
      internalState.popularRecipes = [];
      internalState.history = [];
      internalState.activeFilters = {
        top_n: 10,
        min_nutrition_score: null,
        max_calories: null
      };
    }
    this.dispatch('currentUser', value);
  },

  set recommendations(value) {
    internalState.recommendations = value;
    this.dispatch('recommendations', value);
  },

  set popularRecipes(value) {
    internalState.popularRecipes = value;
    this.dispatch('popularRecipes', value);
  },

  set history(value) {
    internalState.history = value;
    this.dispatch('history', value);
  },

  set stats(value) {
    internalState.stats = value;
    this.dispatch('stats', value);
  },

  set activeFilters(value) {
    internalState.activeFilters = { ...internalState.activeFilters, ...value };
    this.dispatch('activeFilters', internalState.activeFilters);
  },

  set loading(value) {
    internalState.loading = value;
    this.dispatch('loading', value);
  },

  // Reset filter values
  resetFilters() {
    internalState.activeFilters = {
      top_n: 10,
      min_nutrition_score: null,
      max_calories: null
    };
    this.dispatch('activeFilters', internalState.activeFilters);
  },

  // Event dispatching
  subscribe(key, callback) {
    if (!listeners[key]) {
      listeners[key] = [];
    }
    listeners[key].push(callback);
    
    // Call immediately with current value if exists
    if (internalState[key] !== undefined) {
      callback(internalState[key]);
    }
    
    // Return unsubscribe function
    return () => {
      listeners[key] = listeners[key].filter(cb => cb !== callback);
    };
  },

  dispatch(key, value) {
    if (listeners[key]) {
      listeners[key].forEach(callback => callback(value));
    }
  }
};
