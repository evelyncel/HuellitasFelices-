# Huellitas Felices — Plataforma Web de Adopción de Mascotas

Plataforma completa de adopción y cuidado de mascotas organizada en dos proyectos independientes: **Backend en Flask** (puerto 5000) y **Frontend en Vue.js 3 + Vite** (puerto 5174).

---

## Estructura del Proyecto

```text
huellitasFelices-main/
│
├── backend/                             # Servidor Flask (Puerto 5000)
│   ├── app.py                           # Servidor principal y Blueprints
│   ├── config.py                        # Configuración y variables de entorno
│   ├── requirements.txt                 # Dependencias de Python
│   ├── .env                             # Variables de entorno y conexión a MySQL
│   ├── .env.example
│   ├── utils/                           # Conexión MySQL y seguridad JWT
│   │   ├── database.py
│   │   └── auth.py
│   ├── microservicios/                  # Endpoints modulares (Mascotas, Adopciones, Veterinario)
│   │   ├── mascotas/
│   │   ├── adopciones/
│   │   └── veterinario/
│   └── microservicios_individuales/     # Código original de microservicios preservado
│
├── frontend/                            # Interfaz Web en Vue.js 3 + Vite (Puerto 5174)
│   ├── package.json
│   ├── vite.config.js                   # Configurado en puerto fijo 5174
│   ├── index.html
│   ├── .env
│   └── src/
│       ├── assets/                      # Estilos CSS y diseño cálido
│       ├── components/                  # Navbar, PetCard, Modales de adopción y perfil
│       ├── views/                       # LoginView.vue y HomeView.vue
│       ├── services/                    # Axios con interceptores automáticos
│       ├── stores/                      # Pinia (auth, mascotas, adopciones)
│       └── router/                      # Rutas protegidas con guardia de sesión
│
├── postman/                             # Colección completa de pruebas para Postman
│   └── Huellitas_Felices_API.postman_collection.json
├── huellitas_felices.sql                # Estructura de la base de datos
├── insert.sql                           # Datos iniciales y usuarios de prueba
└── README.md
```

---

## Comandos para Iniciar el Proyecto

Abre **dos terminales independientes** en la carpeta principal `huellitasFelices-main`:

### 🔹 Terminal 1: Iniciar el Backend (Flask)

```bash
cd backend
python app.py
```

> **Servidor Backend activo en:** `http://localhost:5000`

---

### 🔹 Terminal 2: Iniciar el Frontend (Vue + Vite)

```bash
cd frontend
npm run dev
```

> **Plataforma Web activa en:** `http://localhost:5174`

Abre tu navegador en **`http://localhost:5174`** para ver e interactuar con las interfaces.

---

## Cuentas de Prueba Preconfiguradas (MySQL)

Puedes iniciar sesión con cualquiera de estas cuentas:

| Usuario | Contraseña | Rol |
|---|---|---|
| `carlos` | `adoptante123` | Adoptante |
| `maria` | `adoptante123` | Adoptante |
| `juan` | `adoptante123` | Adoptante |
| `laura` | `adoptante123` | Adoptante |
| `admin` | `admin123` | Administrador |

*(En la pantalla de Login también dispones de botones de acceso rápido para autocompletar estas credenciales con un solo clic).*
