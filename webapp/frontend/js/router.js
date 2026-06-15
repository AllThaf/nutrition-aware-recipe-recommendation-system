import { state } from './state.js?v=2.0.0';

const routes = {
  '/login': () => import('./pages/login.js?v=2.0.0').then(m => m.LoginPage),
  '/': () => import('./pages/dashboard.js?v=2.0.0').then(m => m.DashboardPage),
  '/recipe/:id': () => import('./pages/detail.js?v=2.0.0').then(m => m.DetailPage),
  '/search': () => import('./pages/search.js?v=2.0.0').then(m => m.SearchPage)
};

class Router {
  constructor(appContainer) {
    this.container = appContainer;
    this.currentRoute = null;
    this.currentModule = null;
    
    window.addEventListener('hashchange', () => this.handleRoute());
  }
  
  init() {
    this.handleRoute();
  }
  
  navigate(path) {
    window.location.hash = path;
  }
  
  matchRoute(hash) {
    let path = hash.replace(/^#/, '');
    if (!path.startsWith('/')) {
      path = '/' + path;
    }
    
    const [pathPart, queryPart] = path.split('?');
    const query = {};
    if (queryPart) {
      const searchParams = new URLSearchParams(queryPart);
      for (const [key, val] of searchParams) {
        query[key] = val;
      }
    }
    
    for (const routePath of Object.keys(routes)) {
      const routeRegex = this.pathToRegex(routePath);
      const match = pathPart.match(routeRegex);
      if (match) {
        const params = this.getParams(routePath, match);
        return { routePath, params, query };
      }
    }
    
    return null;
  }
  
  pathToRegex(path) {
    return new RegExp("^" + path.replace(/\//g, "\\/").replace(/:\w+/g, "(.+)") + "$");
  }
  
  getParams(routePath, match) {
    const keys = [...routePath.matchAll(/:(\w+)/g)].map(result => result[1]);
    const values = match.slice(1);
    return Object.fromEntries(keys.map((key, i) => [key, values[i]]));
  }
  
  async handleRoute() {
    const hash = window.location.hash || '#/';
    const match = this.matchRoute(hash);
    
    if (!match) {
      console.warn(`Route not found: ${hash}, redirecting to /`);
      this.navigate('/');
      return;
    }
    
    const isLoggedIn = !!state.currentUser;
    
    if (!isLoggedIn && match.routePath !== '/login') {
      this.navigate('/login');
      return;
    }
    if (isLoggedIn && match.routePath === '/login') {
      this.navigate('/');
      return;
    }
    
    try {
      state.loading = true;
      const getPage = routes[match.routePath];
      const page = await getPage();
      
      if (this.currentModule && typeof this.currentModule.destroy === 'function') {
        this.currentModule.destroy();
      }
      
      this.currentModule = page;
      this.currentRoute = match;
      
      this.container.innerHTML = '';
      await page.render(this.container, match.params, match.query);
      
      window.dispatchEvent(new CustomEvent('page-rendered'));
    } catch (err) {
      console.error('Failed to load page:', err);
      this.container.innerHTML = `
        <div style="padding: 40px; text-align: center; max-width: 500px; margin: 40px auto; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);">
          <i class="ph-bold ph-warning-circle" style="font-size: 48px; color: var(--pale-red-text); margin-bottom: 16px;"></i>
          <h2 style="font-size: 20px; margin-bottom: 8px;">Gagal Memuat Halaman</h2>
          <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 24px;">${err.message}</p>
          <a href="#/" class="btn btn-primary">Kembali ke Beranda</a>
        </div>
      `;
    } finally {
      state.loading = false;
    }
  }
}

export let routerInstance = null;

export function initRouter(appContainer) {
  routerInstance = new Router(appContainer);
  routerInstance.init();
  return routerInstance;
}
