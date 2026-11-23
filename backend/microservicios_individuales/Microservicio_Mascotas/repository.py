from database import get_cursor, serialize_row, serialize_rows


PET_COLUMNS = """
    id,
    refugio_id,
    nombre,
    tipo,
    edad,
    sexo,
    tamano,
    raza,
    ciudad,
    descripcion,
    personalidad,
    nivel_energia,
    compatible_ninos,
    compatible_mascotas,
    vacunado,
    desparasitado,
    esterilizado,
    estado
"""


def search_available_by_city(city):
    with get_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {PET_COLUMNS}
            FROM mascotas
            WHERE ciudad = %s
              AND estado = 'Disponible'
            ORDER BY nombre ASC
            """,
            (city,),
        )
        return serialize_rows(cursor.fetchall())


def filter_by_type_and_age(pet_type, min_age, max_age):
    with get_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {PET_COLUMNS}
            FROM mascotas
            WHERE tipo = %s
              AND edad BETWEEN %s AND %s
              AND estado = 'Disponible'
            ORDER BY edad ASC
            """,
            (pet_type, min_age, max_age),
        )
        return serialize_rows(cursor.fetchall())


def find_compatible_pets(has_children, has_other_pets, preferred_size):
    with get_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {PET_COLUMNS}
            FROM mascotas
            WHERE estado = 'Disponible'
              AND tamano = %s
              AND (%s = 0 OR compatible_ninos = 1)
              AND (%s = 0 OR compatible_mascotas = 1)
            ORDER BY nombre ASC
            """,
            (
                preferred_size,
                int(has_children),
                int(has_other_pets),
            ),
        )
        return serialize_rows(cursor.fetchall())


def recommend_pets(
    preferred_type,
    preferred_size,
    min_age,
    max_age,
    accepts_children,
    accepts_other_pets,
):
    with get_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {PET_COLUMNS}
            FROM mascotas
            WHERE estado = 'Disponible'
              AND (%s = '' OR tipo = %s)
              AND (%s = '' OR tamano = %s)
              AND edad BETWEEN %s AND %s
              AND (%s = 0 OR compatible_ninos = 1)
              AND (%s = 0 OR compatible_mascotas = 1)
            ORDER BY edad ASC, nombre ASC
            """,
            (
                preferred_type,
                preferred_type,
                preferred_size,
                preferred_size,
                min_age,
                max_age,
                int(accepts_children),
                int(accepts_other_pets),
            ),
        )
        return serialize_rows(cursor.fetchall())


def get_pet_statistics():
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM mascotas")
        total = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM mascotas WHERE estado = 'Disponible'"
        )
        available = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM mascotas WHERE estado = 'Adoptada'"
        )
        adopted = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM mascotas WHERE tipo = 'Perro'"
        )
        dogs = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM mascotas WHERE tipo = 'Gato'"
        )
        cats = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT tipo, COUNT(*) AS cantidad
            FROM mascotas
            GROUP BY tipo
            ORDER BY tipo
            """
        )
        by_type = serialize_rows(cursor.fetchall())

        cursor.execute(
            """
            SELECT estado, COUNT(*) AS cantidad
            FROM mascotas
            GROUP BY estado
            ORDER BY estado
            """
        )
        by_status = serialize_rows(cursor.fetchall())

        return {
            "total": total,
            "disponibles": available,
            "adoptadas": adopted,
            "perros": dogs,
            "gatos": cats,
            "por_tipo": by_type,
            "por_estado": by_status,
        }


def get_pet_profile(pet_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                m.id,
                m.nombre,
                m.tipo,
                m.edad,
                m.sexo,
                m.tamano,
                m.raza,
                m.ciudad,
                m.descripcion,
                m.personalidad,
                m.nivel_energia,
                m.compatible_ninos,
                m.compatible_mascotas,
                m.vacunado,
                m.desparasitado,
                m.esterilizado,
                m.estado,
                r.id AS refugio_id,
                r.nombre AS refugio_nombre,
                r.ciudad AS refugio_ciudad,
                r.direccion AS refugio_direccion,
                r.telefono AS refugio_telefono,
                r.email AS refugio_email
            FROM mascotas m
            LEFT JOIN refugios r ON m.refugio_id = r.id
            WHERE m.id = %s
            """,
            (pet_id,),
        )
        row = cursor.fetchone()

    if not row:
        return None

    data = serialize_row(row)
    return {
        "mascota": {
            "id": data["id"],
            "nombre": data["nombre"],
            "tipo": data["tipo"],
            "edad": data["edad"],
            "sexo": data["sexo"],
            "tamano": data["tamano"],
            "raza": data["raza"],
            "ciudad": data["ciudad"],
            "descripcion": data["descripcion"],
            "personalidad": data["personalidad"],
            "nivel_energia": data["nivel_energia"],
            "compatible_ninos": data["compatible_ninos"],
            "compatible_mascotas": data["compatible_mascotas"],
            "vacunado": data["vacunado"],
            "desparasitado": data["desparasitado"],
            "esterilizado": data["esterilizado"],
            "estado": data["estado"],
        },
        "refugio": {
            "id": data["refugio_id"],
            "nombre": data["refugio_nombre"],
            "ciudad": data["refugio_ciudad"],
            "direccion": data["refugio_direccion"],
            "telefono": data["refugio_telefono"],
            "email": data["refugio_email"],
        },
    }
