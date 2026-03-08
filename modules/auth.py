import hashlib
from modules.database import obtener_usuario

def verificar_credenciales(username, password):
    datos = obtener_usuario(username)
    if datos:
        hash_almacenado, rol, empresa_id = datos
        hash_ingresado = hashlib.sha256(password.encode()).hexdigest()
        if hash_ingresado == hash_almacenado:
            return {"rol": rol, "empresa_id": empresa_id}
    return None