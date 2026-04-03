Usa este contexto como marco permanente del proyecto:

# PROMPT MAESTRO — SISTEMA INTEGRAL PARA RESTO PUB “BACKYARD RESTO PUB”

Actúa como un arquitecto senior de software, desarrollador experto en Django, Django REST Framework, UX/UI, Bootstrap 5, sistemas POS para gastronomía, diseño de APIs REST, modelado relacional con SQLite/PostgreSQL, autenticación JWT, permisos por roles y sistemas empresariales reales para restaurantes, bares y resto pub.

Quiero que me ayudes a construir un sistema integral profesional para **Backyard Resto Pub**, con una **v1 funcional primero** y luego una evolución por fases. El objetivo es desarrollar una plataforma moderna, robusta, escalable y bien estructurada para la gestión interna y externa del negocio.

---

## 1. STACK TECNOLÓGICO OBLIGATORIO

### Backend
- Python
- Django
- Django REST Framework
- SQLite en desarrollo
- PostgreSQL en producción
- JWT para autenticación
- Sin Docker por ahora

### Frontend
- Frontend separado del backend
- Bootstrap 5
- UX/UI inspirada en **Toast POS**
- Modo oscuro obligatorio
- Uso en desktop y tablet
- Diseño rápido, táctil y operativo para resto pub

### Arquitectura general
- Backend API REST centralizada
- Módulos públicos manejados por subdominios
- Módulo interno separado del público

### Subdominios funcionales previstos
- `www` → landing pública
- `menu` → menú público / menú QR
- `reservas` → reservas online
- `pedidos` → pedidos online
- `eventos` → eventos y entradas
- `app` → sistema interno POS / gestión

---

## 2. OBJETIVO DEL SISTEMA

Construir un sistema integral para un resto pub llamado **Backyard Resto Pub**, con:
- operación interna completa
- gestión de caja
- mesas y comandas
- cocina
- reservas
- productos y stock
- clientes
- pedidos online
- menú QR
- eventos y entradas
- reportes
- integraciones externas
- facturación electrónica

Debe quedar preparado para crecer por fases, pero la primera entrega debe ser una **v1 funcional, estable y bien organizada**.

---

## 3. CONDICIONES IMPORTANTES

- Todo el sistema debe estar en **español**
- Los nombres de modelos, campos, serializers, vistas, rutas y textos funcionales deben estar en **español**
- La solución debe estar pensada para código limpio, reutilizable y mantenible
- No usar Django Admin como eje principal del sistema
- La interfaz operativa debe parecerse a Toast POS
- Debe existir bitácora / auditoría de acciones
- Debe existir control de permisos por roles
- Debe priorizarse la experiencia real de uso en operación gastronómica
- Quiero primero una **v1 funcional** y luego mejoras
- No quiero una solución improvisada ni genérica: debe ser un diseño profesional y listo para evolucionar

---

## 4. ROLES DEL SISTEMA

Definir e implementar al menos estos roles:

1. **Administrador del sistema**
   - acceso total

2. **Supervisor / gerente**
   - acceso amplio de supervisión operativa y comercial

3. **Cajero**
   - caja
   - cobros
   - comandas
   - cierres relacionados a su caja

4. **Mozo**
   - mesas
   - comandas
   - gestión de atención

5. **Cocina**
   - ver pedidos
   - cambiar estados de preparación

6. **Cliente**
   - reservas
   - pedidos online
   - visualización de menú
   - compra de entradas
   - funcionalidades públicas

Todos los empleados deben iniciar sesión. Debe existir bitácora de accesos y acciones.

---

## 5. HORARIOS DEL NEGOCIO

El negocio opera en estos horarios:
- jueves de 20:00 a 00:00
- viernes de 21:00 a 02:00
- sábados de 21:00 a 04:00
- domingos de 20:00 a 00:00

No hay turnos por ahora.

---

## 6. REGLAS OPERATIVAS DEL NEGOCIO

- Hay **una caja por cajero**
- Medios de pago:
  - efectivo
  - débito
  - crédito
  - transferencia
  - QR
  - Mercado Pago
- Se registran propinas, especialmente las que no se cobran en efectivo
- Se requiere facturación electrónica
- El delivery es **propio**

---

## 7. MÓDULOS A DESARROLLAR

Quiero que diseñes e implementes la arquitectura contemplando todos estos módulos:

### Internos
- usuarios y autenticación
- roles y permisos
- configuración general
- empleados
- clientes
- caja
- mesas
- ubicaciones de mesas
- comandas
- cocina
- categorías
- productos
- variantes
- extras
- combos
- stock
- materia prima
- recetas
- compras a proveedores
- reservas
- reportes
- auditoría
- facturación electrónica
- integraciones

### Externos / públicos
- landing page
- menú público
- menú QR
- reservas online
- pedidos online
- eventos
- venta de entradas

---

## 8. FUNCIONALIDADES POR MÓDULO

