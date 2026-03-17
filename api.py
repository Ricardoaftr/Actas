from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil
import pyotp
import sqlite3
import pandas as pd


from modules.auth import verificar_credenciales
from modules.database import (
    DB_PATH, 
    listar_empresas_db, 
    crear_empresa_db, 
    actualizar_plan_empresa_db,
    eliminar_empresa_db,
    eliminar_usuario_global,
    resetear_password_superadmin,
    obtener_auditoria,
    registrar_auditoria,
    crear_usuario,
    obtener_metricas_dashboard,
    crear_tarea_db, 
    listar_tareas_admin, 
    actualizar_estado_tarea, 
    eliminar_tarea_db, 
    reasignar_tarea_db
)




app = FastAPI(title="API Actas LED")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NuevoUsuarioAdminRequest(BaseModel):
    username: str
    password: str
    rol: str
    empresa_id: str

class NuevoProyectoRequest(BaseModel):
    nombre: str
    notas: str
    empresa_id: str

class LoginRequest(BaseModel):
    usuario: str
    password: str

class Verify2FARequest(BaseModel):
    usuario: str
    codigo_2fa: str

class NuevaEmpresaRequest(BaseModel):
    nombre: str
    plan: str
    carpeta: str
    admin_user: str
    admin_pass: str

class ActualizarPlanRequest(BaseModel):
    plan: str

class ResetPasswordRequest(BaseModel):
    username: str
    nueva_pass: str

class TareaRequest(BaseModel):
    titulo: str
    descripcion: str
    asignado_a: str
    empresa_id: str
    creado_por: str

class EstadoTareaRequest(BaseModel):
    estado: str

class ReasignarRequest(BaseModel):
    nuevo_tecnico: str

