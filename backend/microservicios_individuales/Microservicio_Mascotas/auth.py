import hashlib
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import jsonify, request

from config import Config
from database import get_cursor, serialize_row


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_token(user: dict) -> str:
    payload = {
        "sub": str(user["id"]),
        "usuario": user["usuario"],
        "rol": user["rol"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRES_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        Config.JWT_SECRET,
        algorithms=["HS256"],
        options={"verify_sub": False},
    )


def authenticate_user(usuario: str, password: str):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, nombre, usuario, password, rol, ciudad
            FROM usuarios
            WHERE usuario = %s
            """,
            (usuario,),
        )
        user = cursor.fetchone()

    if not user:
        return None

    if user["password"] != hash_password(password):
        return None

    return serialize_row(user)


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token no proporcionado"}), 401

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        request.user = payload
        return fn(*args, **kwargs)

    return wrapper
