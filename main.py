import streamlit as st
import os
import sys
import asyncio
import re
import time
import base64
import io
import cv2
import numpy as np
import random
import qrcode
import pandas as pd
import sqlite3
import pyotp
import qrcode
from modules.calculadora import calcular_led
from modules.database import obtener_modulos_empresa
from modules.asistente import obtener_respuesta_ia
from modules.database import listar_tareas_tecnico
from modules.database import obtener_secreto_2fa, guardar_secreto_2fa
from modules.database import obtener_auditoria
from modules.database import obtener_auditoria, registrar_auditoria
import extra_streamlit_components as stx
from modules.database import crear_empresa_db, listar_empresas_db, actualizar_plan_empresa_db
from PIL import Image, ImageOps
from datetime import datetime
from modules.database import eliminar_empresa_db, eliminar_usuario_global
from modules.database import obtener_metricas_dashboard
from modules.utils import limpiar_archivos_temporales
from streamlit_drawable_canvas import st_canvas
from streamlit_js_eval import get_geolocation
from dotenv import load_dotenv
from modules.database import resetear_password_superadmin
from modules.database import (crear_tarea_db, listar_tareas_admin)
from modules.database import actualizar_estado_tarea
from modules.database import eliminar_tarea_db, reasignar_tarea_db
from modules.auth import verificar_credenciales
from modules.pdf_generator import cargar_plantilla, renderizar_html, generar_pdf_playwright, unir_pdfs
from modules.drive_service import subir_a_drive_real
from modules.database import (init_db, obtener_siguiente_id, guardar_nuevo_consecutivo, registrar_acta_db, listar_usuarios, crear_usuario, actualizar_password, eliminar_usuario, crear_carpeta_db, listar_carpetas_db, asignar_acta_a_carpeta, obtener_historial_proyectos, obtener_actas_por_proyecto)
from modules.database import (eliminar_carpeta_db,editar_carpeta_db)

st.set_page_config(page_title="Acta Digital", layout="wide")

cookie_manager = stx.CookieManager(key="mngr_principal")

init_db()

if sys.platform == "win32":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

load_dotenv()
ID_CARPETA_DRIVE = os.getenv("ID_CARPETA_DRIVE")
CARPETA_SALIDA = "actas_generadas"

if not os.path.exists(CARPETA_SALIDA):
    os.makedirs(CARPETA_SALIDA)

