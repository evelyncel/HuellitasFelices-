
from utils.database import get_cursor, serialize_row, serialize_rows


ESTADOS_VALIDOS = {
    "En revisión",
    "Entrevista",
    "Aprobada",
    "Rechazada",
    "Cancelada",
}


def convertir_booleano(valor):
    """Convierte valores recibidos del frontend a booleanos de Python."""
    if isinstance(valor, bool):
        return valor

    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "1", "si", "sí", "yes")

    if isinstance(valor, (int, float)):
        return valor != 0

    return False


def create_adoption(
    usuario_id,
    mascota_id,
    fecha_solicitud,
    motivo,
    lugar_mascota,
    personas_casa,
    tiene_otras_mascotas,
    experiencia,
    responsable,
):
    tiene_otras_mascotas = convertir_booleano(tiene_otras_mascotas)

    with get_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT id FROM usuarios WHERE id = %s",
            (usuario_id,),
        )

        if not cursor.fetchone():
            raise ValueError(f"No existe el usuario con ID {usuario_id}")

        cursor.execute(
            """
            SELECT id, estado
            FROM mascotas
            WHERE id = %s
            """,
            (mascota_id,),
        )

        pet = cursor.fetchone()

        if not pet:
            raise ValueError(f"No existe la mascota con ID {mascota_id}")

        if pet["estado"] != "Disponible":
            raise ValueError("La mascota no está disponible para adopción")

        cursor.execute(
            """
            SELECT id
            FROM adopciones
            WHERE usuario_id = %s
              AND mascota_id = %s
              AND estado IN ('En revisión', 'Entrevista')
            """,
            (usuario_id, mascota_id),
        )

        if cursor.fetchone():
            raise ValueError(
                "Ya tienes una solicitud activa ('En revisión' o "
                "'Entrevista') para esta mascota"
            )

        cursor.execute(
            """
            INSERT INTO adopciones (
                usuario_id,
                mascota_id,
                fecha_solicitud,
                motivo,
                lugar_mascota,
                personas_casa,
                tiene_otras_mascotas,
                experiencia,
                responsable,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'En revisión')
            RETURNING id
            """,
            (
                usuario_id,
                mascota_id,
                fecha_solicitud,
                motivo,
                lugar_mascota,
                personas_casa,
                tiene_otras_mascotas,
                experiencia,
                responsable,
            ),
        )

        return cursor.fetchone()["id"]


def get_all_adoptions(usuario_id=None, refugio_id=None, estado=None, mascota_id=None):
    query = """
        SELECT
            a.id,
            a.usuario_id,
            u.nombre AS usuario_nombre,
            u.usuario AS usuario_username,
            u.ciudad AS usuario_ciudad,
            a.mascota_id,
            m.nombre AS mascota_nombre,
            m.tipo AS mascota_tipo,
            m.raza AS mascota_raza,
            m.estado AS mascota_estado,
            m.foto_url AS mascota_foto_url,
            r.id AS refugio_id,
            r.nombre AS refugio_nombre,
            a.fecha_solicitud,
            a.motivo,
            a.lugar_mascota,
            a.personas_casa,
            a.tiene_otras_mascotas,
            a.experiencia,
            a.responsable,
            a.estado
        FROM adopciones a
        INNER JOIN usuarios u ON a.usuario_id = u.id
        INNER JOIN mascotas m ON a.mascota_id = m.id
        LEFT JOIN refugios r ON m.refugio_id = r.id
        WHERE 1=1
    """

    params = []

    if usuario_id is not None:
        query += " AND a.usuario_id = %s"
        params.append(usuario_id)

    if refugio_id is not None:
        query += " AND m.refugio_id = %s"
        params.append(refugio_id)

    if estado and estado.lower() != "todos":
        query += " AND LOWER(a.estado) = LOWER(%s)"
        params.append(estado)

    if mascota_id is not None:
        query += " AND a.mascota_id = %s"
        params.append(mascota_id)

    query += " ORDER BY a.fecha_solicitud DESC, a.id DESC"

    with get_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return serialize_rows(cursor.fetchall())


