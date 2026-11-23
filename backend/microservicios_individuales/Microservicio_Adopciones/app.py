from datetime import date

from flask import Flask, jsonify, request
from flask_cors import CORS

import repository
from auth import authenticate_user, create_token, token_required
from config import Config

app = Flask(__name__)
CORS(app)


@app.get("/")
def health():
    return jsonify({
        "servicio": "Microservicio Gestión de Adopciones",
        "puerto": Config.SERVER_PORT,
        "estado": "activo",
    })


@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    usuario = data.get("usuario")
    password = data.get("password")

    if not usuario or not password:
        return jsonify({"error": "usuario y password son obligatorios"}), 400

    user = authenticate_user(usuario, password)
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = create_token(user)
    return jsonify({
        "mensaje": "Inicio de sesión exitoso",
        "token": token,
        "usuario": {
            "id": user["id"],
            "nombre": user["nombre"],
            "usuario": user["usuario"],
            "rol": user["rol"],
        },
    })


@app.get("/api/adopciones/pendientes")
@token_required
def adopciones_pendientes():
    adoptions = repository.get_pending_adoptions()
    return jsonify({
        "total": len(adoptions),
        "adopciones": adoptions,
    })


@app.get("/api/adopciones/<int:adopcion_id>")
@token_required
def adopcion_detalle(adopcion_id):
    adoption = repository.get_adoption_by_id(adopcion_id)
    if not adoption:
        return jsonify({"error": f"No existe la adopción con ID {adopcion_id}"}), 404
    return jsonify(adoption)


@app.post("/api/adopciones")
@token_required
def crear_adopcion():
    data = request.get_json(silent=True) or {}

    required = [
        "usuario_id",
        "mascota_id",
        "motivo",
        "lugar_mascota",
        "personas_casa",
        "experiencia",
        "responsable",
    ]
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        return jsonify({
            "error": f"Campos obligatorios faltantes: {', '.join(missing)}"
        }), 400

    fecha_solicitud = data.get("fecha_solicitud") or date.today().isoformat()

    try:
        adoption_id = repository.create_adoption(
            int(data["usuario_id"]),
            int(data["mascota_id"]),
            fecha_solicitud,
            data["motivo"],
            data["lugar_mascota"],
            int(data["personas_casa"]),
            bool(data.get("tiene_otras_mascotas", False)),
            data["experiencia"],
            data["responsable"],
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Error al crear la solicitud: {str(exc)}"}), 500

    return jsonify({
        "mensaje": "Solicitud de adopción creada correctamente",
        "id": adoption_id,
        "estado": "En revisión",
    }), 201


@app.patch("/api/adopciones/<int:adopcion_id>/estado")
@token_required
def actualizar_estado(adopcion_id):
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return jsonify({"error": "El campo estado es obligatorio"}), 400

    try:
        updated = repository.update_adoption_status(adopcion_id, nuevo_estado)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not updated:
        return jsonify({"error": f"No existe la adopción con ID {adopcion_id}"}), 404

    return jsonify({
        "mensaje": "Estado actualizado correctamente",
        "id": adopcion_id,
        "estado": nuevo_estado,
    })


@app.post("/api/adopciones/<int:adopcion_id>/entrevista")
@token_required
def programar_entrevista(adopcion_id):
    data = request.get_json(silent=True) or {}

    fecha = data.get("fecha")
    hora = data.get("hora")
    modalidad = data.get("modalidad")
    observaciones = data.get("observaciones", "")

    if not fecha or not hora or not modalidad:
        return jsonify({
            "error": "Los campos fecha, hora y modalidad son obligatorios"
        }), 400

    interview_id = repository.schedule_interview(
        adopcion_id,
        fecha,
        hora,
        modalidad,
        observaciones,
    )

    if interview_id is None:
        return jsonify({"error": f"No existe la adopción con ID {adopcion_id}"}), 404

    return jsonify({
        "mensaje": "Entrevista programada correctamente",
        "entrevista_id": interview_id,
        "adopcion_id": adopcion_id,
        "fecha": fecha,
        "hora": hora,
        "modalidad": modalidad,
    }), 201


@app.get("/api/entrevistas/proximas")
@token_required
def entrevistas_proximas():
    interviews = repository.get_upcoming_interviews()
    return jsonify({
        "total": len(interviews),
        "entrevistas": interviews,
    })


if __name__ == "__main__":
    print("--------------------------------------------")
    print("MICROSERVICIO DE ADOPCIONES (REST)")
    print("--------------------------------------------")
    print(f"http://127.0.0.1:{Config.SERVER_PORT}")
    print("Login: POST /auth/login")
    print("--------------------------------------------")
    app.run(
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT,
        debug=True,
    )
