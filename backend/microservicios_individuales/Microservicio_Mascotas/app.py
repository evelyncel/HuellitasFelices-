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
        "servicio": "Microservicio Gestión y Búsqueda de Mascotas",
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


@app.get("/api/mascotas/disponibles")
@token_required
def mascotas_disponibles():
    ciudad = request.args.get("ciudad")
    if not ciudad:
        return jsonify({"error": "El parámetro ciudad es obligatorio"}), 400

    pets = repository.search_available_by_city(ciudad)
    return jsonify({
        "ciudad": ciudad,
        "total": len(pets),
        "mascotas": pets,
    })


@app.get("/api/mascotas/filtrar")
@token_required
def mascotas_filtrar():
    tipo = request.args.get("tipo")
    edad_min = request.args.get("edad_min", type=int)
    edad_max = request.args.get("edad_max", type=int)

    if not tipo or edad_min is None or edad_max is None:
        return jsonify({
            "error": "Los parámetros tipo, edad_min y edad_max son obligatorios"
        }), 400

    pets = repository.filter_by_type_and_age(tipo, edad_min, edad_max)
    return jsonify({
        "filtros": {
            "tipo": tipo,
            "edad_min": edad_min,
            "edad_max": edad_max,
        },
        "total": len(pets),
        "mascotas": pets,
    })


@app.post("/api/mascotas/compatibles")
@token_required
def mascotas_compatibles():
    data = request.get_json(silent=True) or {}
    has_children = bool(data.get("tiene_ninos", False))
    has_other_pets = bool(data.get("tiene_otras_mascotas", False))
    preferred_size = data.get("tamano_hogar") or data.get("tamano")

    if not preferred_size:
        return jsonify({
            "error": "El campo tamano_hogar es obligatorio (Pequeno, Mediano o Grande)"
        }), 400

    pets = repository.find_compatible_pets(
        has_children,
        has_other_pets,
        preferred_size,
    )
    return jsonify({
        "criterios": {
            "tiene_ninos": has_children,
            "tiene_otras_mascotas": has_other_pets,
            "tamano_hogar": preferred_size,
        },
        "total": len(pets),
        "mascotas": pets,
    })


@app.post("/api/mascotas/recomendaciones")
@token_required
def mascotas_recomendaciones():
    data = request.get_json(silent=True) or {}

    preferred_type = data.get("tipo", "")
    preferred_size = data.get("tamano", "")
    min_age = data.get("edad_min", 0)
    max_age = data.get("edad_max", 20)
    accepts_children = bool(data.get("acepta_ninos", False))
    accepts_other_pets = bool(data.get("acepta_otras_mascotas", False))

    pets = repository.recommend_pets(
        preferred_type,
        preferred_size,
        int(min_age),
        int(max_age),
        accepts_children,
        accepts_other_pets,
    )
    return jsonify({
        "preferencias": {
            "tipo": preferred_type,
            "tamano": preferred_size,
            "edad_min": min_age,
            "edad_max": max_age,
            "acepta_ninos": accepts_children,
            "acepta_otras_mascotas": accepts_other_pets,
        },
        "total": len(pets),
        "recomendaciones": pets,
    })


@app.get("/api/mascotas/estadisticas")
@token_required
def mascotas_estadisticas():
    stats = repository.get_pet_statistics()
    return jsonify(stats)


@app.get("/api/mascotas/<int:mascota_id>/perfil")
@token_required
def mascota_perfil(mascota_id):
    profile = repository.get_pet_profile(mascota_id)
    if not profile:
        return jsonify({"error": f"No existe la mascota con ID {mascota_id}"}), 404
    return jsonify(profile)


if __name__ == "__main__":
    print("--------------------------------------------")
    print("MICROSERVICIO DE MASCOTAS (REST)")
    print("--------------------------------------------")
    print(f"http://127.0.0.1:{Config.SERVER_PORT}")
    print("Login: POST /auth/login")
    print("--------------------------------------------")
    app.run(
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT,
        debug=True,
    )
