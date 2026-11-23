from database import get_cursor, serialize_row, serialize_rows

ESTADOS_VALIDOS = {
    "En revisión",
    "Entrevista",
    "Aprobada",
    "Rechazada",
    "Cancelada",
}


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
    with get_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (usuario_id,))
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
                "Ya existe una solicitud pendiente para este usuario y mascota"
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
            """,
            (
                usuario_id,
                mascota_id,
                fecha_solicitud,
                motivo,
                lugar_mascota,
                personas_casa,
                int(tiene_otras_mascotas),
                experiencia,
                responsable,
            ),
        )
        return cursor.lastrowid


def get_pending_adoptions():
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                a.id,
                a.usuario_id,
                u.nombre AS usuario_nombre,
                a.mascota_id,
                m.nombre AS mascota_nombre,
                m.tipo AS mascota_tipo,
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
            WHERE a.estado IN ('En revisión', 'Entrevista')
            ORDER BY a.fecha_solicitud ASC, a.id ASC
            """
        )
        return serialize_rows(cursor.fetchall())


def get_adoption_by_id(adoption_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                a.id,
                a.usuario_id,
                u.nombre AS usuario_nombre,
                u.ciudad AS usuario_ciudad,
                a.mascota_id,
                m.nombre AS mascota_nombre,
                m.tipo AS mascota_tipo,
                m.edad AS mascota_edad,
                m.tamano AS mascota_tamano,
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
            WHERE a.id = %s
            """,
            (adoption_id,),
        )
        return serialize_row(cursor.fetchone())


def update_adoption_status(adoption_id, new_status):
    if new_status not in ESTADOS_VALIDOS:
        raise ValueError(
            "Estado inválido. Use: En revisión, Entrevista, Aprobada, Rechazada o Cancelada"
        )

    with get_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM adopciones WHERE id = %s", (adoption_id,))
        if not cursor.fetchone():
            return False

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
                UPDATE mascotas m
                INNER JOIN adopciones a ON a.mascota_id = m.id
                SET m.estado = 'Adoptada'
                WHERE a.id = %s
                """,
                (adoption_id,),
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
        cursor.execute("SELECT id FROM adopciones WHERE id = %s", (adoption_id,))
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
            """,
            (
                adoption_id,
                interview_date,
                interview_time,
                modality,
                observations,
            ),
        )
        interview_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE adopciones
            SET estado = 'Entrevista'
            WHERE id = %s
            """,
            (adoption_id,),
        )

        return interview_id


def get_upcoming_interviews():
    with get_cursor() as cursor:
        cursor.execute(
            """
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
                a.mascota_id,
                m.nombre AS mascota_nombre
            FROM entrevistas e
            INNER JOIN adopciones a ON e.adopcion_id = a.id
            INNER JOIN usuarios u ON a.usuario_id = u.id
            INNER JOIN mascotas m ON a.mascota_id = m.id
            WHERE e.estado = 'Programada'
              AND e.fecha >= CURDATE()
            ORDER BY e.fecha ASC, e.hora ASC
            """
        )
        return serialize_rows(cursor.fetchall())
