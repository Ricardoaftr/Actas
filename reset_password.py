import sqlite3
import hashlib
import os

ruta_db = os.path.join("data", "database.sqlite")

def forzar_usuario(username, nueva_password):
    if not os.path.exists(ruta_db):
        print(f"Error: No se encontró la base de datos en {ruta_db}")
        return

    pwd_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
    conn = sqlite3.connect(ruta_db)
    c = conn.cursor()
    
    c.execute("UPDATE usuarios SET password_hash = ? WHERE username = ?", (pwd_hash, username))
    
    if c.rowcount == 0:
        c.execute("INSERT INTO usuarios (username, password_hash, rol, empresa_id) VALUES (?, ?, ?, ?)",
                  (username, pwd_hash, 'admin', 'PROYECTOS_RPA'))
        print(f"Usuario {username} no existía. Creado como ADMIN con la nueva clave.")
    else:
        print(f"Clave de {username} actualizada correctamente.")
    
    conn.commit()
    conn.close()

forzar_usuario("admin", "1193430021")