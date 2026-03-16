from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil
import pyotp
import sqlite3

# Quitamos crear_usuario de aquí
from modules.auth import verificar_credenciales

# Y lo agregamos aquí, a database
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
    crear_usuario
)

app = FastAPI(title="API Actas LED")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            raise HTTPException(status_code=400, detail="Error al crear usuario. El nombre podria estar en uso.")
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