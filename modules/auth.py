import sqlite3
import hashlib
from datetime import datetime, timedelta
from modules.database import DB_PATH, obtener_estado_bloqueo, actualizar_intentos

MAX_INTENTOS = 5
TIEMPO_BLOQUEO_MINUTOS = 15

def verificar_credenciales(username, password):
    estado = obtener_estado_bloqueo(username)
    
    if estado:
        intentos, bloqueado_hasta = estado
        if bloqueado_hasta:
            tiempo_desbloqueo = datetime.strptime(bloqueado_hasta, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < tiempo_desbloqueo:
                faltan = (tiempo_desbloqueo - datetime.now()).seconds // 60
                mensaje = f"Cuenta bloqueada. Intente de nuevo en {faltan + 1} minutos."
                return False, None, None, None, mensaje
            else:
                actualizar_intentos(username, 0, None)
                intentos = 0
    else:
        intentos = 0

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute("SELECT rol, empresa_id FROM usuarios WHERE username = ? AND password_hash = ?", (username, password_hash))
    resultado = c.fetchone()
    conn.close()
    
    if resultado:
        actualizar_intentos(username, 0, None)
        return True, username, resultado[0], resultado[1], "Exito"
    else:
        if estado is not None:
            intentos += 1
            if intentos >= MAX_INTENTOS:
                tiempo_desbloqueo = (datetime.now() + timedelta(minutes=TIEMPO_BLOQUEO_MINUTOS)).strftime("%Y-%m-%d %H:%M:%S")
                actualizar_intentos(username, intentos, tiempo_desbloqueo)
                return False, None, None, None, "Cuenta bloqueada por multiples intentos fallidos."
            else:
                actualizar_intentos(username, intentos, None)
        return False, None, None, None, "Usuario o contrasena incorrectos."