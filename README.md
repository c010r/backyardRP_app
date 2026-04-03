# BackyardRP POS System v1.0.1

Sistema de Punto de Venta (POS) moderno para restaurantes y bares con gestión de mesas, comandas, inventario y reportes.

## 📁 Estructura del Proyecto

```
/
├── backend/          # API Django REST Framework
├── frontend/         # Frontend vanilla JavaScript
└── README.md         # Este archivo
```

## 🚀 Inicio Rápido

### Backend (Django)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

### Frontend

```bash
cd frontend
python3 -m http.server 80
# O con Python 2
python -m SimpleHTTPServer 80
```

Luego accede a `http://localhost` en tu navegador.

## ✨ Características Principales

### 🍽️ Gestión de Mesas
- Vista en tiempo real de mesas ocupadas/libres
- Asignación de mozo a mesa
- Estados visuales intuitivos

### 📝 Comandas
- Creación y seguimiento de comandas
- Estados: Abierta → En Cocina → Lista → Pagada
- Historial de cambios
- Filtros por estado

### 💳 Caja y Pagos
- Cobro de mesas
- Movimientos de caja (ingresos/egresos)
- Fotografía opcional de recibos
- Cierre de caja con validaciones

### 📊 Inventario
- Gestión de productos
- Control de stock
- Categorías y subcategorías

### �� Caché Local
- Resiliencia offline
- Sincronización automática con servidor
- TTL configurable

### 🔐 Seguridad
- Autenticación JWT
- Control de roles (administrador, supervisor, cajero, mozo, cocina, cliente)
- Permisos granulares

## 🛠️ Tecnologías

**Backend:**
- Django 4.2
- Django REST Framework
- SimpleJWT (JWT authentication)
- SQLite (desarrollo) / PostgreSQL (producción)
- Pillow (manejo de imágenes)

**Frontend:**
- Vanilla JavaScript (ES6+)
- FormData API
- LocalStorage para caché
- CSS moderno

## 🔧 Configuración

### Backend (development)

El archivo de configuración está en `backend/config/settings/development.py`:

```python
ALLOWED_HOSTS = ['*']
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_desarrollo.sqlite3',
    }
}
```

### Frontend

Las rutas de API se configuran en `frontend/assets/js/api.js`:

```javascript
const API_URL = 'http://localhost:8001/api';
```

## 📚 API Endpoints

### Autenticación
- `POST /api/token/` - Obtener JWT
- `POST /api/token/refresh/` - Refrescar token

### Mesas
- `GET /api/mesas/` - Listar mesas
- `GET /api/mesas/{id}/` - Detalle de mesa
- `PATCH /api/mesas/{id}/` - Actualizar mesa

### Comandas
- `GET /api/comandas/` - Listar comandas
- `POST /api/comandas/` - Crear comanda
- `GET /api/comandas/{id}/` - Detalle
- `PATCH /api/comandas/{id}/` - Actualizar estado

### Caja
- `GET /cajas/mi-caja/` - Mi caja actual
- `POST /api/cajas/cobrar/` - Cobrar comanda
- `POST /api/cajas/cerrar/` - Cerrar caja

## 🚦 Estados de Comanda

- **ABIERTA**: Esperando agregar productos
- **EN_COCINA**: Enviada a cocina
- **LISTA**: Productos listos
- **PAGADA**: Comanda cobrada
- **CERRADA**: Archivada (sin volver a usar)

## 🔄 Cache System

El sistema implementa caché local con TTL:

```javascript
// Carga con caché (30 segundos)
const data = await requestWithCache('GET', '/api/mesas/', {
  cacheTTL: 30,
});

// Fuerza actualización del servidor
const data = await requestWithCache('GET', '/api/mesas/', {
  bypassCache: true,
});
```

## 📝 Turnos

- Un turno comienza al abrir caja
- Las comandas se aíslan por turno
- No se pueden cerrar mesas ocupadas
- Fallback a caché local si hay errores del servidor

## 🧪 Testing

```bash
cd backend
python manage.py test
```

## 📦 Deployment

Ver archivos de configuración:
- `backend/config/settings/production.py`
- `.venv/` - Virtual environment con todas las dependencias

## 📄 Licencia

Propietario - BackyardRP © 2026

## 👥 Autores

- BackyardRP Dev Team

## 📞 Soporte

Para soporte contactar al equipo de desarrollo.

---

**Versión Actual:** 1.0.1  
**Última Actualización:** 2 de Abril de 2026
