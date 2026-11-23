"""
Test suite de verificación para:
1. Subida local de imágenes (POST /api/upload y GET /uploads/<filename>)
2. Creación y eliminación de registros veterinarios por Admin
3. Consulta de las 20 fundaciones y 29 mascotas
"""
import io
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app

client = app.test_client()

API_KEY = 'huellitas_api_secret_key_2026'

def get_admin_token():
    res = client.post('/auth/login', json={'usuario': 'admin', 'password': 'admin123'}, headers={'X-API-KEY': API_KEY})
    assert res.status_code == 200
    return res.get_json()['token']

def test_features():
    print("=" * 60)
    print("PROBANDO NUEVAS FUNCIONALIDADES SOLICITADAS")
    print("=" * 60)

    token = get_admin_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'X-API-KEY': API_KEY
    }

    # 1. Probar subida local de foto
    print("\n1. Probando subida local de imagen (POST /api/upload)...")
    dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
    data = {
        'file': (io.BytesIO(dummy_png), 'mi_perrito_local.png', 'image/png')
    }
    res = client.post('/api/upload', data=data, content_type='multipart/form-data', headers={'X-API-KEY': API_KEY})
    assert res.status_code == 201, f"Falló upload: {res.data}"
    upload_res = res.get_json()
    filename = upload_res['filename']
    url = upload_res['url']
    print(f"  [PASS] Imagen subida exitosamente: {filename} -> {url}")

    # 1.1 Probar descarga/servicio de la imagen subida
    res = client.get(f'/uploads/{filename}')
    assert res.status_code == 200
    assert len(res.data) == len(dummy_png)
    print(f"  [PASS] Imagen servida correctamente en /uploads/{filename} (200 OK)")

    # 2. Probar que Admin puede crear registro veterinario
    print("\n2. Probando creación de registro veterinario por Admin...")
    # Obtener primera mascota
    res_pets = client.get('/api/mascotas', headers=headers)
    assert res_pets.status_code == 200
    pets = res_pets.get_json().get('mascotas', [])
    assert len(pets) > 0
    test_pet_id = pets[0]['id']

    nuevo_control = {
        "tipo": "Vacuna",
        "descripcion": "Vacuna triple felina aplicada por administrador",
        "fecha": "2026-03-25",
        "proxima_fecha": "2027-03-25",
        "veterinario": "Dr. Fernando Ortiz - MV",
        "observaciones": "Paciente en excelente estado, sin reacciones alérgicas"
    }
    res_control = client.post(f'/api/mascotas/{test_pet_id}/controles', json=nuevo_control, headers=headers)
    assert res_control.status_code == 201, f"Falló creación de control: {res_control.data}"
    control_id = res_control.get_json()['id']
    print(f"  [PASS] Registro veterinario creado exitosamente por Admin (ID #{control_id}) para mascota ID #{test_pet_id}")

    # 2.1 Probar eliminación del control por Admin
    res_del = client.delete(f'/api/seguimiento/controles/{control_id}', headers=headers)
    assert res_del.status_code == 200
    print(f"  [PASS] Registro veterinario eliminado exitosamente por Admin (ID #{control_id})")

    # 3. Verificar cantidad de fundaciones (20) y mascotas (al menos 20)
    print("\n3. Verificando cantidad de fundaciones y mascotas en la plataforma...")
    res_refugios = client.get('/api/refugios', headers=headers)
    assert res_refugios.status_code == 200
    refugios = res_refugios.get_json().get('refugios', [])
    print(f"  [PASS] Total fundaciones registradas: {len(refugios)} (Meta: 20)")
    assert len(refugios) >= 20

    print(f"  [PASS] Total mascotas registradas: {len(pets)} (Meta: 20+)")
    assert len(pets) >= 20

    perros = [p for p in pets if p['tipo'].lower() == 'perro']
    gatos = [p for p in pets if p['tipo'].lower() == 'gato']
    print(f"  [PASS] Distribución: {len(perros)} Perros y {len(gatos)} Gatos")
    assert len(perros) >= 5 and len(gatos) >= 5

    print("\n" + "=" * 60)
    print("¡TODAS LAS PRUEBAS DE LAS NUEVAS FUNCIONALIDADES PASARON AL 100%!")
    print("=" * 60)

if __name__ == '__main__':
    test_features()