### 8.1 Usuarios y autenticación
Implementar:
- login con JWT
- refresh token
- perfil del usuario autenticado
- permisos por rol
- protección de endpoints
- cambio obligatorio de contraseña en primer acceso para usuarios creados por el sistema
- bitácora de inicio/cierre de sesión

### 8.2 Empleados
Debe manejar:
- datos personales
- documento / cédula
- nombres
- apellidos
- teléfono
- email
- dirección
- cargo / rol
- costo por hora o costo fijo según diseño recomendado
- estado activo/inactivo
- acceso al sistema
- historial de acciones relacionadas

### 8.3 Clientes
Debe manejar:
- datos básicos
- teléfono
- email
- historial de consumo
- reservas
- pedidos
- beneficios futuros
- base para programa de fidelidad

### 8.4 Configuración general
Debe manejar:
- datos del negocio
- horarios
- parámetros globales
- medios de pago
- impuestos
- propinas
- impresoras
- integraciones
- políticas operativas

### 8.5 Categorías y productos
Debe manejar:
- categorías
- productos
- descripción
- precio costo
- precio venta
- disponibilidad
- imagen
- variantes
- extras
- combos
- historial de precios
- visibilidad en menú público
- visibilidad en pedidos online
- visibilidad en salón

### 8.6 Inventario
Debe manejar:
- materia prima
- unidades de medida
- stock actual
- stock mínimo
- recetas por producto
- descuento automático por venta
- movimientos de stock
- ajustes manuales
- proveedores
- compras
- costo actualizado
- alertas de bajo stock

### 8.7 Mesas y ubicaciones
Debe manejar:
- ubicaciones
- mesas
- capacidad
- estado
- posición visual
- mover mesas
- cambiar mesa de ubicación
- drag & drop
- colores por estado
- vista tipo mapa operativo

### 8.8 Comandas
Debe manejar:
- apertura
- detalle
- agregar productos
- quitar productos
- editar cantidades
- observaciones
- enviar a cocina
- dividir cuenta
- transferir comanda
- cierre
- asociación con mesa
- asociación con mozo
- asociación con caja y pago

### 8.9 Cocina
Debe manejar:
- panel en tiempo real
- pedidos pendientes
- en preparación
- listos
- entregados
- prioridad visual
- auto refresh
- observaciones
- filtros

### 8.10 Caja
Debe manejar:
- apertura de caja
- cierre de caja
- una caja por cajero
- movimientos de ingreso/egreso
- cobro de comandas
- arqueo
- diferencias
- registro de propinas
- historial de cierres

### 8.11 Reservas
Debe manejar:
- reservas web
- reservas internas
- disponibilidad por fecha/hora
- validación según horarios del negocio
- cantidad de personas
- estado de reserva
- confirmación
- asociación opcional a mesa
- observaciones

### 8.12 Pedidos online
Debe manejar:
- cliente
- carrito
- take away / delivery propio
- estado del pedido
- pago
- seguimiento básico
- asociación a cocina
- asociación a caja si corresponde

### 8.13 Menú QR
Debe manejar:
- visualización pública del menú
- categorías
- productos destacados
- disponibilidad
- posibilidad futura de llamar mozo
- posibilidad futura de pedir cuenta
- posibilidad futura de pedir desde mesa

### 8.14 Eventos y entradas
Debe manejar:
- eventos
- fecha y hora
- cupos
- tipos de entrada
- precios
- estados
- QR de validación
- compra por cliente
- control de acceso futuro

### 8.15 Reportes
Debe manejar:
- ventas por día
- ventas por producto
- ventas por categoría
- ventas por mozo
- movimientos de caja
- cierres
- consumo
- stock
- rentabilidad
- reservas
- clientes
- eventos

### 8.16 Auditoría
Debe manejar:
- registro de acciones relevantes
- usuario
- módulo
- fecha/hora
- tipo de acción
- cambios sensibles
- accesos
- errores operativos importantes

### 8.17 Integraciones
Dejar preparada arquitectura para:
- WhatsApp
- Email
- Mercado Pago
- impresora térmica
- lector QR
- escáner de código de barras
- API de facturación electrónica
- Google Maps

---

## 9. RECOMENDACIÓN DE ARQUITECTURA DEL BACKEND

Quiero que organices el backend de forma modular, escalable y limpia. Recomiendo esta estructura, pero puedes mejorarla si hay una opción superior:

```bash
apps/
  usuarios/
  empleados/
  clientes/
  cajas/
  catalogo/
  inventario/
  mesas/
  comandas/
  cocina/
  reservas/
  pedidos/
  eventos/
  facturacion/
  reportes/
  configuracion/
  auditoria/
  common/

Tarea puntual:
Quiero comenzar por la base del backend.
Crea la estructura inicial del proyecto Django con apps modulares:
usuarios, empleados, configuracion, auditoria, common.

Necesito:
- estructura de carpetas
- settings separados por entorno
- instalación de DRF
- JWT
- modelo de usuario o estrategia recomendada
- permisos base por rol
- urls iniciales
- archivos completos
- explicación breve de cada archivo
- código listo para copiar y pegar