import sqlite3
import hashlib
from modules.database import DB_PATH

def verificar_credenciales(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute("SELECT rol, empresa_id FROM usuarios WHERE username = ? AND password_hash = ?", (username, password_hash))
    resultado = c.fetchone()
    conn.close()
    
    if resultado:
        return True, username, resultado[0], resultado[1]
    return False, None, None, None