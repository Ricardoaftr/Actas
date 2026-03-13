import sqlite3
import uuid
import os
import pandas as pd
import hashlib
from datetime import datetime

DB_PATH = "data/database.sqlite"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion 
                 (clave TEXT PRIMARY KEY, valor INTEGER)''')
    c.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('ultimo_acta', 0)")
    
    c.execute('''CREATE TABLE IF NOT EXISTS empresas 
                    (id TEXT PRIMARY KEY, 
                    nombre TEXT, 
                    plan TEXT, 
                    carpeta_drive_raiz TEXT,
                    modulos_activos TEXT DEFAULT 'actas,tareas,dashboard')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                    (username TEXT PRIMARY KEY, 
                    password_hash TEXT, 
                    rol TEXT, 
                    empresa_id TEXT,
                    intentos_fallidos INTEGER DEFAULT 0,
                    bloqueado_hasta TEXT,
                    secreto_2fa TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS carpetas_proyectos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT, 
                  color TEXT, 
                  notas TEXT,
                  empresa_id TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS registros_actas 
                 (id_acta TEXT PRIMARY KEY, 
                  usuario TEXT, 
                  proyecto_texto_libre TEXT, 
                  fecha TEXT, 
                  ruta_archivo TEXT,
                  carpeta_id INTEGER,
                  empresa_id TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tareas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tecnico TEXT, 
                  proyecto_id INTEGER, 
                  descripcion TEXT, 
                  prioridad TEXT, 
                  estado TEXT, 
                  fecha_asignacion TEXT,
                  fecha_limite TEXT,
                  checklist TEXT DEFAULT '',
                  empresa_id TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS auditoria 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  empresa_id TEXT, 
                  usuario TEXT, 
                  accion TEXT, 
                  detalle TEXT, 
                  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    columnas_nuevas = [
        ("carpetas_proyectos", "empresa_id TEXT"),
        ("registros_actas", "empresa_id TEXT"),
        ("tareas", "empresa_id TEXT"),
        ("usuarios", "intentos_fallidos INTEGER DEFAULT 0"),
        ("usuarios", "bloqueado_hasta TEXT"),
        ("usuarios", "secreto_2fa TEXT"),
        ("empresas", "modulos_activos TEXT DEFAULT 'actas,tareas,dashboard'")
    ]
    
    for tabla, definicion in columnas_nuevas:
        try:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {definicion}")
        except sqlite3.OperationalError:
            pass
            
    conn.commit()
    conn.close()

def crear_tarea_db(tecnico, proyecto_id, descripcion, prioridad, fecha_limite, checklist, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    fecha_asignacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute('''INSERT INTO tareas 
                 (tecnico, proyecto_id, descripcion, prioridad, estado, fecha_asignacion, fecha_limite, checklist, empresa_id) 
                 VALUES (?, ?, ?, ?, 'Pendiente', ?, ?, ?, ?)''', 
              (tecnico, proyecto_id, descripcion, prioridad, fecha_asignacion, fecha_limite, checklist, empresa_id))
    
    conn.commit()
    conn.close()

def obtener_modulos_empresa(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT plan, modulos_activos FROM empresas WHERE id = ?", (empresa_id,))
    res = c.fetchone()
    conn.close()
    
    if res:
        plan_empresa = str(res[0]).lower()
        modulos_personalizados = res[1].split(',') if res[1] else []
        
        if "basico" in plan_empresa or "básico" in plan_empresa:
            return ['actas']
        
        elif plan_empresa == "plus":
            return ['actas', 'tareas', 'dashboard']
            
        elif plan_empresa == "enterprise":
            modulos_base = ['actas', 'tareas', 'dashboard']
            return list(set(modulos_base + modulos_personalizados))
            
    return ['actas']

def listar_tareas_admin(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT t.id, t.tecnico, c.nombre, t.descripcion, t.prioridad, t.estado, t.fecha_asignacion, t.fecha_limite, t.checklist 
                 FROM tareas t 
                 LEFT JOIN carpetas_proyectos c ON t.proyecto_id = c.id 
                 WHERE t.empresa_id = ?''', (empresa_id,))
    
    res = c.fetchall()
    conn.close()
    
    if res:
        return pd.DataFrame(res, columns=["ID", "Tecnico", "Proyecto", "Descripcion", "Prioridad", "Estado", "Fecha Asignacion", "Fecha Limite", "Checklist"])
    return None
    
def obtener_secreto_2fa(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT secreto_2fa FROM usuarios WHERE username = ?", (username,))
    res = c.fetchone()
    conn.close()
    return res[0] if res and res[0] else None

def guardar_secreto_2fa(username, secreto):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET secreto_2fa = ? WHERE username = ?", (secreto, username))
    conn.commit()
    conn.close()


def actualizar_estado_tarea(id_tarea, nuevo_estado, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tareas SET estado = ? WHERE id = ? AND empresa_id = ?", (nuevo_estado, id_tarea, empresa_id))
    conn.commit()
    conn.close()

def obtener_siguiente_id(empresa_id):
    clave = f"ultimo_acta_{empresa_id}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    row = c.fetchone()
    siguiente = row[0] + 1 if row else 1
    conn.close()
    return f"ACT-{siguiente:03d}"

def obtener_usuario(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash, rol, empresa_id FROM usuarios WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def listar_tareas_tecnico(tecnico_username, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT t.id, c.nombre, t.descripcion, t.prioridad, t.estado, t.fecha_asignacion, t.fecha_limite, t.checklist 
                 FROM tareas t 
                 LEFT JOIN carpetas_proyectos c ON t.proyecto_id = c.id 
                 WHERE t.tecnico = ? AND t.empresa_id = ?''', (tecnico_username, empresa_id))
    
    res = c.fetchall()
    conn.close()
    
    if res:
        return pd.DataFrame(res, columns=["ID", "Proyecto", "Descripcion", "Prioridad", "Estado", "Fecha Asignacion", "Fecha Limite", "Checklist"])
    return None

def obtener_estado_bloqueo(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT intentos_fallidos, bloqueado_hasta FROM usuarios WHERE username = ?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def actualizar_intentos(username, intentos, bloqueado_hasta=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE username = ?", (intentos, bloqueado_hasta, username))
    conn.commit()
    conn.close

def guardar_nuevo_consecutivo(empresa_id):
    clave = f"ultimo_acta_{empresa_id}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE configuracion SET valor = valor + 1 WHERE clave = ?", (clave,))
    else:
        c.execute("INSERT INTO configuracion (clave, valor) VALUES (?, 1)", (clave,))
    conn.commit()
    conn.close()

def crear_usuario(username, password, rol, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO usuarios (username, password_hash, rol, empresa_id) VALUES (?, ?, ?, ?)", 
                  (username, password_hash, rol, empresa_id))
        conn.commit()
        exito = True
    except sqlite3.IntegrityError:
        exito = False
    conn.close()
    return exito

def listar_usuarios(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT username, rol FROM usuarios WHERE empresa_id = ?"
    try:
        df = pd.read_sql_query(query, conn, params=(empresa_id,))
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def actualizar_password(username, nueva_password, empresa_id):
    pwd_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET password_hash = ? WHERE username = ? AND empresa_id = ?", (pwd_hash, username, empresa_id))
    conn.commit()
    conn.close()

def eliminar_usuario(username, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE username = ? AND empresa_id = ?", (username, empresa_id))
    conn.commit()
    conn.close()

def registrar_acta_db(id_acta, usuario, proyecto, fecha, ruta, carpeta_id=None, empresa_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO registros_actas 
            (id_acta, usuario, proyecto_texto_libre, fecha, ruta_archivo, carpeta_id, empresa_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_acta, usuario, proyecto, fecha, ruta, carpeta_id, empresa_id))
        conn.commit()
    except Exception as e:
        print(f"Error al registrar acta: {e}")
    finally:
        conn.close()

def crear_carpeta_db(nombre, color, notas, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id FROM carpetas_proyectos WHERE nombre = ? AND empresa_id = ?", (nombre, empresa_id))
    if c.fetchone():
        conn.close()
        return False 
        
    try:
        c.execute("INSERT INTO carpetas_proyectos (nombre, color, notas, empresa_id) VALUES (?, ?, ?, ?)", 
                  (nombre, color, notas, empresa_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error crítico en BD al crear carpeta: {e}")
        return False
    finally: 
        conn.close()

def listar_carpetas_db(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Filtramos para que solo devuelva las carpetas de esta empresa
    c.execute("SELECT * FROM carpetas_proyectos WHERE empresa_id = ?", (empresa_id,))
    res = c.fetchall()
    conn.close()
    return res

def asignar_acta_a_carpeta(id_acta, carpeta_id, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE registros_actas SET carpeta_id = ? WHERE id_acta = ? AND empresa_id = ?", (carpeta_id, id_acta, empresa_id))
    conn.commit()
    conn.close()

def obtener_historial_proyectos(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT nombre FROM carpetas_proyectos WHERE empresa_id = ?", (empresa_id,))
    res = [row[0] for row in c.fetchall()]
    conn.close()
    return res

def obtener_actas_por_proyecto(nombre_carpeta, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT r.* FROM registros_actas r 
                 JOIN carpetas_proyectos c ON r.carpeta_id = c.id 
                 WHERE c.nombre = ? AND c.empresa_id = ?""", (nombre_carpeta, empresa_id))
    res = c.fetchall()
    conn.close()
    return res

def eliminar_carpeta_db(id_carpeta, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE registros_actas SET carpeta_id = NULL WHERE carpeta_id = ? AND empresa_id = ?", (id_carpeta, empresa_id))
    c.execute("DELETE FROM carpetas_proyectos WHERE id = ? AND empresa_id = ?", (id_carpeta, empresa_id))
    conn.commit()
    conn.close()

def editar_carpeta_db(id_carpeta, nombre, color, notas, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("UPDATE carpetas_proyectos SET nombre = ?, color = ?, notas = ? WHERE id = ? AND empresa_id = ?", 
                  (nombre, color, notas, id_carpeta, empresa_id))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def eliminar_tarea_db(id_tarea, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tareas WHERE id = ? AND empresa_id = ?", (id_tarea, empresa_id))
    conn.commit()
    conn.close()

def reasignar_tarea_db(id_tarea, nuevo_tecnico, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tareas SET tecnico = ? WHERE id = ? AND empresa_id = ?", (nuevo_tecnico, id_tarea, empresa_id))
    conn.commit()
    conn.close()

def obtener_metricas_dashboard(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM registros_actas WHERE empresa_id = ?", (empresa_id,))
    total_actas = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tareas WHERE empresa_id = ?", (empresa_id,))
    total_tareas = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tareas WHERE estado = 'Finalizada' AND empresa_id = ?", (empresa_id,))
    actas_vinculadas = c.fetchone()[0]
    
    c.execute("SELECT usuario, COUNT(*) as total FROM registros_actas WHERE empresa_id = ? GROUP BY usuario", (empresa_id,))
    actas_usuarios = c.fetchall()
    
    conn.close()
    
    actas_independientes = total_actas - actas_vinculadas
    if actas_independientes < 0:
        actas_independientes = 0
        
    return total_actas, total_tareas, actas_vinculadas, actas_independientes, actas_usuarios

def crear_empresa_db(nombre, plan, carpeta_drive_raiz):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    empresa_id = str(uuid.uuid4())[:8]
    
    c.execute("INSERT INTO empresas (id, nombre, plan, carpeta_drive_raiz) VALUES (?, ?, ?, ?)",
              (empresa_id, nombre, plan, carpeta_drive_raiz))
    conn.commit()
    conn.close()
    return empresa_id

def listar_empresas_db():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM empresas"
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def actualizar_plan_empresa_db(empresa_id, nuevo_plan):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE empresas SET plan = ? WHERE id = ?", (nuevo_plan, empresa_id))
    conn.commit()
    conn.close()

def eliminar_empresa_db(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM tareas WHERE empresa_id = ?", (empresa_id,))
        c.execute("DELETE FROM registros_actas WHERE empresa_id = ?", (empresa_id,))
        c.execute("DELETE FROM carpetas_proyectos WHERE empresa_id = ?", (empresa_id,))
        c.execute("DELETE FROM usuarios WHERE empresa_id = ?", (empresa_id,))
        c.execute("DELETE FROM configuracion WHERE clave = ?", (f"ultimo_acta_{empresa_id}",))
        c.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error crítico al eliminar empresa: {e}")
        return False
    finally:
        conn.close()

def eliminar_usuario_global(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE username = ?", (username,))
    
    filas_afectadas = c.rowcount 
    
    conn.commit()
    conn.close()
    
    return filas_afectadas > 0

def resetear_password_superadmin(username, nueva_password):
    pwd_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("UPDATE usuarios SET password_hash = ? WHERE username = ?", (pwd_hash, username))
    filas_afectadas = c.rowcount
    
    conn.commit()
    conn.close()
    
    return filas_afectadas > 0

def registrar_auditoria(empresa_id, usuario, accion, detalle):
    """Guarda un registro inmutable de una acción en el sistema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO auditoria (empresa_id, usuario, accion, detalle) VALUES (?, ?, ?, ?)",
                  (empresa_id, usuario, accion, detalle))
        conn.commit()
    except Exception as e:
        print(f"Error al registrar auditoria: {e}")
    finally:
        conn.close()

def obtener_auditoria(empresa_id=None, limite=100):
    """Devuelve los registros. Si es SuperAdmin (empresa_id=None), ve todo."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if empresa_id:
        c.execute("SELECT usuario, accion, detalle, fecha FROM auditoria WHERE empresa_id = ? ORDER BY fecha DESC LIMIT ?", (empresa_id, limite))
    else:
        c.execute("SELECT empresa_id, usuario, accion, detalle, fecha FROM auditoria ORDER BY fecha DESC LIMIT ?", (limite,))
    
    res = c.fetchall()
    conn.close()
    return res