def get_pending_adoptions(refugio_id=None):
    query = """
        SELECT
            a.id,
            a.usuario_id,
            u.nombre AS usuario_nombre,
            u.usuario AS usuario_username,
            a.mascota_id,
            m.nombre AS mascota_nombre,
            m.tipo AS mascota_tipo,
            m.refugio_id,
            r.nombre AS refugio_nombre,
            a.fecha_solicitud,
            a.motivo,
            a.lugar_mascota,
            a.personas_casa,
            a.tiene_otras_mascotas,
            a.experiencia,
            a.responsable,
            a.estado
        FROM adopciones a
        INNER JOIN usuarios u ON a.usuario_id = u.id
        INNER JOIN mascotas m ON a.mascota_id = m.id
        LEFT JOIN refugios r ON m.refugio_id = r.id
        WHERE a.estado IN ('En revisión', 'Entrevista')
    """

    params = []

    if refugio_id is not None:
        query += " AND m.refugio_id = %s"
        params.append(refugio_id)

    query += " ORDER BY a.fecha_solicitud ASC, a.id ASC"

    with get_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return serialize_rows(cursor.fetchall())


def get_adoption_by_id(adoption_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                a.id,
                a.usuario_id,
                u.nombre AS usuario_nombre,
                u.usuario AS usuario_username,
                u.ciudad AS usuario_ciudad,
                u.tipo_vivienda AS usuario_tipo_vivienda,
                u.tiene_patio AS usuario_tiene_patio,
                u.tiempo_disponible AS usuario_tiempo_disponible,
                u.experiencia AS usuario_experiencia_base,
                a.mascota_id,
                m.nombre AS mascota_nombre,
                m.tipo AS mascota_tipo,
                m.edad AS mascota_edad,
                m.tamano AS mascota_tamano,
                m.raza AS mascota_raza,
                m.estado AS mascota_estado,
                m.refugio_id,
                r.nombre AS refugio_nombre,
                r.ciudad AS refugio_ciudad,
                r.telefono AS refugio_telefono,
                r.email AS refugio_email,
                a.fecha_solicitud,
                a.motivo,
                a.lugar_mascota,
                a.personas_casa,
                a.tiene_otras_mascotas,
                a.experiencia,
                a.responsable,
                a.estado
            FROM adopciones a
            INNER JOIN usuarios u ON a.usuario_id = u.id
            INNER JOIN mascotas m ON a.mascota_id = m.id
            LEFT JOIN refugios r ON m.refugio_id = r.id
            WHERE a.id = %s
            """,
            (adoption_id,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        adoption = serialize_row(row)

        cursor.execute(
            """
            SELECT id, fecha, hora, modalidad, observaciones, estado
            FROM entrevistas
            WHERE adopcion_id = %s
            ORDER BY fecha DESC, hora DESC
            """,
            (adoption_id,),
        )

        adoption["entrevistas"] = serialize_rows(cursor.fetchall())

        return adoption


def update_adoption_status(adoption_id, new_status):
    if new_status not in ESTADOS_VALIDOS:
        raise ValueError(
            "Estado inválido. Use: En revisión, Entrevista, Aprobada, "
            "Rechazada o Cancelada"
        )

    with get_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT
                a.id,
                a.mascota_id,
                a.estado AS adopcion_estado,
                m.estado AS pet_estado
            FROM adopciones a
            JOIN mascotas m ON a.mascota_id = m.id
            WHERE a.id = %s
            """,
            (adoption_id,),
        )

        row = cursor.fetchone()

        if not row:
            return False

        mascota_id = row["mascota_id"]
        pet_estado = row["pet_estado"]
        current_status = row["adopcion_estado"]

        if new_status == "Aprobada" and pet_estado == "Adoptada":
            if current_status != "Aprobada":
                raise ValueError(
                    "La mascota ya ha sido adoptada en otro proceso "
                    "y no puede tener múltiples adopciones finalizadas."
                )

        cursor.execute(
            """
            UPDATE adopciones
            SET estado = %s
            WHERE id = %s
            """,
            (new_status, adoption_id),
        )

        if new_status == "Aprobada":
            cursor.execute(
                """
                UPDATE mascotas
                SET estado = 'Adoptada'
                WHERE id = %s
                """,
                (mascota_id,),
            )

            cursor.execute(
                """
                UPDATE adopciones
                SET estado = 'Rechazada'
                WHERE mascota_id = %s
                  AND id != %s
                  AND estado IN ('En revisión', 'Entrevista')
                """,
                (mascota_id, adoption_id),
            )

        return True


