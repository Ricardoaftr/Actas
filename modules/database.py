import sqlite3
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (username TEXT PRIMARY KEY, password_hash TEXT, rol TEXT, empresa_id TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS carpetas_proyectos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT UNIQUE, 
                  color TEXT, 
                  notas TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS registros_actas 
                 (id_acta TEXT PRIMARY KEY, 
                  usuario TEXT, 
                  proyecto_texto_libre TEXT, 
                  fecha TEXT, 
                  ruta_archivo TEXT,
                  carpeta_id INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tareas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tecnico TEXT, 
                  proyecto_id INTEGER, 
                  descripcion TEXT, 
                  prioridad TEXT, 
                  estado TEXT, 
                  fecha_asignacion TEXT,
                  fecha_limite TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tareas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tecnico TEXT, 
                  proyecto_id INTEGER, 
                  descripcion TEXT, 
                  prioridad TEXT, 
                  estado TEXT, 
                  fecha_asignacion TEXT,
                  fecha_limite TEXT,
                  checklist TEXT DEFAULT '')''')
    
    
    try:
        c.execute("ALTER TABLE tareas ADD COLUMN checklist TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def crear_tarea_db(proyecto_id, tecnico, descripcion, prioridad, fecha_limite, checklist=""):
    conn = sqlite3.connect(DB_PATH) # AQUÍ ESTABA EL ERROR (antes decía 'actas.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO tareas (proyecto_id, tecnico, descripcion, prioridad, fecha_limite, estado, checklist)
        VALUES (?, ?, ?, ?, ?, 'Pendiente', ?)
    """, (proyecto_id, tecnico, descripcion, prioridad, fecha_limite, checklist))
    conn.commit()
    conn.close()

def listar_tareas_admin():
    conn = sqlite3.connect(DB_PATH)
    query = """SELECT t.*, c.nombre 
               FROM tareas t 
               LEFT JOIN carpetas_proyectos c ON t.proyecto_id = c.id"""
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def actualizar_estado_tarea(id_tarea, nuevo_estado):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tareas SET estado = ? WHERE id = ?", (nuevo_estado, id_tarea))
    conn.commit()
    conn.close()

def obtener_siguiente_id():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave='ultimo_acta'")
    ultimo = c.fetchone()[0]
    conn.close()
    siguiente = ultimo + 1
    return f"ACT-{siguiente:03d}", siguiente

def obtener_usuario(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash, rol, empresa_id FROM usuarios WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def guardar_nuevo_consecutivo(numero):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE configuracion SET valor=? WHERE clave='ultimo_acta'", (numero,))
    conn.commit()
    conn.close()

def crear_usuario(username, password, rol, empresa_id):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", (username, pwd_hash, rol, empresa_id))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def listar_usuarios():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, rol, empresa_id FROM usuarios")
    res = c.fetchall()
    conn.close()
    return res

def actualizar_password(username, nueva_password):
    pwd_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET password_hash = ? WHERE username = ?", (pwd_hash, username))
    conn.commit()
    conn.close()

def eliminar_usuario(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def registrar_acta_db(id_acta, usuario, proyecto, fecha, ruta, carpeta_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO registros_actas VALUES (?, ?, ?, ?, ?, ?)", 
              (id_acta, usuario, proyecto, fecha, ruta, carpeta_id))
    conn.commit()
    conn.close()

def crear_carpeta_db(nombre, color, notas):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO carpetas_proyectos (nombre, color, notas) VALUES (?, ?, ?)", 
                  (nombre, color, notas))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def listar_carpetas_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM carpetas_proyectos")
    res = c.fetchall()
    conn.close()
    return res

def asignar_acta_a_carpeta(id_acta, carpeta_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE registros_actas SET carpeta_id = ? WHERE id_acta = ?", (carpeta_id, id_acta))
    conn.commit()
    conn.close()

def obtener_historial_proyectos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT nombre FROM carpetas_proyectos")
    res = [row[0] for row in c.fetchall()]
    conn.close()
    return res

def obtener_actas_por_proyecto(nombre_carpeta):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT r.* FROM registros_actas r 
                 JOIN carpetas_proyectos c ON r.carpeta_id = c.id 
                 WHERE c.nombre = ?""", (nombre_carpeta,))
    res = c.fetchall()
    conn.close()
    return res

def eliminar_carpeta_db(id_carpeta):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE registros_actas SET carpeta_id = NULL WHERE carpeta_id = ?", (id_carpeta,))
    c.execute("DELETE FROM carpetas_proyectos WHERE id = ?", (id_carpeta,))
    conn.commit()
    conn.close()

def editar_carpeta_db(id_carpeta, nombre, color, notas):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("UPDATE carpetas_proyectos SET nombre = ?, color = ?, notas = ? WHERE id = ?", 
                  (nombre, color, notas, id_carpeta))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def eliminar_tarea_db(id_tarea):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))
    conn.commit()
    conn.close()

def reasignar_tarea_db(id_tarea, nuevo_tecnico):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tareas SET tecnico = ? WHERE id = ?", (nuevo_tecnico, id_tarea))
    conn.commit()
    conn.close()

def obtener_metricas_dashboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM registros_actas")
    total_actas = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tareas WHERE estado = 'Finalizada'")
    actas_vinculadas = c.fetchone()[0]
    
    c.execute("SELECT usuario, COUNT(*) as total FROM registros_actas GROUP BY usuario")
    actas_usuarios = c.fetchall()
    
    conn.close()
    
    actas_independientes = total_actas - actas_vinculadas
    if actas_independientes < 0:
        actas_independientes = 0
        
    return total_actas, total_tareas, actas_vinculadas, actas_independientes, actas_usuarios