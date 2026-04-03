/**
 * BACKYARD RESTO PUB — Cliente API
 * Gestión de JWT, refresh automático y requests al backend.
 */

const API_BASE = 'http://localhost:8000/api';

// ============================================================
// Caché local para resiliencia
// ============================================================

const LocalCache = {
  set(key, value, ttlSeconds = 3600) {
    const item = {
      value,
      expires: Date.now() + ttlSeconds * 1000,
    };
    try {
      localStorage.setItem(`cache_${key}`, JSON.stringify(item));
    } catch (e) {
      console.warn('LocalCache.set error:', e);
    }
  },

  get(key) {
    try {
      const item = JSON.parse(localStorage.getItem(`cache_${key}`) || 'null');
      if (!item) return null;
      if (Date.now() > item.expires) {
        localStorage.removeItem(`cache_${key}`);
        return null;
      }
      return item.value;
    } catch (e) {
      return null;
    }
  },

  clear(key) {
    localStorage.removeItem(`cache_${key}`);
  },

  clearAll() {
    const keys = Object.keys(localStorage).filter(k => k.startsWith('cache_'));
    keys.forEach(k => localStorage.removeItem(k));
  },
};

// Wrapper para cachear GETs automáticamente
async function requestWithCache(method, endpoint, options = {}) {
  // Incluir params en la cache key para que queries diferentes tengan cache diferente
  let cacheKey = `${method}:${endpoint}`;
  if (options.params) {
    const paramStr = new URLSearchParams(options.params).toString();
    if (paramStr) cacheKey += `?${paramStr}`;
  }
  
  const cacheTTL = options.cacheTTL || 300; // 5min por defecto
  const bypassCache = options.bypassCache === true;

  // Si es GET y no bypass, intentar cache
  if (method === 'GET' && !bypassCache) {
    const cached = LocalCache.get(cacheKey);
    if (cached) return cached;
  }

  try {
    const result = await request(method, endpoint, options);
    // Cachear solo GETs exitosos
    if (method === 'GET' && result) {
      LocalCache.set(cacheKey, result, cacheTTL);
    }
    return result;
  } catch (error) {
    // Si falla el GET, intentar cache aunque esté expirado
    if (method === 'GET') {
      const expiredCache = (() => {
        try {
          const item = JSON.parse(localStorage.getItem(`cache_${cacheKey}`) || 'null');
          return item ? item.value : null;
        } catch {
          return null;
        }
      })();
      if (expiredCache) {
        console.warn(`API error, usando cache expirado para ${endpoint}`);
        return expiredCache;
      }
    }
    throw error;
  }
}

// ============================================================
// Almacenamiento de tokens
// ============================================================

const Auth = {
  getAccess()  { return localStorage.getItem('access_token'); },
  getRefresh() { return localStorage.getItem('refresh_token'); },

  setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  },

  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('user_data') || 'null');
    } catch { return null; }
  },

  setUser(data) {
    localStorage.setItem('user_data', JSON.stringify(data));
  },

  isLoggedIn() {
    return !!this.getAccess();
  },

  /** Decodifica el payload del JWT (sin verificar firma) */
  decodeToken(token) {
    try {
      const payload = token.split('.')[1];
      return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    } catch { return null; }
  },

  /** Verifica si el access token está vencido (con 30s de margen) */
  isExpired() {
    const token = this.getAccess();
    if (!token) return true;
    const payload = this.decodeToken(token);
    if (!payload) return true;
    return Date.now() / 1000 > payload.exp - 30;
  },
};

// ============================================================
// Refresh automático
// ============================================================

let _refreshPromise = null;

async function refreshAccessToken() {
  if (_refreshPromise) return _refreshPromise;

  _refreshPromise = (async () => {
    const refresh = Auth.getRefresh();
    if (!refresh) throw new Error('Sin refresh token');

    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });

    if (!res.ok) {
      Auth.clearTokens();
      window.location.href = '/pages/login.html';
      throw new Error('Sesión expirada');
    }

    const data = await res.json();
    Auth.setTokens(data.access, data.refresh);
    return data.access;
  })().finally(() => { _refreshPromise = null; });

  return _refreshPromise;
}