def vista_superadmin_global():
    st.title("Panel de Control Global - SaaS")
    
    tab1, tab2 = st.tabs(["Gestión de Empresas", "Métricas del Servidor"])
    
    with tab1:
        st.subheader("Registrar Nueva Empresa")

        with st.form("form_nueva_empresa"):
            c1, c2, c3 = st.columns(3)
            nombre_emp = c1.text_input("Nombre de la Empresa")
            plan_emp = c2.selectbox("Plan", ["Basico", "Plus", "Enterprise"])
            carpeta_emp = c3.text_input("ID Carpeta Drive Raíz")
            
            st.markdown("---")
            st.write("Usuario Administrador Principal")
            
            c4, c5, c6 = st.columns(3)
            admin_user = c4.text_input("Usuario Admin").strip().lower().replace(" ", "_")
            admin_pass = c5.text_input("Contraseña", type="password")
            admin_pass_confirm = c6.text_input("Confirmar Contraseña", type="password")
            
            submit = st.form_submit_button("Crear Empresa y Admin")
            
            if submit:
                if not (nombre_emp and admin_user and admin_pass and admin_pass_confirm):
                    st.warning("Por favor, completa todos los campos.")
                elif admin_pass != admin_pass_confirm:
                    st.error("Las contraseñas no coinciden. Inténtalo de nuevo.")
                else:
                    nuevo_id = crear_empresa_db(nombre_emp, plan_emp, carpeta_emp)
                    if crear_usuario(admin_user, admin_pass, "admin", nuevo_id):
                        st.success(f"Empresa {nombre_emp} creada exitosamente con ID: {nuevo_id}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Error al crear el usuario. El nombre podría estar en uso.")

        st.markdown("---")
        st.subheader("Empresas Activas")
        df_empresas = listar_empresas_db()
        
        if not df_empresas.empty:
            for _, emp in df_empresas.iterrows():
                with st.container(border=True):
                    col_info, col_plan = st.columns([3, 1])
                    with col_info:
                        st.write(f"**{emp['nombre']}** (ID: {emp['id']})")
                        st.caption(f"Carpeta Drive: {emp['carpeta_drive_raiz']}")
                    with col_plan:
                        nuevo_plan = st.selectbox("Plan", ["Basico", "Plus", "Enterprise"], 
                                                  index=["Basico", "Plus", "Enterprise"].index(emp['plan']),
                                                  key=f"plan_{emp['id']}", 
                                                  label_visibility="collapsed")
                        if st.button("Actualizar", key=f"btn_plan_{emp['id']}", use_container_width=True):
                            actualizar_plan_empresa_db(emp['id'], nuevo_plan)
                            st.success("Plan actualizado")
                            st.rerun()
        else:
            st.info("No hay empresas registradas en el sistema.")

            
    with tab2:
        st.info("Métricas globales en construcción para la fase PostgreSQL.")

        st.markdown("---")
        st.subheader("Super Admin")
        
        col_peligro1, col_peligro2, col_peligro3 = st.columns(3)
        
        with col_peligro1:
            st.write("### Eliminar Empresa Completa")
            if not df_empresas.empty:
                dict_empresas = {row['nombre']: row['id'] for _, row in df_empresas.iterrows()}
                empresa_a_borrar = st.selectbox("Seleccionar Empresa", list(dict_empresas.keys()))
                
                check_borrar_empresa = st.checkbox(f"Confirmar destrucción de '{empresa_a_borrar}'")
                if check_borrar_empresa:
                    if st.button("Aniquilar Empresa", type="primary"):
                        if eliminar_empresa_db(dict_empresas[empresa_a_borrar]):
                            registrar_auditoria("GLOBAL", st.session_state.username, "ELIMINAR EMPRESA", f"Se destruyó la empresa: {empresa_a_borrar}")
                            st.success("Empresa eliminada de la faz del servidor.")
                            time.sleep(1)
                            st.rerun()
                            st.success("Empresa eliminada de la faz del servidor.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error al eliminar la empresa.")
            else:
                st.info("No hay empresas registradas.")
            
            st.markdown("---")
            st.subheader("Auditoría Global")
            st.info("Registro inmutable de todas las acciones críticas en la plataforma SaaS.")
        
            logs = obtener_auditoria(empresa_id=None, limite=200)
        
            if logs:
                df_logs = pd.DataFrame(logs, columns=["Empresa ID", "Usuario", "Acción", "Detalle", "Fecha/Hora"])
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.write("No hay registros de auditoría todavía.")

        with col_peligro2:
            st.write("Eliminar Admins")
            user_fantasma = st.text_input("Escribe el 'username' exacto a eliminar:")
            
            check_borrar_user = st.checkbox("Confirmar eliminación global")
            if check_borrar_user and user_fantasma:
                if st.button("Eliminar Usuario", type="primary"):
                    if user_fantasma != st.session_state.username:
                        
                        if eliminar_usuario_global(user_fantasma):
                            st.success(f"Usuario '{user_fantasma}' eliminado del sistema.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning(f"El usuario '{user_fantasma}' no existe en la base de datos.")
                            
                    else:
                        st.error("No puedes eliminarte a ti mismo (Super Admin).")

        with col_peligro3:
            st.write("Resetear Contraseña")            
            user_reset = st.text_input("Username del usuario (Admin o Técnico):")
            nueva_pass = st.text_input("Asignar nueva contraseña:", type="password")
            
            if st.button("Forzar Cambio de Clave", type="primary"):
                if user_reset and nueva_pass:
                    if resetear_password_superadmin(user_reset, nueva_pass):
                        st.success(f"¡Éxito! La contraseña de '{user_reset}' ha sido actualizada.")
                    else:
                        st.error(f"El usuario '{user_reset}' no existe en la base de datos.")
                else:
                    st.warning("Debes escribir el usuario y la nueva contraseña.")
                        
        
def limpiar_nombre_archivo(nombre):
    limpio = re.sub(r'[\\/*?:"<>|]', "", nombre)
    return limpio.strip()

def formulario_asignacion_tareas():
    st.header("Asignar Nueva Tarea")
    
    if "checklist_temporal" not in st.session_state:
        st.session_state.checklist_temporal = []
        
    df_tecnicos = listar_usuarios(st.session_state.empresa_id)
    tecnicos = df_tecnicos['username'].tolist() if not df_tecnicos.empty else []
    
    carpetas_data = listar_carpetas_db(st.session_state.empresa_id)
    if isinstance(carpetas_data, pd.DataFrame):
        carpetas_vacias = carpetas_data.empty
    else:
        carpetas_vacias = not bool(carpetas_data)
        
    if carpetas_vacias or not tecnicos:
        st.warning("Debes crear al menos una carpeta/sede y registrar un técnico para poder asignar tareas.")
        return
        
    nombres_carpetas = {c[0]: c[1] for c in carpetas_data}
    nombres_tecnicos = [t for t in tecnicos if t != st.session_state.username]
    
    col1, col2 = st.columns(2)
    with col1:
        proyecto_sel = st.selectbox("Proyecto / Sede", options=list(nombres_carpetas.keys()), format_func=lambda x: nombres_carpetas[x])
        tecnico_sel = st.selectbox("Técnico Asignado", options=nombres_tecnicos)
        prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
    with col2:
        fecha_limite = st.date_input("Fecha Límite")
        descripcion = st.text_area("Descripción de la Tarea")
        
    st.markdown("---")
    st.write("Checklist de Materiales/Herramientas")
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        nuevo_item = st.text_input("Añadir requerimiento", key="input_temp", placeholder="Ej: Kit de instalación TV 55...", label_visibility="collapsed")
    with col_btn:
        if st.button("Añadir", use_container_width=True):
            if nuevo_item.strip():
                st.session_state.checklist_temporal.append(nuevo_item.strip())
                st.rerun()
        
    if st.session_state.checklist_temporal:
        st.write("Ítems requeridos para esta tarea:")
        for i, item in enumerate(st.session_state.checklist_temporal):
            c_texto, c_borrar = st.columns([9, 1])
            with c_texto:
                st.markdown(f"- {item}")
            with c_borrar:
                if st.button("X", key=f"del_chk_{i}"):
                    st.session_state.checklist_temporal.pop(i)
                    st.rerun()
                    
    st.markdown("---")
    
    # Botón final para asignar la tarea
    if st.button("Asignar Tarea al Técnico", type="primary", use_container_width=True):
        if descripcion and tecnico_sel:
            checklist_final = "\n".join(st.session_state.checklist_temporal)
            
            crear_tarea_db(proyecto_sel, tecnico_sel, descripcion, prioridad, fecha_limite, checklist_final, st.session_state.empresa_id)
            
            st.session_state.checklist_temporal = []
            
            st.success("¡Tarea asignada correctamente!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("La descripción y el técnico son campos obligatorios.")

    st.markdown("---")
    st.subheader(" Gestión de Tareas Activas")
    
    df_tareas = listar_tareas_admin(st.session_state.empresa_id)

    if isinstance(df_tareas, pd.DataFrame) and not df_tareas.empty:
            activas = df_tareas[df_tareas['Estado'] != 'Finalizada']
            finalizadas = df_tareas[df_tareas['Estado'] == 'Finalizada']
            
            st.subheader("Tareas Activas")
            if not activas.empty:
                for _, tarea in activas.iterrows():
                    with st.container(border=True):
                        c_info, c_reasignar, c_eliminar = st.columns([4, 2, 1])
                        
                        with c_info:
                            st.write(f"**{tarea['Descripcion']}**")
                            st.caption(f"Sede: {tarea['Proyecto']} | Técnico: {tarea['Tecnico']} | Estado: {tarea['Estado']}")
                            
                        with c_reasignar:
                            nuevo_tec = st.selectbox(
                                "Reasignar a:", 
                                options=nombres_tecnicos, 
                                index=None, 
                                placeholder="Seleccionar técnico para reasignar...",
                                key=f"re_sel_{tarea['ID']}", 
                                label_visibility="collapsed"
                            )
                            
                            if st.button("Reasignar", key=f"re_btn_{tarea['ID']}", use_container_width=True):
                                if nuevo_tec:
                                    reasignar_tarea_db(tarea['ID'], nuevo_tec, st.session_state.empresa_id)
                                    st.success(f"Reasignada a {nuevo_tec}")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.warning("Por favor, selecciona un técnico primero.")
                                    
                        with c_eliminar:
                            if st.button("Eliminar", key=f"del_{tarea['ID']}", type="primary", use_container_width=True):
                                eliminar_tarea_db(tarea['ID'],st.session_state.empresa_id)
                                st.rerun()
            else:
                st.info("No hay tareas pendientes ni en proceso.")
                
            st.subheader("Historial de Tareas Finalizadas")
            if not finalizadas.empty:
                st.dataframe(finalizadas, use_container_width=True)
            else:
                st.info("Aun no hay tareas finalizadas.")
                
    else:
         st.info("No hay tareas registradas en el sistema.")
    

def vista_tareas_tecnico():
    st.header("Mis Tareas Asignadas")
    
    df_tareas = listar_tareas_tecnico(st.session_state.username, st.session_state.empresa_id)
    
    if isinstance(df_tareas, pd.DataFrame) and not df_tareas.empty:
        activas = df_tareas[df_tareas['Estado'] != 'Finalizada']
        finalizadas = df_tareas[df_tareas['Estado'] == 'Finalizada']
        
        st.subheader("Tareas Activas")
        if not activas.empty:
            for _, tarea in activas.iterrows():
                with st.expander(f"{tarea['Proyecto']} - {tarea['Prioridad']}"):
                    st.write(f"**Descripcion:** {tarea['Descripcion']}")
                    st.write(f"**Fecha Limite:** {tarea['Fecha Limite']}")
                    st.write(f"**Estado Actual:** {tarea['Estado']}")
                    
                    todos_marcados = True
                    if tarea['Checklist']:
                        st.write("**Checklist de requisitos:**")
                        items = [i.strip() for i in str(tarea['Checklist']).split('\n')]
                        for idx, item in enumerate(items):
                            if item:
                                marcado = st.checkbox(item, key=f"chk_{tarea['ID']}_{idx}")
                                if not marcado:
                                    todos_marcados = False
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if tarea['Estado'] == 'Pendiente':
                            if st.button("Iniciar Tarea", key=f"iniciar_{tarea['ID']}", disabled=not todos_marcados, use_container_width=True):
                                actualizar_estado_tarea(tarea['ID'], 'En Proceso', st.session_state.empresa_id)
                                st.rerun()
                    with col2:
                        if tarea['Estado'] == 'En Proceso':
                            if st.button("Finalizar Tarea", key=f"fin_{tarea['ID']}", disabled=not todos_marcados, use_container_width=True):
                                actualizar_estado_tarea(tarea['ID'], 'Finalizada',st.session_state.empresa_id)
                                st.rerun()
        else:
            st.info("No tienes tareas activas en este momento.")
            
        st.subheader("Historial de Tareas Finalizadas")
        if not finalizadas.empty:
            st.dataframe(finalizadas, use_container_width=True)
    else:
        st.info("No tienes tareas asignadas.")

def vista_asistente_ia():
    st.header("Asistente Tecnico IA")
    st.write("Realiza consultas sobre manuales, instalaciones y configuraciones.")

    if "mensajes_chat" not in st.session_state:
        st.session_state.mensajes_chat = []

    for mensaje in st.session_state.mensajes_chat:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    if prompt := st.chat_input("Escribe tu pregunta detallada aqui..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.mensajes_chat.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Consultando manuales locales..."):
                respuesta, fuentes = obtener_respuesta_ia(prompt)
                
                if fuentes != "Error" and fuentes != "":
                    respuesta_completa = f"{respuesta}\n\n*Fuentes consultadas: {fuentes}*"
                else:
                    respuesta_completa = respuesta

                st.markdown(respuesta_completa)
        
        st.session_state.mensajes_chat.append({"role": "assistant", "content": respuesta_completa})

def login_screen():
    st.title("Acceso al Sistema")
    
    if st.session_state.get("esperando_2fa", False):
        st.subheader("Autenticacion de Dos Pasos (2FA)")
        user_temp = st.session_state.temp_user
        rol_temp = st.session_state.temp_rol
        emp_temp = st.session_state.temp_emp_id
        
        secreto_guardado = obtener_secreto_2fa(user_temp)
        
        if not secreto_guardado:
            if "nuevo_secreto" not in st.session_state:
                st.session_state.nuevo_secreto = pyotp.random_base32()
            secreto_actual = st.session_state.nuevo_secreto
            
            uri = pyotp.totp.TOTP(secreto_actual).provisioning_uri(name=user_temp, issuer_name="Plataforma_SaaS")
            
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(uri)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            st.info("Configuracion Inicial: Escanea este codigo con Google Authenticator o Authy.")
            st.image(img_qr.get_image())
        else:
            secreto_actual = secreto_guardado
            st.info("Ingresa el codigo de 6 digitos de tu aplicacion autenticadora.")
        
        with st.form("form_2fa"):
            codigo = st.text_input("Codigo de 6 digitos:", max_chars=6)
            if st.form_submit_button("Verificar y Entrar", type="primary"):
                totp = pyotp.TOTP(secreto_actual)
                if totp.verify(codigo):
                    if not secreto_guardado:
                        guardar_secreto_2fa(user_temp, secreto_actual)
                        
                    st.session_state.logged_in = True
                    st.session_state.username = user_temp
                    st.session_state.rol = rol_temp
                    st.session_state.empresa_id = emp_temp
                    
                    token_val = f"{user_temp}|{rol_temp}|{emp_temp}"
                    cookie_manager.set("token_sesion", token_val, expires_at=datetime.now() + pd.Timedelta(days=1))
                    st.query_params["session"] = token_val
                    
                    st.session_state.esperando_2fa = False
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Codigo incorrecto o expirado.")
        
        if st.button("Volver atras"):
            st.session_state.esperando_2fa = False
            st.rerun()
            
        return
    
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit_button = st.form_submit_button("Ingresar")

        if submit_button:
            exito, user, rol, empresa_id, mensaje_error = verificar_credenciales(username, password)
            if exito:
                if rol in ["superadmin", "admin"]:
                    st.session_state.esperando_2fa = True
                    st.session_state.temp_user = user
                    st.session_state.temp_rol = rol
                    st.session_state.temp_emp_id = empresa_id
                    st.rerun()
                else:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.rol = rol
                    st.session_state.empresa_id = empresa_id
                    
                    token_val = f"{user}|{rol}|{empresa_id}"
                    cookie_manager.set("token_sesion", token_val, expires_at=datetime.now() + pd.Timedelta(days=1))
                    st.query_params["session"] = token_val
                    
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.error(mensaje_error)


def vista_gestion_proyectos():
    st.subheader("Explorador de Proyectos y Archivos")
    
    if "folder_actual_id" not in st.session_state:
        st.session_state.folder_actual_id = None
    if "folder_actual_nom" not in st.session_state:
        st.session_state.folder_actual_nom = None

    t1, t2, t3 = st.tabs(["Clasificar Actas", "Explorador de Carpetas", "Impresion Masiva"])
    
    with t1:
        st.write("Actas en Bandeja de Entrada")
        conn = sqlite3.connect("data/database.sqlite")
        
        query = "SELECT id_acta, usuario, proyecto_texto_libre, fecha FROM registros_actas WHERE carpeta_id IS NULL AND empresa_id = ?"
        df_pendientes = pd.read_sql_query(query, conn, params=(st.session_state.empresa_id,))
        
        conn.close()

        if not df_pendientes.empty:
            st.dataframe(df_pendientes, use_container_width=True)
            
            carpetas = listar_carpetas_db(st.session_state.empresa_id)
            
            if carpetas:
                with st.form("form_clasificar"):
                    acta_sel = st.selectbox("Seleccionar Acta", df_pendientes["id_acta"].tolist())
                    dict_c = {c[1]: c[0] for c in carpetas}
                    destino = st.selectbox("Mover a carpeta oficial:", list(dict_c.keys()))
                    
                    if st.form_submit_button("Confirmar Clasificacion"):
                        asignar_acta_a_carpeta(acta_sel, dict_c[destino], st.session_state.empresa_id)
                        st.success("Acta movida correctamente.")
                        st.rerun()
            else:
                st.warning("Debes crear una carpeta en el 'Explorador de Carpetas' primero para poder clasificar las actas.")
        else:
            st.info("No hay actas pendientes de clasificar.")

    with t2:
        if st.session_state.folder_actual_id is None:
            with st.expander("Crear Nueva Carpeta / Proyecto"):
                with st.form("nueva_cap"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        nom = st.text_input("Nombre de la Carpeta")
                    with col2:
                        col = st.color_picker("Color de Etiqueta", "#8AC7FA")
                    not_ = st.text_area("Notas / Recordatorios")
                    if st.form_submit_button("Crear Carpeta"):
                        if crear_carpeta_db(nom, col, not_, st.session_state.empresa_id):
                            st.success("Carpeta creada")
                            st.rerun()
                        else:
                            st.error("La carpeta ya existe")
            
            st.markdown("---")
            
            carpetas_list = listar_carpetas_db(st.session_state.empresa_id)
            if carpetas_list:
                for c in carpetas_list:
                    with st.container(border=True):
                        col_color, col_info, col_abrir, col_opt = st.columns([1, 6, 2, 1])
                        
                        with col_color:
                            st.markdown(f"<div style='width: 25px; height: 25px; border-radius: 5px; background-color: {c[2]}; margin-top: 5px;'></div>", unsafe_allow_html=True)
                            
                        with col_info:
                            st.markdown(f"**{c[1]}**")
                            if c[3]:
                                st.caption(c[3])
                                
                        with col_abrir:
                            if st.button("Abrir", key=f"abrir_{c[0]}", use_container_width=True):
                                st.session_state.folder_actual_id = c[0]
                                st.session_state.folder_actual_nom = c[1]
                                st.rerun()
                                
                        with col_opt:
                            with st.popover("...", use_container_width=True):
                                with st.form(f"edit_{c[0]}"):
                                    enom = st.text_input("Nombre", value=c[1])
                                    ecol = st.color_picker("Color", value=c[2])
                                    enot = st.text_area("Notas", value=c[3])
                                    if st.form_submit_button("Guardar", use_container_width=True):
                                        editar_carpeta_db(c[0], enom, ecol, enot, st.session_state.empresa_id)
                                        st.rerun()
                                st.markdown("---")
                                st.warning("Acción irreversible")
                                confirmacion = st.checkbox("Confirmar eliminación", key=f"chk_del_{c[0]}")
                                
                                if confirmacion:
                                    if st.button("Eliminar Definitivamente", key=f"del_{c[0]}", type="primary", use_container_width=True):
                                        eliminar_carpeta_db(c[0], st.session_state.empresa_id)
                                        # REGISTRO
                                        registrar_auditoria(st.session_state.empresa_id, st.session_state.username, "ELIMINAR CARPETA", f"Se eliminó la carpeta: {c[1]}")
                                        st.rerun()
            else:
                st.info("No hay carpetas creadas.")
        else:
            if st.button("Volver al inicio"):
                st.session_state.folder_actual_id = None
                st.session_state.folder_actual_nom = None
                st.rerun()
                
            st.markdown(f"### Contenido de: **{st.session_state.folder_actual_nom}**")
            
            actas_en_carpeta = obtener_actas_por_proyecto(st.session_state.folder_actual_nom, st.session_state.empresa_id)
            if actas_en_carpeta:
                df_interna = pd.DataFrame(actas_en_carpeta, columns=["ID", "Tecnico", "Nombre", "Fecha", "Ruta", "C_ID", "Empresa_ID"])
                st.table(df_interna[["ID", "Tecnico", "Fecha", "Nombre"]])
                
                with st.expander("Mover archivo a otra carpeta"):
                    acta_id_mover = st.selectbox("Elegir ID de acta", df_interna["ID"].tolist())
                    todas_c = listar_carpetas_db(st.session_state.empresa_id)
                    dict_all = {c[1]: c[0] for c in todas_c}
                    nueva_c = st.selectbox("Mover a:", list(dict_all.keys()))
                    if st.button("Ejecutar Cambio"):
                        asignar_acta_a_carpeta(acta_id_mover, dict_all[nueva_c],st.session_state.empresa_id)
                        st.rerun()
            else:
                st.info("Esta carpeta esta vacia.")

    with t3:
        carpetas = listar_carpetas_db(st.session_state.empresa_id)
        if carpetas:
            sel_nombre = st.selectbox("Seleccionar carpeta para imprimir", [c[1] for c in carpetas])
            actas_print = obtener_actas_por_proyecto(sel_nombre, st.session_state.empresa_id)
            
            if actas_print:
                df_p = pd.DataFrame(actas_print, columns=["ID", "Tecnico", "Nombre", "Fecha", "Ruta", "C_ID", "Empresa_ID"])
                st.write(f"Se unificaran {len(df_p)} archivos.")
                
                if st.button("Generar y Descargar PDF Unificado"):
                    rutas = df_p["Ruta"].tolist()
                    rutas_validas = [r for r in rutas if os.path.exists(r)]
                    
                    if not rutas_validas:
                        st.error("Los archivos PDF no estan en el servidor local.")
                    else:
                        with st.spinner("Uniendo archivos..."):
                            salida = os.path.join(CARPETA_SALIDA, f"Tanda_{sel_nombre}.pdf")
                            unir_pdfs(rutas_validas, salida)
                            with open(salida, "rb") as f:
                                st.download_button("Descargar PDF final", f, file_name=f"Tanda_{sel_nombre}.pdf")
            else:
                st.info("Esta carpeta no tiene archivos asignados.")

def admin_dashboard():
    st.header("Consola de Administracion")
    limpiar_archivos_temporales("temp", 3600)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Proyectos y Carpetas", 
        "Metricas y KPIs", 
        "Gestion de Usuarios", 
        "Google Drive",
        "Seguridad"
    ])

    with tab1:
        vista_gestion_proyectos()

    with tab2:
        st.subheader("Rendimiento del Equipo")
        
        t_actas, t_tareas, actas_vinc, actas_indep, actas_usr = obtener_metricas_dashboard(st.session_state.empresa_id)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Actas Elaboradas", t_actas)
        col2.metric("Tareas Asignadas", t_tareas)
        col3.metric("Actas Vinculadas", actas_vinc)
        col4.metric("Actas Independientes", actas_indep)
        
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.write("Origen de las Actas")
            df_origen = pd.DataFrame({
                "Categoria": ["Vinculadas a Tareas", "Independientes"],
                "Cantidad": [actas_vinc, actas_indep]
            })
            st.bar_chart(df_origen.set_index("Categoria"))
            
        with col_g2:
            st.write("Productividad por Tecnico")
            if actas_usr:
                df_usuarios = pd.DataFrame(actas_usr, columns=["Usuario", "Cantidad"])
                st.bar_chart(df_usuarios.set_index("Usuario"))
            else:
                st.info("No hay datos de actas para mostrar.")

    with tab3:
            st.subheader("Gestion de Usuarios")
            
            st.markdown("""
                <style>
                input[type="password"]::-ms-reveal,
                input[type="password"]::-ms-clear {
                    display: none;
                }
                </style>
            """, unsafe_allow_html=True)
            
            df_usuarios = listar_usuarios(st.session_state.empresa_id)
            if not df_usuarios.empty:
                usuarios_lista = df_usuarios['username'].tolist()
            else:
                usuarios_lista = []

            if usuarios_lista:
                st.write("Modificar o Eliminar Usuario")
                user_to_mod = st.selectbox("Seleccionar Usuario", usuarios_lista)
                col1, col2 = st.columns(2)
                
                with col1:
                    nueva_pass = st.text_input("Nueva Contraseña", type="password")
                    if st.button("Actualizar Contraseña"):
                        if nueva_pass:
                            actualizar_password(user_to_mod, nueva_pass, st.session_state.empresa_id)
                            st.success("Contraseña actualizada")
                        else:
                            st.warning("Escribe una contraseña valida")
                            
                with col2:
                    st.write("")
                    st.write("")
                    
                    if st.button("Eliminar Usuario", type="secondary"):
                        st.session_state.confirmar_eliminacion = user_to_mod

                if st.session_state.get("confirmar_eliminacion") == user_to_mod:
                    st.error(f"Advertencia: ¿Estas totalmente seguro de eliminar al usuario '{user_to_mod}'?")
                    c_conf1, c_conf2 = st.columns(2)
                    with c_conf1:
                        if st.button("Si, eliminar definitivamente", type="primary"):
                            if user_to_mod != st.session_state.username:
                                eliminar_usuario(user_to_mod, st.session_state.empresa_id)
                                st.success("Usuario eliminado")
                                st.session_state.confirmar_eliminacion = None
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Proteccion de sistema: No puedes eliminarte a ti mismo.")
                    with c_conf2:
                        if st.button("Cancelar"):
                            st.session_state.confirmar_eliminacion = None
                            st.rerun()
            
            st.markdown("---")
            st.write("Registrar Nuevo Usuario")
            
            with st.form("crear_u", clear_on_submit=True):
                u = st.text_input("Nuevo Usuario (Tecnico)").strip().lower().replace(" ", "_")
                p = st.text_input("Clave", type="password")
                r = "tecnico" 
                
                if st.form_submit_button("Registrar Tecnico"):
                    if u and p:
                        if crear_usuario(u, p, r, st.session_state.empresa_id):
                            st.success("Tecnico creado exitosamente")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error al crear. El nombre de usuario ya existe.")
                    else:
                        st.warning("Por favor completa todos los campos.")

    with tab4:
        st.subheader("Variables del Sistema")
        st.text_input("ID Carpeta Google Drive", value=ID_CARPETA_DRIVE)
        st.button("Guardar Configuracion")
            
    with tab5:
        st.subheader("Registro de Auditoria")
        st.info("Log de seguridad: Monitoreo de accesos y cambios en la base de datos.")

def vista_historial_actas():
    st.header("Historial Global de Actas")
    st.write("Visualiza todas las actas generadas por tus técnicos.")
    
    conn = sqlite3.connect("data/database.sqlite")
    query = """
        SELECT r.id_acta as ID, r.usuario as Tecnico, r.fecha as Fecha, c.nombre as Proyecto, r.ruta_archivo as Enlace
        FROM registros_actas r
        LEFT JOIN carpetas_proyectos c ON r.carpeta_id = c.id
        WHERE r.empresa_id = ?
        ORDER BY r.fecha DESC
    """
    try:
        df_actas = pd.read_sql_query(query, conn, params=(st.session_state.empresa_id,))
    except Exception:
        df_actas = pd.DataFrame()
    conn.close()
    
    if not df_actas.empty:
        st.dataframe(df_actas, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay actas registradas en el sistema para tu empresa.")

def vista_mis_tareas_tecnico():
    st.title("Mis Tareas Pendientes")
    df_todas = listar_tareas_admin(st.session_state.empresa_id)
    
    if not df_todas.empty:
        mis_tareas = df_todas[df_todas['tecnico'] == st.session_state.username]
        if not mis_tareas.empty:
            for _, tarea in mis_tareas.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    
                    with c1:
                        st.write(f"### Sede: {tarea['nombre']}")
                        st.write(f"**Tarea:** {tarea['descripcion']}")
                        st.caption(f"Prioridad: {tarea['Prioridad']} | Límite: {tarea['Fecha_limite']}")
                        
                        # Lectura robusta evitar errores 'NaN'
                        valor_chk = tarea['checklist'] if 'checklist' in tarea else ""
                        if pd.isna(valor_chk) or valor_chk is None or str(valor_chk).lower() == "nan":
                            valor_chk = ""
                            
                        items_checklist = [i.strip() for i in str(valor_chk).split('\n') if i.strip() and i.strip().lower() != "nan"]
                        todo_marcado = True
                        
                        if items_checklist and tarea['estado'] == "Pendiente":
                            st.markdown("---")
                            st.write("**Checklist de Preparación:**")
                            for item in items_checklist:
                                check = st.checkbox(item, key=f"chk_{tarea['ID']}_{item}")
                                if not check:
                                    todo_marcado = False
                        
                    with c2:
                        st.write(f"Estado: **{tarea['estado']}**")
                        
                        if tarea['estado'] == "Pendiente":
                            if st.button("Iniciar Trabajo", disabled=not todo_marcado, key=f"start_{tarea['ID']}", use_container_width=True):
                                actualizar_estado_tarea(tarea['ID'], "En Proceso", st.session_state.empresa_id)
                                st.success("Tarea iniciada")
                                st.rerun()
                                
                        elif tarea['estado'] == "En Proceso":
                            if st.button("Realizar Acta", key=f"do_{tarea['ID']}", type="primary", use_container_width=True):
                                st.session_state.proyecto_prellenado = tarea['nombre']
                                st.session_state.tarea_actual_id = tarea['ID'] 
                                st.info(f"Ve a 'Formulario de Acta'. Sede {tarea['nombre']} seleccionada.")
        else:
            st.info("No tienes tareas pendientes.")
    else:
        st.info("No hay tareas registradas.")

def formulario_acta():
    st.title("Generar Acta con Firma")
    html_template = cargar_plantilla("templates/plantilla.html")
    if not html_template:
        st.error("Falta el archivo plantilla.html en templates/")
        st.stop()

    with st.form("form_completo"):
        st.subheader("1. Datos Generales")
        c1, c2 = st.columns(2)
        with c1:
            # 1. Obtenemos el ID enviando el empresa_id
            id_acta = obtener_siguiente_id(st.session_state.empresa_id)
            st.text_input("ID Acta", value=id_acta, disabled=True)
            fecha = st.date_input("Fecha", datetime.today())
        with c2:
            ciudad = st.text_input("Ciudad", value="Cali")
            proyecto = st.text_input("Nombre del Proyecto")

        st.subheader("2. Detalles de lo Entregado")
        direccion = st.text_input("Direccion de Entrega")
        
        col_det1, col_det2 = st.columns([1, 3])
        with col_det1:
            cantidad = st.number_input("Cant.", min_value=1, value=1, key="cant1")
        with col_det2:
            texto1 = st.text_input("Descripcion Item 1")
            
        col_det3, col_det4 = st.columns([1, 3])
        with col_det3:
            cantidad2 = st.number_input("Cant.", min_value=0, value=0, key="cant2")
        with col_det4:
            texto2 = st.text_input("Descripcion Item 2 (Opcional)")

        texto3 = st.text_area("Observaciones Adicionales")
        
        st.markdown("Datos del Contratante")
        contratante = st.text_input("Empresa quien recibe") 

        c_cli1, c_cli2, c_cli3 = st.columns([2, 1, 1])
        with c_cli1:
            nombre_contratante = st.text_input("Persona encargada de quien recibe")
        with c_cli2:
            tipo_doc_opcion = st.selectbox("Tipo", ["CC", "NIT"])
        with c_cli3:
            numero_nit_contratante = st.text_input("Numero (NIT/CC)")

        st.markdown("Datos del Colaborador")
        c_cont1, c_cont2 = st.columns(2)
        with c_cont1:
            nombre_contratista = st.text_input("Nombre del Colaborador", value=st.session_state.username, disabled=True)

        st.subheader("4. Firma de Recibido")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)", 
            stroke_width=2,
            stroke_color="#000000",
            background_color="#EEEEEE",
            height=150,
            drawing_mode="freedraw",
            key="canvas_firma",
            display_toolbar=True
        )

        st.subheader("5. Sello Fisico")
        archivo_sello_fisico = st.file_uploader("Seleccionar foto del sello", type=['png', 'jpg', 'jpeg'])

        st.subheader("6. Evidencias Fotograficas")
        imagenes_subidas = st.file_uploader(
            "Seleccionar fotos de prueba", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True
        )

        loc = get_geolocation()
        enviado = st.form_submit_button("ENVIAR ACTA", type="primary")

    if enviado:
        campos_vacios = []
        if not ciudad.strip(): campos_vacios.append("Ciudad")
        if not proyecto.strip(): campos_vacios.append("Nombre del Proyecto")
        if not direccion.strip(): campos_vacios.append("Direccion")
        if not texto1.strip(): campos_vacios.append("Item 1")
        if not contratante.strip(): campos_vacios.append("Empresa")
        if not nombre_contratante.strip(): campos_vacios.append("Persona")
        if not numero_nit_contratante.strip(): campos_vacios.append("NIT/CC")

        if campos_vacios:
            st.error(f"Faltan campos: {', '.join(campos_vacios)}")
            st.stop()

        if not loc or 'coords' not in loc:
            st.error("Ubicacion GPS obligatoria.")
            st.stop()

        if not archivo_sello_fisico:
            st.error("Sello fisico obligatorio.")
            st.stop()

        if not imagenes_subidas or len(imagenes_subidas) == 0:
            st.error("Subir al menos una foto.")
            st.stop()

        firma_b64 = ""
        if canvas_result.image_data is not None:
            try:
                img_data = canvas_result.image_data
                img = Image.fromarray(img_data.astype('uint8'), 'RGBA')
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    firma_b64 = f"data:image/png;base64,{img_str}"
            except:
                pass

        if not firma_b64:
            st.error("Firma obligatoria.")
            st.stop()

        lista_imagenes_b64 = []
        for archivo_img in imagenes_subidas:
            try:
                img = Image.open(archivo_img)
                img.thumbnail((500, 500))
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=55)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                lista_imagenes_b64.append(f"data:image/jpeg;base64,{img_str}")
            except:
                pass

        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        lat_lon_str = f"{lat}, {lon}"
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"

        info_qr = f"ID: {id_acta}\nProyecto: {proyecto}\nUbicacion: {maps_link}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(info_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        buffered_qr = io.BytesIO()
        img_qr.save(buffered_qr, format="PNG")
        qr_b64 = f"data:image/png;base64,{base64.b64encode(buffered_qr.getvalue()).decode()}"
        
        sello_procesado_b64 = ""
        pos_x_css = "0%"
        pos_y_css = "0px"
        rot_css = "0deg"

        try:
            image_pil = Image.open(archivo_sello_fisico)
            image_pil = ImageOps.exif_transpose(image_pil) 
            image_pil = image_pil.convert("RGB")
            img = np.array(image_pil)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            max_dim = 1000
            if max(img.shape) > max_dim:
                scale = max_dim / max(img.shape)
                img = cv2.resize(img, None, fx=scale, fy=scale)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 15)
            alpha = cv2.bitwise_not(thresh)

            kernel = np.ones((2,2), np.uint8)
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)

            b, g, r = cv2.split(img)
            rgba = cv2.merge([b, g, r, alpha])

            _, buffer_sello = cv2.imencode('.png', rgba)
            sello_procesado_b64 = f"data:image/png;base64,{base64.b64encode(buffer_sello).decode()}"

            pos_x_css = f"{random.randint(35, 65)}%" 
            pos_y_css = f"{random.randint(-30, 0)}px"
            rot_css = f"{random.randint(-10, 10)}deg"
        except:
            pass

        datos = {
            "id_acta": id_acta,
            "fecha": fecha.strftime("%d/%m/%Y"),
            "ciudad": ciudad,
            "proyecto": proyecto,
            "direccion": direccion,
            "cantidad": cantidad,
            "texto1": texto1,
            "cantidad2": cantidad2 if cantidad2 > 0 else "",
            "texto2": texto2,
            "texto3": texto3,
            "contratante": contratante,
            "numero_nit_contratante": numero_nit_contratante,
            "nombre_contratante": nombre_contratante,
            "nombre_contratista": nombre_contratista,
            "tipo_documento": tipo_doc_opcion,
            "lista_imagenes": lista_imagenes_b64,
            "firma_imagen": firma_b64,
            "qr_imagen": qr_b64,
            "coordenadas": lat_lon_str,
            "sello_imagen": sello_procesado_b64,
            "sello_x": pos_x_css,
            "sello_y": pos_y_css,
            "sello_rot": rot_css
        }

        titulo_limpio = limpiar_nombre_archivo(proyecto)
        if not titulo_limpio:
            titulo_limpio = "Acta"

        nombre_proyecto_carpeta = titulo_limpio
        ruta_carpeta_proyecto = os.path.join(CARPETA_SALIDA, nombre_proyecto_carpeta)

        if not os.path.exists(ruta_carpeta_proyecto):
            os.makedirs(ruta_carpeta_proyecto)

        nombre_pdf = f"{titulo_limpio} - {id_acta}.pdf"
        ruta_pdf = os.path.join(CARPETA_SALIDA, nombre_pdf)

        with st.spinner("Procesando..."):
            html_final = renderizar_html(html_template, datos)
            generar_pdf_playwright(html_final, ruta_pdf)

        exito = subir_a_drive_real(ruta_pdf, nombre_pdf, ID_CARPETA_DRIVE)
        
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)

        # 3. Bug corregido: Toda la logica de exito, actas y tareas agrupada al final
        if exito:
            guardar_nuevo_consecutivo(st.session_state.empresa_id)
            registrar_acta_db(id_acta, st.session_state.username, nombre_proyecto_carpeta, fecha.strftime("%Y-%m-%d"), ruta_pdf, carpeta_id=None, empresa_id=st.session_state.empresa_id)
            registrar_auditoria(st.session_state.empresa_id, st.session_state.username, "CREAR ACTA", f"Generó el acta {id_acta} para el proyecto {proyecto}")
            
            # Si el acta proviene de una tarea, se actualiza aqui mismo antes de reiniciar
            if "tarea_actual_id" in st.session_state:
                actualizar_estado_tarea(st.session_state.tarea_actual_id, "Finalizada", st.session_state.empresa_id)
                del st.session_state.tarea_actual_id 

            st.success(f"Acta {id_acta} enviada y registrada con exito.")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Error al subir el acta a Google Drive.")               

