
import os
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client

from config import Config
from utils.auth import (
    authenticate_user,
    create_token,
    token_required,
    hash_password,
)
from utils.database import get_cursor


# =========================================================
# CONFIGURACIÓN DE SUPABASE STORAGE
# =========================================================

BUCKET_NAME = "mascotas"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_supabase_storage():
    """
    Crea el cliente de Supabase utilizando las variables
    de entorno existentes en Vercel.
    """

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_SECRET_KEY en las variables de entorno"
        )

    return create_client(supabase_url, supabase_key)


# =========================================================
# IMPORTAR BLUEPRINTS DE LOS MICROSERVICIOS
# =========================================================

from microservicios.mascotas.routes import mascotas_bp
from microservicios.adopciones.routes import (
    adopciones_bp,
    entrevistas_bp,
)
from microservicios.veterinario.routes import (
    veterinario_mascotas_bp,
    seguimiento_bp,
)
from microservicios.favoritos.routes import favoritos_bp
from microservicios.refugios.routes import refugios_bp
from microservicios.usuarios.routes import usuarios_bp, admin_bp


# =========================================================
# CREACIÓN DE LA APLICACIÓN
# =========================================================

app = Flask(__name__)

# Límite de tamaño de la petición
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE + (1024 * 1024)


# =========================================================
# CONFIGURACIÓN CORS
# =========================================================

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://huellitas-felices-3fz2.vercel.app"
            ]
        }
    },
    supports_credentials=False,
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-API-KEY",
        "x-api-key",
    ],
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
)


# =========================================================
# RUTA PRINCIPAL
# =========================================================

@app.get("/")
def health():
    return jsonify({
        "plataforma": "Huellitas Felices — Plataforma Web de Adopción de Mascotas",
        "servicios": [
            "Gestión y Búsqueda de Mascotas",
            "Gestión de Adopciones y Entrevistas",
            "Seguimiento Veterinario",
            "Favoritos de Usuarios",
            "Gestión de Refugios",
            "Administración del Sistema",
        ],
        "puerto": Config.SERVER_PORT,
        "estado": "activo",
    })


# =========================================================
# SUBIR FOTOGRAFÍAS A SUPABASE STORAGE
# =========================================================

@app.post("/api/upload")
def subir_archivo():
    """
    Recibe una fotografía desde el frontend,
    la almacena en Supabase Storage y devuelve su URL pública.
    """

    if "file" not in request.files and "foto" not in request.files:
        return jsonify({
            "error": "No se envió ningún archivo en la petición"
        }), 400

    file = request.files.get("file") or request.files.get("foto")

    if not file or file.filename == "":
        return jsonify({
            "error": "Nombre de archivo inválido o vacío"
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Formato no permitido. Use JPG, JPEG, PNG, WEBP o GIF"
        }), 400

    extension = file.filename.rsplit(".", 1)[1].lower()

    file_bytes = file.read()

    if not file_bytes:
        return jsonify({
            "error": "El archivo está vacío"
        }), 400

    if len(file_bytes) > MAX_FILE_SIZE:
        return jsonify({
            "error": "La imagen supera el límite de 5 MB"
        }), 400

    try:
        supabase = get_supabase_storage()

        # Nombre único para evitar reemplazar otras fotografías
        filename = f"mascota_{uuid.uuid4().hex}.{extension}"

        # Tipo MIME según la extensión
        content_type = ALLOWED_MIME_TYPES[extension]

        # Subir el archivo al bucket mascotas
        supabase.storage.from_(BUCKET_NAME).upload(
            path=filename,
            file=file_bytes,
            file_options={
                "content-type": content_type,
                "cache-control": "3600",
                "upsert": "false",
            },
        )

        # Obtener la dirección pública de la imagen
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(
            filename
        )

        return jsonify({
            "mensaje": "Fotografía subida exitosamente",
            "url": public_url,
            "filename": filename,
        }), 201

    except Exception as e:
        print(f"ERROR AL SUBIR FOTOGRAFÍA: {str(e)}")

        return jsonify({
            "error": "No se pudo subir la fotografía. Verifica la configuración de Supabase Storage."
        }), 500


# =========================================================
# AUTENTICACIÓN: INICIAR SESIÓN
# =========================================================

@app.post("/auth/login")
@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}

    usuario = (data.get("usuario") or "").strip()
    password = data.get("password") or ""

    if not usuario or not password:
        return jsonify({
            "error": "usuario y password son obligatorios"
        }), 400

    user = authenticate_user(usuario, password)

    if not user:
        return jsonify({
            "error": "Credenciales inválidas"
        }), 401

    if user.get("activo") is False or user.get("activo") == 0:
        return jsonify({
            "error": "Esta cuenta de usuario ha sido desactivada. Comunícate con el administrador."
        }), 403

    token = create_token(user)

    return jsonify({
        "mensaje": "Inicio de sesión exitoso",
        "token": token,
        "usuario": {
            "id": user["id"],
            "nombre": user["nombre"],
            "usuario": user["usuario"],
            "rol": user["rol"],
            "ciudad": user.get("ciudad"),
            "experiencia": user.get("experiencia"),
            "tipo_vivienda": user.get("tipo_vivienda"),
            "refugio_id": user.get("refugio_id"),
            "refugio_nombre": user.get("refugio_nombre"),
        },
    })


