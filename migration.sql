-- ========================================================
-- MIGRACIÓN COMPATIBLE HUELLITAS FELICES
-- ========================================================
USE huellitas_felices;

-- 1. Vincular Refugios con Usuarios
ALTER TABLE refugios ADD COLUMN IF NOT EXISTS usuario_id INT NULL;
-- Agregar clave foránea si no existe
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS WHERE CONSTRAINT_NAME = 'fk_refugios_usuario' AND TABLE_NAME = 'refugios');
SET @sql = IF(@fk_exists = 0, 'ALTER TABLE refugios ADD CONSTRAINT fk_refugios_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL;', 'SELECT "Constraint ya existe";');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. Estado Activo en Usuarios (para gestión de cuentas por Admin)
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;
UPDATE usuarios SET activo = TRUE WHERE activo IS NULL;

-- 3. Campo foto_url en Mascotas (para soportar imágenes personalizadas además de fallbacks visuales)
ALTER TABLE mascotas ADD COLUMN IF NOT EXISTS foto_url VARCHAR(500) NULL;

-- 4. Usuarios para Refugios (contraseña inicial: refugio123 -> SHA256: 4b29bb73a5a415ff67da2368c5b0580ca0ce6ebf010f37b1dfa52b8277259062)
INSERT IGNORE INTO usuarios (id, nombre, usuario, password, edad, ciudad, tipo_vivienda, tiene_patio, otras_mascotas, tiempo_disponible, experiencia, rol, activo)
VALUES 
(7, 'Huellitas Popayan', 'refugio_1', '4b29bb73a5a415ff67da2368c5b0580ca0ce6ebf010f37b1dfa52b8277259062', 30, 'Popayan', 'Institucional', 1, 1, 'Alta', 'Administración de refugio', 'refugio', 1),
(8, 'Refugio Patitas Felices', 'refugio_2', '4b29bb73a5a415ff67da2368c5b0580ca0ce6ebf010f37b1dfa52b8277259062', 30, 'Popayan', 'Institucional', 1, 1, 'Alta', 'Administración de refugio', 'refugio', 1),
(9, 'Fundacion Amigos Peludos', 'refugio_3', '4b29bb73a5a415ff67da2368c5b0580ca0ce6ebf010f37b1dfa52b8277259062', 30, 'Cali', 'Institucional', 1, 1, 'Alta', 'Administración de refugio', 'refugio', 1);

UPDATE refugios SET usuario_id = 7 WHERE id = 1 AND (usuario_id IS NULL OR usuario_id = 0);
UPDATE refugios SET usuario_id = 8 WHERE id = 2 AND (usuario_id IS NULL OR usuario_id = 0);
UPDATE refugios SET usuario_id = 9 WHERE id = 3 AND (usuario_id IS NULL OR usuario_id = 0);

-- 5. Favoritos de prueba
INSERT IGNORE INTO favoritos (usuario_id, mascota_id) VALUES (2, 1), (2, 2), (3, 3);