# --- MANEJO DE SESION Y PERSISTENCIA ---

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

token_url = st.query_params.get("session")
token_cookie = cookie_manager.get(cookie="token_sesion")

token_activo = token_url if token_url else token_cookie

if not st.session_state.logged_in and token_activo:
    partes = str(token_activo).split("|")
    if len(partes) == 3:
        user_token, rol_token, emp_token = partes
        st.session_state.logged_in = True
        st.session_state.username = user_token
        st.session_state.rol = rol_token
        st.session_state.empresa_id = emp_token
        
        if not token_url:
            st.query_params["session"] = token_activo
            
        st.rerun()

if not st.session_state.logged_in:
    login_screen()
    st.stop()

st.sidebar.title("Menu")
st.sidebar.write(f"Usuario: **{st.session_state.username}**")

if st.sidebar.button("Cerrar Sesion"):
    st.cache_data.clear()
    st.cache_resource.clear()
    
    import datetime
    fecha_expiracion = datetime.datetime.now() - datetime.timedelta(days=1)
    try:
        cookie_manager.set("token_sesion", "", expires_at=fecha_expiracion, key="forzar_cierre")
    except Exception:
        pass
        
    st.query_params.clear()
    
    for key in list(st.session_state.keys()):
        del st.session_state[key]
        
    st.session_state.logged_in = False
    
    time.sleep(1.5) 
    st.rerun()

