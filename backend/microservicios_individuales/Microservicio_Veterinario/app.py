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
        "servicio": "Microservicio Seguimiento Veterinario",
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


@app.get("/api/mascotas/<int:mascota_id>/historial-veterinario")
@token_required
def historial_veterinario(mascota_id):
    if not repository.pet_exists(mascota_id):
        return jsonify({"error": f"No existe la mascota con ID {mascota_id}"}), 404

    history = repository.get_veterinary_history(mascota_id)
    return jsonify({
        "mascota_id": mascota_id,
        "total": len(history),
        "historial": history,
    })


@app.post("/api/mascotas/<int:mascota_id>/controles")
@token_required
def registrar_control(mascota_id):
    data = request.get_json(silent=True) or {}

    tipo = data.get("tipo")
    descripcion = data.get("descripcion")
    fecha = data.get("fecha") or date.today().isoformat()
    proxima_fecha = data.get("proxima_fecha")
    veterinario = data.get("veterinario")
    observaciones = data.get("observaciones")

    if not tipo or not descripcion:
        return jsonify({
            "error": "Los campos tipo y descripcion son obligatorios"
        }), 400

    control_id = repository.register_control(
        mascota_id,
        tipo,
        descripcion,
        fecha,
        proxima_fecha,
        veterinario,
        observaciones,
    )

    if control_id is None:
        return jsonify({"error": f"No existe la mascota con ID {mascota_id}"}), 404

    return jsonify({
        "mensaje": "Control veterinario registrado correctamente",
        "id": control_id,
        "mascota_id": mascota_id,
        "tipo": tipo,
        "fecha": fecha,
        "proxima_fecha": proxima_fecha,
    }), 201


@app.get("/api/seguimiento/vacunas-pendientes")
@token_required
def vacunas_pendientes():
    items = repository.get_pending_vaccines_and_care()
    return jsonify({
        "total": len(items),
        "mascotas": items,
    })


@app.get("/api/seguimiento/proximos-controles")
@token_required
def proximos_controles():
    dias = request.args.get("dias", default=30, type=int)
    if dias < 1:
        return jsonify({"error": "El parámetro dias debe ser mayor a 0"}), 400

    controls = repository.get_upcoming_controls(dias)
    return jsonify({
        "dias": dias,
        "total": len(controls),
        "controles": controls,
    })


@app.get("/api/seguimiento/resumen/<int:mascota_id>")
@token_required
def resumen_seguimiento(mascota_id):
    summary = repository.get_tracking_summary(mascota_id)
    if not summary:
        return jsonify({"error": f"No existe la mascota con ID {mascota_id}"}), 404
    return jsonify(summary)


@app.get("/api/seguimiento/indicadores")
@token_required
def indicadores():
    return jsonify(repository.get_health_indicators())


if __name__ == "__main__":
    print("--------------------------------------------")
    print("MICROSERVICIO VETERINARIO (REST)")
    print("--------------------------------------------")
    print(f"http://127.0.0.1:{Config.SERVER_PORT}")
    print("Login: POST /auth/login")
    print("--------------------------------------------")
    app.run(
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT,
        debug=True,
    )
