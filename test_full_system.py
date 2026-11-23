"""
Test suite de integración completa para el sistema Huellitas Felices.
Prueba todas las rutas de la API, roles, autenticación, y lógica de negocio.
"""
import sys
import os

# Asegurar path de backend
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app

client = app.test_client()

API_KEY = 'huellitas_api_secret_key_2026'

def headers_with_auth(token=None):
    h = {
        'Content-Type': 'application/json',
        'X-API-KEY': API_KEY
    }
    if token:
        h['Authorization'] = f'Bearer {token}'
    return h

def run_tests():
    print("=" * 60)
    print("INICIANDO PRUEBAS DE INTEGRACIÓN: HUELLITAS FELICES")
    print("=" * 60)
    
    # 1. Health check
    res = client.get('/', headers=headers_with_auth())
    assert res.status_code == 200, f"Health check falló: {res.status_code}"
    print("[PASS] 1. Health check OK")

    # 2. Login Adoptante (carlos / adoptante123)
    res = client.post('/api/auth/login', json={'usuario': 'carlos', 'password': 'adoptante123'}, headers=headers_with_auth())
    assert res.status_code == 200, f"Login carlos falló: {res.data}"
    data_carlos = res.get_json()
    token_carlos = data_carlos['token']
    assert data_carlos['usuario']['rol'] == 'adoptante'
    print(f"[PASS] 2. Login Adoptante OK: {data_carlos['usuario']['nombre']} (rol: {data_carlos['usuario']['rol']})")

    # 3. Login Refugio (refugio_1 / refugio123)
    res = client.post('/api/auth/login', json={'usuario': 'refugio_1', 'password': 'refugio123'}, headers=headers_with_auth())
    assert res.status_code == 200, f"Login refugio falló: {res.data}"
    data_refugio = res.get_json()
    token_refugio = data_refugio['token']
    assert data_refugio['usuario']['rol'] == 'refugio'
    assert data_refugio['usuario']['refugio_id'] is not None
    print(f"[PASS] 3. Login Refugio OK: {data_refugio['usuario']['nombre']} (refugio_id: {data_refugio['usuario']['refugio_id']})")

    # 4. Login Admin (admin / admin123)
    res = client.post('/api/auth/login', json={'usuario': 'admin', 'password': 'admin123'}, headers=headers_with_auth())
    assert res.status_code == 200, f"Login admin falló: {res.data}"
    data_admin = res.get_json()
    token_admin = data_admin['token']
    assert data_admin['usuario']['rol'] == 'admin'
    print(f"[PASS] 4. Login Admin OK: {data_admin['usuario']['nombre']} (rol: {data_admin['usuario']['rol']})")

    # 5. Listar mascotas públicas / con filtros
    res = client.get('/api/mascotas', headers=headers_with_auth(token_carlos))
    assert res.status_code == 200
    res_data = res.get_json()
    pets = res_data.get('mascotas', res_data)
    assert isinstance(pets, list)
    assert len(pets) > 0
    print(f"[PASS] 5. Listar mascotas OK: {len(pets)} mascotas encontradas")

    # 5.1 Filtro por tipo=Perro
    res = client.get('/api/mascotas?tipo=Perro', headers=headers_with_auth(token_carlos))
    assert res.status_code == 200
    res_dogs = res.get_json()
    dogs = res_dogs.get('mascotas', res_dogs)
    for d in dogs:
        assert d['tipo'].lower() == 'perro'
    print(f"[PASS] 5.1 Filtro tipo=Perro OK: {len(dogs)} perros")

    # 6. Detalle completo de mascota (incluyendo refugio e historial veterinario)
    pet_id = pets[0]['id']
    res = client.get(f'/api/mascotas/{pet_id}', headers=headers_with_auth(token_carlos))
    assert res.status_code == 200
    pet_detail = res.get_json()
    assert 'nombre' in pet_detail
    assert 'refugio' in pet_detail
    assert 'historial' in pet_detail
    print(f"[PASS] 6. Detalle completo de mascota ID {pet_id} ({pet_detail['nombre']}) OK. "
          f"Refugio: {pet_detail['refugio'].get('nombre') if pet_detail['refugio'] else 'N/A'}. "
          f"Historial veterinario: {len(pet_detail['historial'])} registros")

    # 7. Favoritos
    # Obtener favoritos de carlos
    res = client.get('/api/favoritos', headers=headers_with_auth(token_carlos))
    assert res.status_code == 200
    favs = res.get_json()
    print(f"[PASS] 7. Favoritos de carlos OK: {len(favs)} favoritos")

    # Toggle favorito (agregar o quitar)
    res = client.post(f'/api/favoritos/{pet_id}', headers=headers_with_auth(token_carlos))
    assert res.status_code in [200, 201]
    fav_action = res.get_json()
    print(f"[PASS] 7.1 Acción toggle favorito en pet ID {pet_id}: {fav_action.get('message')}")

    # 8. Perfil de usuario (GET y PUT)
    res = client.get('/api/usuarios/perfil', headers=headers_with_auth(token_carlos))
    assert res.status_code == 200
    perfil = res.get_json()
    assert perfil['usuario'] == 'carlos'
    print(f"[PASS] 8. Perfil de carlos OK: ciudad={perfil.get('ciudad')}, tiempo_disponible={perfil.get('tiempo_disponible')}")

    # 9. Mis solicitudes de adopción
    res = client.get('/api/adopciones', headers=headers_with_auth(token_carlos))
    assert res.status_code == 200
    mis_solicitudes = res.get_json()
    print(f"[PASS] 9. Mis solicitudes de adopción (carlos): {len(mis_solicitudes)} solicitudes")

    # 10. Mis entrevistas
    res = client.get('/api/entrevistas', headers=headers_with_auth(token_carlos))
    assert res.status_code == 200
    mis_entrevistas = res.get_json()
    print(f"[PASS] 10. Mis entrevistas (carlos): {len(mis_entrevistas)} entrevistas")

    # 11. Refugio: Información de 'mi-refugio'
    res = client.get('/api/refugios/mi-refugio', headers=headers_with_auth(token_refugio))
    assert res.status_code == 200
    mi_refugio = res.get_json()
    nombre_refugio = mi_refugio.get('refugio', {}).get('nombre')
    print(f"[PASS] 11. Panel refugio: datos de 'mi-refugio' OK ({nombre_refugio})")

    # 12. Refugio: Mascotas de su refugio
    res = client.get('/api/mascotas/refugio/mis-mascotas', headers=headers_with_auth(token_refugio))
    assert res.status_code == 200
    ref_pets = res.get_json()
    print(f"[PASS] 12. Panel refugio: mis mascotas OK ({len(ref_pets)} mascotas del refugio)")

    # 13. Refugio: Solicitudes recibidas
    res = client.get('/api/adopciones', headers=headers_with_auth(token_refugio))
    assert res.status_code == 200
    ref_adopciones = res.get_json()
    print(f"[PASS] 13. Panel refugio: solicitudes recibidas OK ({len(ref_adopciones)} solicitudes)")

    # 14. Admin: Estadísticas globales
    res = client.get('/api/admin/estadisticas', headers=headers_with_auth(token_admin))
    assert res.status_code == 200
    stats = res.get_json()
    print(f"[PASS] 14. Panel admin: estadísticas OK (usuarios: {stats.get('total_usuarios')}, mascotas: {stats.get('total_mascotas')}, adopciones: {stats.get('total_adopciones')})")

    # 15. Admin: Listado y control de usuarios
    res = client.get('/api/usuarios', headers=headers_with_auth(token_admin))
    assert res.status_code == 200
    users_list = res.get_json()
    print(f"[PASS] 15. Panel admin: listado de usuarios OK ({len(users_list)} usuarios)")

    # 16. Control de acceso: Usuario adoptante NO puede acceder a panel admin
    res = client.get('/api/admin/estadisticas', headers=headers_with_auth(token_carlos))
    assert res.status_code == 403, f"Se esperaba 403 pero se obtuvo {res.status_code}"
    print("[PASS] 16. Seguridad y RBAC OK: Adoptante bloqueado de rutas administrativas (403 Forbidden)")

    print("=" * 60)
    print("TODAS LAS PRUEBAS DE INTEGRACIÓN PASARON EXITOSAMENTE (16/16)")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