if st.session_state.rol == "superadmin":
    opciones_menu = ["Panel Global SaaS"]
    opcion = st.sidebar.selectbox("Navegacion", opciones_menu)
    
    if opcion == "Panel Global SaaS":
        vista_superadmin_global()

if st.session_state.rol in ["admin", "tecnico"]:
    modulos_crudos = obtener_modulos_empresa(st.session_state.empresa_id)
    modulos = [str(m).strip().lower() for m in modulos_crudos]
    
    opciones_menu = []
    
    if "actas" in modulos:
        opciones_menu.append("Generar Acta")
          
    if "dashboard" in modulos and st.session_state.rol == "admin":
        opciones_menu.append("Dashboard")

    if "tareas" in modulos:
        opciones_menu.append("Tareas")
        

    if "asistente ia" in modulos and st.session_state.rol == "tecnico":
        opciones_menu.append("Asistente IA")
        
    seleccion = st.sidebar.radio("Navegacion", opciones_menu)
    
    if seleccion == "Generar Acta":
        formulario_acta()
        
    elif seleccion == "Tareas":
        if st.session_state.rol == "admin":
            formulario_asignacion_tareas()
        elif st.session_state.rol == "tecnico":
            vista_tareas_tecnico()
            
    elif seleccion == "Dashboard":
        admin_dashboard()
        
    elif seleccion == "Calculadora LED":
        calcular_led()
        
    elif seleccion == "Asistente IA":
        if st.session_state.rol == "tecnico":
            vista_asistente_ia()
        else:
            st.warning(" Esta herramienta es de uso exclusivo para el personal técnico.")