# =========================================================
# AUTENTICACIÓN: REGISTRO
# =========================================================

@app.post("/auth/register")
@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}

    nombre = (data.get("nombre") or "").strip()
    usuario = (data.get("usuario") or "").strip()
    password = data.get("password") or ""
    ciudad = (data.get("ciudad") or "Popayán").strip()

    try:
        edad = int(data.get("edad") or 25)
    except (ValueError, TypeError):
        return jsonify({
            "error": "La edad debe ser un número válido"
        }), 400

    tipo_vivienda = data.get("tipo_vivienda") or "Casa"

    def convertir_booleano(valor):
        if isinstance(valor, str):
            return valor.strip().lower() in (
                "true", "1", "si", "sí", "yes"
            )
        return bool(valor)

    tiene_patio = convertir_booleano(
        data.get("tiene_patio", False)
    )

    otras_mascotas = convertir_booleano(
        data.get("otras_mascotas", False)
    )

    tiempo_disponible = data.get("tiempo_disponible") or "Medio"
    experiencia = (
        data.get("experiencia") or "Amante de los animales"
    ).strip()

    preferencia_tipo = data.get("preferencia_tipo") or "Todos"
    preferencia_tamano = data.get("preferencia_tamano") or "Mediano"
    preferencia_edad = data.get("preferencia_edad") or "Joven"

    if not nombre or not usuario or not password:
        return jsonify({
            "error": "nombre, usuario y password son obligatorios"
        }), 400

    try:
        with get_cursor(commit=True) as cursor:

            cursor.execute(
                "SELECT id FROM usuarios WHERE usuario = %s",
                (usuario,)
            )

            if cursor.fetchone():
                return jsonify({
                    "error": "El nombre de usuario ya se encuentra registrado"
                }), 409

            cursor.execute(
                """
                INSERT INTO usuarios (
                    nombre,
                    usuario,
                    password,
                    edad,
                    ciudad,
                    tipo_vivienda,
                    tiene_patio,
                    otras_mascotas,
                    tiempo_disponible,
                    experiencia,
                    preferencia_tipo,
                    preferencia_tamano,
                    preferencia_edad,
                    rol
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, 'adoptante'
                )
                RETURNING id
                """,
                (
                    nombre,
                    usuario,
                    hash_password(password),
                    edad,
                    ciudad,
                    tipo_vivienda,
                    tiene_patio,
                    otras_mascotas,
                    tiempo_disponible,
                    experiencia,
                    preferencia_tipo,
                    preferencia_tamano,
                    preferencia_edad,
                ),
            )

            nuevo_id = cursor.fetchone()["id"]

            cursor.execute(
                """
                SELECT
                    id, nombre, usuario, rol, ciudad, edad,
                    tipo_vivienda, tiene_patio, otras_mascotas,
                    tiempo_disponible, experiencia, preferencia_tipo,
                    preferencia_tamano, preferencia_edad
                FROM usuarios
                WHERE id = %s
                """,
                (nuevo_id,)
            )

            nuevo_usuario = cursor.fetchone()

        return jsonify({
            "mensaje": "Usuario adoptante registrado exitosamente",
            "usuario": nuevo_usuario,
        }), 201

    except Exception as e:
        print(f"ERROR EN REGISTRO: {str(e)}")

        return jsonify({
            "error": f"Error al registrar usuario: {str(e)}"
        }), 500


# =========================================================
# AUTENTICACIÓN: USUARIO ACTUAL
# =========================================================

@app.get("/auth/me")
@app.get("/api/auth/me")
@token_required
def me():
    """Verifica sesión y obtiene información del usuario actual."""

    user = getattr(request, "user", {})

    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, nombre, usuario, rol, ciudad, edad
            FROM usuarios
            WHERE id = %s
            """,
            (user.get("id"),)
        )

        db_user = cursor.fetchone()

    return jsonify({
        "usuario": db_user or user,
        "valido": True,
    })


# =========================================================
# REGISTRAR BLUEPRINTS
# =========================================================

app.register_blueprint(mascotas_bp)
app.register_blueprint(adopciones_bp)
app.register_blueprint(entrevistas_bp)
app.register_blueprint(veterinario_mascotas_bp)
app.register_blueprint(seguimiento_bp)
app.register_blueprint(favoritos_bp)
app.register_blueprint(refugios_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(admin_bp)


# =========================================================
# EJECUCIÓN LOCAL
# =========================================================

if __name__ == "__main__":
    port = Config.SERVER_PORT

    print("==================================================")
    print("  HUELLITAS FELICES — BACKEND UNIFICADO (FLASK)")
    print("==================================================")
    print(f"  Servidor corriendo en: http://localhost:{port}")
    print(f"  Microservicio Mascotas: http://localhost:{port}/api/mascotas")
    print(f"  Microservicio Adopciones: http://localhost:{port}/api/adopciones")
    print(f"  Microservicio Veterinario: http://localhost:{port}/api/seguimiento")
    print(f"  Microservicio Favoritos: http://localhost:{port}/api/favoritos")
    print(f"  Microservicio Refugios: http://localhost:{port}/api/refugios")
    print(f"  Microservicio Usuarios y Admin: http://localhost:{port}/api/usuarios")
    print("==================================================")

    app.run(
        host=Config.SERVER_HOST,
        port=port,
        debug=True,
    )