// ============================================================
// Cliente HTTP principal
// ============================================================

async function request(method, endpoint, { body, params, requireAuth = true } = {}) {
  // Construir URL
  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    if (qs) url += `?${qs}`;
  }

  // Refrescar token si está por vencer
  if (requireAuth && Auth.isExpired()) {
    await refreshAccessToken();
  }

  const headers = {};
  if (!(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (requireAuth) {
    const token = Auth.getAccess();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const init = { method, headers };
  if (body != null) {
    init.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  let res = await fetch(url, init);

  // Reintento tras refresh si 401
  if (res.status === 401 && requireAuth) {
    try {
      await refreshAccessToken();
      headers['Authorization'] = `Bearer ${Auth.getAccess()}`;
      res = await fetch(url, { ...init, headers });
    } catch {
      return null;
    }
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const err = new Error(data?.detail || data?.error || `Error ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

// Atajos
const api = {
  get:    (url, opts)  => request('GET',    url, opts),
  post:   (url, body, opts) => request('POST',   url, { body, ...opts }),
  put:    (url, body, opts) => request('PUT',    url, { body, ...opts }),
  patch:  (url, body, opts) => request('PATCH',  url, { body, ...opts }),
  delete: (url, opts)  => request('DELETE',  url, opts),
};

// ============================================================
// Endpoints por módulo
// ============================================================

const AuthAPI = {
  async login(username, password) {
    const data = await request('POST', '/auth/login/', {
      body: { username, password },
      requireAuth: false,
    });
    Auth.setTokens(data.access, data.refresh);
    // Cargar perfil
    const user = await api.get('/auth/perfil/');
    Auth.setUser(user);
    return user;
  },

  async logout() {
    try {
      const refresh = Auth.getRefresh();
      if (refresh) {
        await api.post('/auth/logout/', { refresh });
      }
    } catch { /* ignorar */ }
    Auth.clearTokens();
    window.location.href = '/pages/login.html';
  },
};

const MesasAPI = {
  listar(params)          { return api.get('/mesas/', { params }); },
  detalle(id)             { return api.get(`/mesas/${id}/`); },
  cambiarEstado(id, body) { return api.patch(`/mesas/${id}/estado/`, body); },
  ubicaciones()           { return api.get('/mesas/ubicaciones/'); },
};

const ComandasAPI = {
  listar(params)             { return api.get('/comandas/', { params }); },
  crear(body)                { return api.post('/comandas/', body); },
  detalle(id)                { return api.get(`/comandas/${id}/`); },
  agregarItem(id, body)      { return api.post(`/comandas/${id}/items/`, body); },
  cancelarItem(id, item_id)  { return api.post(`/comandas/${id}/items/${item_id}/cancelar/`, {}); },
  enviarCocina(id)           { return api.post(`/comandas/${id}/enviar-cocina/`, {}); },
  transferir(id, body)       { return api.post(`/comandas/${id}/transferir-mesa/`, body); },
};

const CocinaAPI = {
  pendientes()                      { return api.get('/cocina/'); },
  cambiarEstadoItem(itemId, estado) { return api.patch(`/cocina/items/${itemId}/estado/`, { estado_cocina: estado }); },
  marcarLista(comandaId)            { return api.post(`/cocina/comandas/${comandaId}/lista/`, {}); },
};

const CajaAPI = {
  activa()              { return api.get('/cajas/mi-caja/'); },
  abrir(body)           { return api.post('/cajas/abrir/', body); },
  cerrar(id, body)      { return api.post(`/cajas/${id}/cerrar/`, body); },
  movimiento(id, body)  { return api.post(`/cajas/${id}/movimientos/`, body); },
  historial(params)     { return api.get('/cajas/', { params }); },
  cobrar(body)          { return api.post('/cajas/cobrar/', body); },
};

const CatalogoAPI = {
  categorias()       { return api.get('/catalogo/categorias/'); },
  productos(params)  { return api.get('/catalogo/productos/', { params }); },
  menuPublico()      { return api.get('/catalogo/menu/', { requireAuth: false }); },
};

const ReportesAPI = {
  resumen(params)          { return api.get('/reportes/resumen/', { params }); },
  ventasPorDia(params)     { return api.get('/reportes/ventas-por-dia/', { params }); },
  ventasPorProducto(params){ return api.get('/reportes/ventas-por-producto/', { params }); },
  stock()                  { return api.get('/reportes/stock/'); },
  caja(params)             { return api.get('/reportes/movimientos-caja/', { params }); },
};

const ReservasAPI = {
  listar(params)  { return api.get('/reservas/', { params }); },
  crear(body)     { return api.post('/reservas/', body); },
  confirmar(id)   { return api.post(`/reservas/${id}/confirmar/`, {}); },
  cancelar(id)    { return api.post(`/reservas/${id}/cancelar/`, {}); },
};

const EventosAPI = {
  listar()              { return api.get('/eventos/publicos/', { requireAuth: false }); },
  detalle(id)           { return api.get(`/eventos/publicos/${id}/`, { requireAuth: false }); },
  comprar(id, body)     { return api.post(`/eventos/${id}/comprar/`, body, { requireAuth: false }); },
  validarQR(body)       { return api.post('/eventos/validar/', body); },
  adminListar()         { return api.get('/eventos/'); },
};

const PedidosAPI = {
  listar(params)  { return api.get('/pedidos/', { params }); },
  detalle(id)     { return api.get(`/pedidos/${id}/`); },
  estado(id, body){ return api.post(`/pedidos/${id}/estado/`, body); },
};

const FacturacionAPI = {
  emitir(body)    { return api.post('/facturacion/emitir/', body); },
};

// ============================================================
// Helpers UI
// ============================================================

const UI = {
  /** Muestra un toast */
  toast(msg, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container') ||
      (() => {
        const el = document.createElement('div');
        el.id = 'toast-container';
        el.className = 'toast-container-pos';
        document.body.appendChild(el);
        return el;
      })();

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast-pos ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
      <span class="toast-msg">${msg}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'toastIn .3s ease reverse';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  /** Spinner en un botón mientras espera */
  async withLoading(btn, fn) {
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-pos" style="width:16px;height:16px;border-width:2px;"></span>';
    try {
      return await fn();
    } finally {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  },

  /** Formato moneda UYU */
  moneda(val) {
    return new Intl.NumberFormat('es-UY', {
      style: 'currency', currency: 'UYU', minimumFractionDigits: 0,
    }).format(val ?? 0);
  },

  /** Formato fecha/hora */
  fechaHora(iso) {
    if (!iso) return '—';
    return new Intl.DateTimeFormat('es-UY', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    }).format(new Date(iso));
  },

  /** Tiempo transcurrido desde un ISO string */
  tiempoDesde(iso) {
    if (!iso) return '';
    const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
  },

  /** Confirma acción destructiva */
  confirm(msg) {
    return window.confirm(msg);
  },
};

// ============================================================
// Guard de autenticación
// ============================================================

function requireLogin() {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/pages/login.html';
    return false;
  }
  // Si hay token pero no hay datos de usuario, forzar re-login
  if (!Auth.getUser()) {
    Auth.clearTokens();
    window.location.href = '/pages/login.html';
    return false;
  }
  return true;
}

function requireRol(...roles) {
  if (!requireLogin()) return false;
  const user = Auth.getUser();
  const userRol = user?.rol?.toLowerCase();
  if (!userRol || !roles.includes(userRol)) {
    UI.toast('No tenés permiso para acceder a esta sección', 'error');
    setTimeout(() => history.back(), 1500);
    return false;
  }
  return true;
}

// ============================================================
// Layout compartido: renderizar topbar + sidebar dinámicamente
// ============================================================

function renderLayout({ title = '', activeLink = '' } = {}) {
  const user = Auth.getUser() || {};
  const iniciales = ((user.first_name?.[0] || '') + (user.last_name?.[0] || '')).toUpperCase() || user.username?.[0]?.toUpperCase() || '?';
  const rolLabel = {
    administrador: 'Administrador',
    supervisor: 'Supervisor',
    cajero: 'Cajero',
    mozo: 'Mozo',
    cocina: 'Cocina',
    cliente: 'Cliente',
  }[user.rol?.toLowerCase()] || user.rol || '';

  const links = [
    { href: 'mesas.html',     icon: '🪑', label: 'Mesas',      key: 'mesas',      roles: ['administrador','supervisor','mozo','cajero'] },
    { href: 'comandas.html',  icon: '🧾', label: 'Comandas',   key: 'comandas',   roles: ['administrador','supervisor','mozo','cajero'] },
    { href: 'cocina.html',    icon: '👨‍🍳', label: 'Cocina',     key: 'cocina',     roles: ['administrador','supervisor','cocina'] },
    { href: 'caja.html',      icon: '💰', label: 'Caja',       key: 'caja',       roles: ['administrador','supervisor','cajero'] },
    { href: 'pedidos.html',   icon: '📦', label: 'Pedidos',    key: 'pedidos',    roles: ['administrador','supervisor','cajero'] },
    { href: 'reservas.html',  icon: '📅', label: 'Reservas',   key: 'reservas',   roles: ['administrador','supervisor','mozo','cajero'] },
    { href: 'dashboard.html', icon: '📊', label: 'Reportes',   key: 'dashboard',  roles: ['administrador','supervisor'] },
    { href: 'inventario.html',icon: '📋', label: 'Inventario', key: 'inventario', roles: ['administrador','supervisor'] },
    { href: 'eventos.html',   icon: '🎉', label: 'Eventos',    key: 'eventos',    roles: ['administrador','supervisor'] },
  ];

  const navLinks = links
    .filter(l => !user.rol || l.roles.includes(user.rol?.toLowerCase()))
    .map(l => `
      <a href="${l.href}" class="sidebar-link ${activeLink === l.key ? 'active' : ''}">
        <span class="nav-icon">${l.icon}</span>
        <span>${l.label}</span>
        <span class="badge-count" id="badge-${l.key}"></span>
      </a>
    `).join('');

  document.body.innerHTML = `
    <div class="app-wrapper">
      <nav class="sidebar">
        <div class="sidebar-brand">
          <div class="brand-logo">B</div>
          <div class="brand-text">
            <div class="brand-name">Backyard</div>
            <div class="brand-sub">Resto Pub POS</div>
          </div>
        </div>

        <div class="sidebar-section">
          <div class="sidebar-section-title">Operación</div>
          ${navLinks}
        </div>

        <div class="sidebar-footer">
          <button class="sidebar-link" onclick="AuthAPI.logout()" style="color:var(--mesa-ocupada)">
            <span class="nav-icon">🚪</span>
            <span>Cerrar sesión</span>
          </button>
        </div>
      </nav>

      <div class="main-area">
        <header class="topbar">
          <span class="topbar-title" id="topbar-title">${title}</span>
          <div class="topbar-actions">
            <div id="topbar-extra"></div>
            <div class="topbar-user">
              <div class="topbar-avatar">${iniciales}</div>
              <div class="topbar-user-info">
                <div class="topbar-user-name">${user.first_name || user.username || 'Usuario'}</div>
                <div class="topbar-user-role">${rolLabel}</div>
              </div>
            </div>
          </div>
        </header>

        <main class="content-area" id="content-area">
          <div style="display:flex;align-items:center;justify-content:center;height:200px;">
            <div class="spinner-pos" style="width:36px;height:36px;"></div>
          </div>
        </main>
      </div>
    </div>
    <div id="toast-container" class="toast-container-pos"></div>
    <div id="modal-container"></div>
  `;
}
