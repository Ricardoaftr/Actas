from modules.database import init_db, crear_usuario

init_db()
exito = crear_usuario("admin", "tu_password_segura", "admin", "PROYECTOS_RPA")

if exito:
    print("Usuario administrador creado con éxito")
else:
    print("El usuario ya existe")