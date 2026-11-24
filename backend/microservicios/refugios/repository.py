
from utils.database import get_cursor, serialize_row, serialize_rows


def get_all_shelters():
    query = """
        SELECT
            r.id,
            r.nombre,
            r.ciudad,
            r.direccion,
            r.telefono,
            r.email,
            u.id AS usuario_id,
            u.usuario AS usuario_username,
            u.nombre AS usuario_nombre,
            COUNT(DISTINCT m.id) AS total_mascotas,
            COUNT(DISTINCT m.id) FILTER (
                WHERE m.estado = 'Disponible'
            ) AS mascotas_disponibles,
            COUNT(DISTINCT m.id) FILTER (
                WHERE m.estado = 'Adoptada'
            ) AS mascotas_adoptadas
        FROM refugios r
        LEFT JOIN usuarios u ON u.refugio_id = r.id
        LEFT JOIN mascotas m ON m.refugio_id = r.id
        GROUP BY r.id, u.id
        ORDER BY r.id ASC
    """

    with get_cursor() as cursor:
        cursor.execute(query)
        return serialize_rows(cursor.fetchall())


def get_shelter_by_id(refugio_id):
    query = """
        SELECT
            r.id,
            r.nombre,
            r.ciudad,
            r.direccion,
            r.telefono,
            r.email,
            u.id AS usuario_id,
            u.usuario AS usuario_username,
            u.nombre AS usuario_nombre
        FROM refugios r
        LEFT JOIN usuarios u ON u.refugio_id = r.id
        WHERE r.id = %s
        LIMIT 1
    """

    with get_cursor() as cursor:
        cursor.execute(query, (refugio_id,))
        return serialize_row(cursor.fetchone())


def get_shelter_by_user_id(usuario_id):
    query = """
        SELECT
            r.id,
            r.nombre,
            r.ciudad,
            r.direccion,
            r.telefono,
            r.email,
            u.id AS usuario_id,
            u.usuario AS usuario_username,
            u.nombre AS usuario_nombre
        FROM usuarios u
        INNER JOIN refugios r ON u.refugio_id = r.id
        WHERE u.id = %s
        LIMIT 1
    """

    with get_cursor() as cursor:
        cursor.execute(query, (usuario_id,))
        return serialize_row(cursor.fetchone())


def create_shelter(data):
    nombre = (data.get("nombre") or "").strip()
    ciudad = (data.get("ciudad") or "").strip()
    direccion = data.get("direccion", "")
    telefono = data.get("telefono", "")
    email = data.get("email", "")
    usuario_id = data.get("usuario_id") or None

    if not nombre or not ciudad:
        raise ValueError("El nombre y la ciudad del refugio son obligatorios")

    with get_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO refugios (nombre, ciudad, direccion, telefono, email)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (nombre, ciudad, direccion, telefono, email),
        )

        new_id = cursor.fetchone()["id"]

        if usuario_id:
            cursor.execute(
                """
                UPDATE usuarios
                SET refugio_id = %s
                WHERE id = %s
                """,
                (new_id, usuario_id),
            )

        return new_id


def update_shelter(refugio_id, data):
    allowed_fields = [
        "nombre",
        "ciudad",
        "direccion",
        "telefono",
        "email",
    ]

    fields = []
    params = []

    for key in allowed_fields:
        if key in data:
            fields.append(f"{key} = %s")
            params.append(data[key])

    usuario_id = data.get("usuario_id")

    with get_cursor(commit=True) as cursor:
        updated = False

        if fields:
            params.append(refugio_id)

            query = f"""
                UPDATE refugios
                SET {', '.join(fields)}
                WHERE id = %s
            """

            cursor.execute(query, tuple(params))
            updated = cursor.rowcount > 0

        if "usuario_id" in data:
            cursor.execute(
                """
                UPDATE usuarios
                SET refugio_id = NULL
                WHERE refugio_id = %s
                """,
                (refugio_id,),
            )

            if usuario_id:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET refugio_id = %s
                    WHERE id = %s
                    """,
                    (refugio_id, usuario_id),
                )

            updated = updated or cursor.rowcount > 0

        return updated


def get_shelter_dashboard(refugio_id):
    with get_cursor() as cursor:

        # Total de mascotas
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM mascotas
            WHERE refugio_id = %s
            """,
            (refugio_id,),
        )
        total_mascotas = cursor.fetchone()["total"]

        # Mascotas disponibles
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM mascotas
            WHERE refugio_id = %s AND estado = 'Disponible'
            """,
            (refugio_id,),
        )
        disponibles = cursor.fetchone()["total"]

        # Mascotas adoptadas
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM mascotas
            WHERE refugio_id = %s AND estado = 'Adoptada'
            """,
            (refugio_id,),
        )
        adoptadas = cursor.fetchone()["total"]

        # Mascotas en proceso
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM mascotas
            WHERE refugio_id = %s
            AND estado IN ('En revisión', 'Entrevista', 'Proceso')
            """,
            (refugio_id,),
        )
        en_proceso = cursor.fetchone()["total"]

        # Solicitudes pendientes
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM adopciones a
            INNER JOIN mascotas m ON a.mascota_id = m.id
            WHERE m.refugio_id = %s
            AND a.estado IN ('En revisión', 'Entrevista')
            """,
            (refugio_id,),
        )
        solicitudes_pendientes = cursor.fetchone()["total"]

        # Entrevistas programadas
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM entrevistas e
            INNER JOIN adopciones a ON e.adopcion_id = a.id
            INNER JOIN mascotas m ON a.mascota_id = m.id
            WHERE m.refugio_id = %s
            AND e.estado = 'Programada'
            """,
            (refugio_id,),
        )
        entrevistas_programadas = cursor.fetchone()["total"]

        # Distribución de mascotas por tipo
        cursor.execute(
            """
            SELECT tipo, COUNT(*) AS cantidad
            FROM mascotas
            WHERE refugio_id = %s
            GROUP BY tipo
            """,
            (refugio_id,),
        )
        por_tipo = serialize_rows(cursor.fetchall())

        return {
            "mascotas_registradas": total_mascotas,
            "mascotas_disponibles": disponibles,
            "mascotas_en_proceso": en_proceso,
            "mascotas_adoptadas": adoptadas,
            "solicitudes_pendientes": solicitudes_pendientes,
            "entrevistas_programadas": entrevistas_programadas,
            "por_tipo": por_tipo,
        }
