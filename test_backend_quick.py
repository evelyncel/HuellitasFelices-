import sys
import os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

try:
    from config import Config
    print("[OK] Config cargada")
    print("     DB:", Config.DB_HOST + "/" + Config.DB_NAME, "usuario=" + Config.DB_USER)
    print("     Puerto:", Config.SERVER_PORT)
except Exception as e:
    print("[ERROR] Config:", e)
    sys.exit(1)

try:
    from utils.database import get_connection
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM usuarios")
        row = cur.fetchone()
        print("[OK] MySQL conectado - Usuarios en DB:", row['total'])
        cur.execute("SELECT usuario, rol FROM usuarios LIMIT 5")
        users = cur.fetchall()
        for u in users:
            print("     -", u['usuario'], "(" + u['rol'] + ")")
    conn.close()
except Exception as e:
    print("[ERROR] MySQL:", e)
    sys.exit(1)

try:
    from utils.auth import authenticate_user, hash_password
    from utils.database import get_cursor

    h = hash_password("admin123")
    print("[OK] Hash admin123:", h[:20] + "...")

    user = authenticate_user("admin", "admin123")
    if user:
        print("[OK] Login admin exitoso - rol=" + user['rol'])
    else:
        print("[WARN] Login admin FALLO - comparando hashes...")
        with get_cursor() as cur:
            cur.execute("SELECT usuario, password FROM usuarios WHERE usuario='admin'")
            row = cur.fetchone()
            if row:
                db_hash = row['password']
                expected = hash_password("admin123")
                print("     Hash en DB:   ", db_hash)
                print("     Hash esperado:", expected)
                print("     Coinciden:", db_hash == expected)
            else:
                print("     Usuario 'admin' NO existe en la DB")

    user2 = authenticate_user("carlos", "adoptante123")
    if user2:
        print("[OK] Login carlos exitoso - rol=" + user2['rol'])
    else:
        print("[WARN] Login carlos FALLO - comparando hashes...")
        with get_cursor() as cur:
            cur.execute("SELECT usuario, password FROM usuarios WHERE usuario='carlos'")
            row = cur.fetchone()
            if row:
                db_hash = row['password']
                expected = hash_password("adoptante123")
                print("     Hash en DB:   ", db_hash)
                print("     Hash esperado:", expected)
                print("     Coinciden:", db_hash == expected)
            else:
                print("     Usuario 'carlos' NO existe en la DB")

except Exception as e:
    print("[ERROR] Auth:", e)

print("")
print("[LISTO] Verificacion completada.")