def schedule_interview(
    adoption_id,
    interview_date,
    interview_time,
    modality,
    observations,
):
    with get_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT id FROM adopciones WHERE id = %s",
            (adoption_id,),
        )

        if not cursor.fetchone():
            return None

        cursor.execute(
            """
            INSERT INTO entrevistas (
                adopcion_id,
                fecha,
                hora,
                modalidad,
                observaciones,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, 'Programada')
            RETURNING id
            """,
            (
                adoption_id,
                interview_date,
                interview_time,
                modality,
                observations or "",
            ),
        )

        interview_id = cursor.fetchone()["id"]

        cursor.execute(
            """
            UPDATE adopciones
            SET estado = 'Entrevista'
            WHERE id = %s
            """,
            (adoption_id,),
        )

        return interview_id


def get_interviews(usuario_id=None, refugio_id=None, adopcion_id=None, estado=None):
    query = """
        SELECT
            e.id,
            e.adopcion_id,
            e.fecha,
            e.hora,
            e.modalidad,
            e.observaciones,
            e.estado,
            a.usuario_id,
            u.nombre AS usuario_nombre,
            u.usuario AS usuario_username,
            a.mascota_id,
            m.nombre AS mascota_nombre,
            m.tipo AS mascota_tipo,
            m.foto_url AS mascota_foto_url,
            m.refugio_id,
            r.nombre AS refugio_nombre,
            r.ciudad AS refugio_ciudad,
            r.telefono AS refugio_telefono
        FROM entrevistas e
        INNER JOIN adopciones a ON e.adopcion_id = a.id
        INNER JOIN usuarios u ON a.usuario_id = u.id
        INNER JOIN mascotas m ON a.mascota_id = m.id
        LEFT JOIN refugios r ON m.refugio_id = r.id
        WHERE 1=1
    """

    params = []

    if usuario_id is not None:
        query += " AND a.usuario_id = %s"
        params.append(usuario_id)

    if refugio_id is not None:
        query += " AND m.refugio_id = %s"
        params.append(refugio_id)

    if adopcion_id is not None:
        query += " AND e.adopcion_id = %s"
        params.append(adopcion_id)

    if estado and estado.lower() != "todos":
        query += " AND LOWER(e.estado) = LOWER(%s)"
        params.append(estado)

    query += " ORDER BY e.fecha DESC, e.hora DESC"

    with get_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return serialize_rows(cursor.fetchall())


def update_interview(interview_id, data):
    allowed_fields = [
        "fecha",
        "hora",
        "modalidad",
        "observaciones",
        "estado",
    ]

    fields = []
    params = []

    for key in allowed_fields:
        if key in data:
            fields.append(f"{key} = %s")
            params.append(data[key])

    if not fields:
        return False

    params.append(interview_id)

    query = f"""
        UPDATE entrevistas
        SET {', '.join(fields)}
        WHERE id = %s
    """

    with get_cursor(commit=True) as cursor:
        cursor.execute(query, tuple(params))
        return cursor.rowcount > 0
