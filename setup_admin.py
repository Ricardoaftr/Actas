import sqlite3
import hashlib
import os

DB_PATH = "data/database.sqlite"

usuario_maestro = "Ricardo"
password_maestro = "1193430021"
rol = "superadmin"
empresa_id = "GLOBAL"

def crear_superadmin():
    if not os.path.exists(DB_PATH):
        print("La base de datos no existe aún.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    password_hash = hashlib.sha256(password_maestro.encode()).hexdigest()
    
    try:
        c.execute("INSERT INTO usuarios (username, password_hash, rol, empresa_id) VALUES (?, ?, ?, ?)", 
                  (usuario_maestro, password_hash, rol, empresa_id))
        conn.commit()
        print(f"Superadmin '{usuario_maestro}' creado exitosamente.")
    except sqlite3.IntegrityError:
        print(f"El usuario '{usuario_maestro}' ya existe en la base de datos.")
    
    conn.close()

if __name__ == "__main__":
    crear_superadmin()