@app.get("/api/admin/tecnicos/{empresa_id}")
def obtener_tecnicos(empresa_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT username FROM usuarios WHERE empresa_id = ? AND rol = 'tecnico'", (empresa_id,))
        tecnicos = [row[0] for row in c.fetchall()]
        conn.close()
        return {"success": True, "tecnicos": tecnicos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/tareas/{empresa_id}")
def obtener_tareas(empresa_id: str):
    try:
        tareas = listar_tareas_admin(empresa_id)
        if hasattr(tareas, 'values'): # Convertir DataFrame a lista limpia
            tareas = tareas.fillna("").values.tolist()
        return {"success": True, "tareas": tareas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/tareas")
def crear_tarea(datos: TareaRequest):
    try:
        crear_tarea_db(datos.titulo, datos.descripcion, datos.asignado_a, datos.empresa_id, datos.creado_por)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/tareas/{tarea_id}/estado")
def actualizar_estado(tarea_id: int, datos: EstadoTareaRequest):
    try:
        actualizar_estado_tarea(tarea_id, datos.estado)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/tareas/{tarea_id}/reasignar")
def reasignar_tarea(tarea_id: int, datos: ReasignarRequest):
    try:
        reasignar_tarea_db(tarea_id, datos.nuevo_tecnico)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    try:
        eliminar_tarea_db(tarea_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/login")
def login(datos: LoginRequest):
    exito, username, rol, empresa_id, mensaje = verificar_credenciales(datos.usuario, datos.password)
    
    if exito:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT secreto_2fa FROM usuarios WHERE username = ?", (username,))
        resultado = c.fetchone()
        conn.close()

        tiene_2fa = resultado and resultado[0] is not None and resultado[0] != ""

        return {
            "success": True, 
            "requiere_2fa": tiene_2fa,
            "usuario_temp": {"nombre": username, "rol": rol, "empresaId": empresa_id}
        }
    
    raise HTTPException(status_code=401, detail=mensaje or "Usuario o contraseña incorrectos")

@app.post("/api/verify-2fa")
def verificar_2fa(datos: Verify2FARequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT secreto_2fa FROM usuarios WHERE username = ?", (datos.usuario,))
    resultado = c.fetchone()
    conn.close()

    if not resultado or not resultado[0]:
        raise HTTPException(status_code=400, detail="El usuario no tiene 2FA configurado")
    
    secret = resultado[0]
    totp = pyotp.TOTP(secret)
    
    if totp.verify(datos.codigo_2fa):
        return {"success": True}
    else:
        raise HTTPException(status_code=401, detail="Codigo 2FA incorrecto o expirado")


# --- RUTAS DEL DASHBOARD (ADMIN) CORREGIDAS ---
@app.get("/api/admin/dashboard/{empresa_id}")
def obtener_dashboard_admin(empresa_id: str):
    try:
        resultado = obtener_metricas_dashboard(empresa_id)
        
        # Blindaje: Extraemos los datos ya sea que vengan como Tupla (5 valores) o Diccionario
        if isinstance(resultado, (tuple, list)):
            if len(resultado) == 5:
                total_actas, tareas_pendientes, tareas_completadas, uso_almacenamiento, actividad_reciente = resultado
            else:
                total_actas, tareas_pendientes, tareas_completadas, uso_almacenamiento, actividad_reciente = 0, 0, 0, "0 MB", []
        elif isinstance(resultado, dict):
            total_actas = resultado.get('total_actas', 0)
            tareas_pendientes = resultado.get('tareas_pendientes', 0)
            tareas_completadas = resultado.get('tareas_completadas', 0)
            uso_almacenamiento = resultado.get('uso_almacenamiento', "0 MB")
            actividad_reciente = resultado.get('actividad_reciente', [])
        else:
            total_actas, tareas_pendientes, tareas_completadas, uso_almacenamiento, actividad_reciente = 0, 0, 0, "0 MB", []

        # Convertir la actividad a lista limpia por si es un DataFrame de Pandas
        if hasattr(actividad_reciente, 'values'):
            actividad_reciente = actividad_reciente.fillna("").values.tolist()
            
        return {
            "success": True,
            "metricas": {
                "total_actas": total_actas,
                "tareas_pendientes": tareas_pendientes,
                "tareas_completadas": tareas_completadas,
                "uso_almacenamiento": uso_almacenamiento
            },
            "actividad_reciente": actividad_reciente
        }
    except Exception as e:
        import traceback
        traceback.print_exc() # Esto imprimirá el error real en tu terminal si vuelve a fallar
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/superadmin/empresas")
def obtener_empresas():
    try:
        empresas = listar_empresas_db()
        if hasattr(empresas, 'values'):
            empresas = empresas.fillna("").values.tolist()
        return {"success": True, "empresas": empresas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/superadmin/empresas")
def crear_empresa(datos: NuevaEmpresaRequest):
    try:
        nuevo_id = crear_empresa_db(datos.nombre, datos.plan, datos.carpeta)
        exito_usuario = crear_usuario(datos.admin_user, datos.admin_pass, "admin", nuevo_id)
        if exito_usuario:
            return {"success": True, "id": nuevo_id}
        else:
            eliminar_empresa_db(nuevo_id)
            raise HTTPException(status_code=400, detail="Error al crear usuario.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/superadmin/empresas/{empresa_id}/plan")
def actualizar_plan(empresa_id: str, datos: ActualizarPlanRequest):
    try:
        actualizar_plan_empresa_db(empresa_id, datos.plan)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/superadmin/empresas/{empresa_id}")
def eliminar_empresa(empresa_id: str):
    try:
        if eliminar_empresa_db(empresa_id):
            registrar_auditoria("GLOBAL", "SuperAdmin", "ELIMINAR EMPRESA", f"Se destruyo la empresa: {empresa_id}")
            return {"success": True}
        raise HTTPException(status_code=400, detail="Error al eliminar")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/superadmin/usuarios/{username}")
def eliminar_usuario(username: str):
    try:
        if eliminar_usuario_global(username):
            return {"success": True}
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/superadmin/usuarios/reset")
def reset_password(datos: ResetPasswordRequest):
    try:
        if resetear_password_superadmin(datos.username, datos.nueva_pass):
            return {"success": True}
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/superadmin/auditoria")
def obtener_logs_auditoria():
    try:
        logs = obtener_auditoria(empresa_id=None, limite=200)
        return {"success": True, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/superadmin/metricas")
def obtener_metricas():
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram_info = psutil.virtual_memory()
        disco_info = psutil.disk_usage('/')
        
        return {
            "success": True,
            "metricas": {
                "cpu": f"{cpu_usage}%",
                "ram_usada": f"{ram_info.percent}%",
                "ram_total": f"{round(ram_info.total / (1024**3), 1)} GB",
                "disco_usado": f"{disco_info.percent}%",
                "disco_total": f"{round(disco_info.total / (1024**3), 1)} GB"
            }
        }
    except Exception as e:
        return {"success": False, "detail": "Error al leer metricas del servidor"}

@app.get("/api/admin/kpi/{empresa_id}")
def obtener_kpi(empresa_id: str):
    try:
        resultado = obtener_metricas_dashboard(empresa_id)
        if isinstance(resultado, (tuple, list)) and len(resultado) >= 4:
            metricas = {
                "total_actas": resultado[0],
                "tareas_pendientes": resultado[1],
                "tareas_completadas": resultado[2],
                "uso_almacenamiento": resultado[3]
            }
        else:
            metricas = resultado if isinstance(resultado, dict) else {}
        return {"success": True, "metricas": metricas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/usuarios/{empresa_id}")
def listar_usuarios_admin(empresa_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT username, rol FROM usuarios WHERE empresa_id = ?", (empresa_id,))
        usuarios = c.fetchall()
        conn.close()
        return {"success": True, "usuarios": usuarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/usuarios")
def crear_usuario_admin(datos: NuevoUsuarioAdminRequest):
    try:
        exito = crear_usuario(datos.username, datos.password, datos.rol, datos.empresa_id)
        if exito:
            return {"success": True}
        raise HTTPException(status_code=400, detail="Error al crear usuario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/proyectos/{empresa_id}")
def listar_proyectos_admin(empresa_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, nombre, color, notas FROM carpetas_proyectos WHERE empresa_id = ?", (empresa_id,))
        proyectos = c.fetchall()
        conn.close()
        return {"success": True, "proyectos": proyectos}
    except Exception as e:
        # Retorna lista vacia si la tabla no existe o falla
        return {"success": True, "proyectos": []}

@app.post("/api/admin/proyectos")
def crear_proyecto_admin(datos: NuevoProyectoRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO carpetas_proyectos (nombre, color, notas, empresa_id) VALUES (?, ?, ?, ?)", 
                  (datos.nombre, "#FFFFFF", datos.notas, datos.empresa_id))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))