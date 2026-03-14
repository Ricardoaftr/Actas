import streamlit as st
import sqlite3

def obtener_gabinetes():
    conn = sqlite3.connect('data/database.sqlite')
    c = conn.cursor()
    c.execute('SELECT id, marca, serie, modelo, pitch, ancho_mm, alto_mm, res_ancho, res_alto, peso_kg, consumo_max_w FROM gabinetes_led')
    gabinetes = c.fetchall()
    conn.close()
    return gabinetes

def guardar_gabinete(datos):
    conn = sqlite3.connect('data/database.sqlite')
    c = conn.cursor()
    c.execute('''
        INSERT INTO gabinetes_led 
        (marca, serie, modelo, pitch, ancho_mm, alto_mm, res_ancho, res_alto, peso_kg, consumo_max_w)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', datos)
    conn.commit()
    conn.close()

def calcular_led():
    st.header("Calculadora de Ingeniería LED")
    
    tab_calc, tab_admin = st.tabs(["Calculadora", "Gestionar Catálogo"])
    
    with tab_calc:
        st.subheader("1. Espacio Disponible")
        col1, col2 = st.columns(2)
        with col1:
            ancho_espacio_m = st.number_input("Ancho del área (metros)", min_value=0.1, value=3.0, step=0.1)
        with col2:
            alto_espacio_m = st.number_input("Alto del área (metros)", min_value=0.1, value=2.0, step=0.1)

        st.subheader("2. Selección de Gabinete")
        gabinetes = obtener_gabinetes()
        
        if not gabinetes:
            st.warning("No hay gabinetes en la base de datos.")
            return
            
        opciones_gabinetes = {f"{g[1]} {g[2]} - {g[3]}": g for g in gabinetes}
        seleccion = st.selectbox("Selecciona el modelo a instalar:", list(opciones_gabinetes.keys()))
        
        gabinete_actual = opciones_gabinetes[seleccion]
        (g_id, marca, serie, modelo, pitch, ancho_mm, alto_mm, res_ancho, res_alto, peso_kg, consumo_max_w) = gabinete_actual
        
        ancho_gabinete_m = ancho_mm / 1000
        alto_gabinete_m = alto_mm / 1000

        st.info(f"Especificaciones técnicas: {ancho_mm}x{alto_mm}mm | Pitch: {pitch} | Resolución: {res_ancho}x{res_alto}px | Peso: {peso_kg}kg | Consumo Max: {consumo_max_w}W")

        modulos_horizontal = int((ancho_espacio_m + 0.0001) / ancho_gabinete_m)
        modulos_vertical = int((alto_espacio_m + 0.0001) / alto_gabinete_m)
        
        ancho_real_m = modulos_horizontal * ancho_gabinete_m
        alto_real_m = modulos_vertical * alto_gabinete_m
        
        res_total_ancho = modulos_horizontal * res_ancho
        res_total_alto = modulos_vertical * res_alto
        total_pixeles = res_total_ancho * res_total_alto
        total_modulos = modulos_horizontal * modulos_vertical

        peso_total_kg = total_modulos * peso_kg
        consumo_total_kw = (total_modulos * consumo_max_w) / 1000

        st.divider()
        st.subheader("3. Resultados de Ingeniería")
        
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Resolución Final", f"{res_total_ancho} x {res_total_alto} px")
            st.metric("Total Píxeles", f"{total_pixeles:,} px")
        with r2:
            st.metric("Matriz (Columnas x Filas)", f"{modulos_horizontal} x {modulos_vertical}")
            st.metric("Total Gabinetes", f"{total_modulos}")
        with r3:
            st.metric("Tamaño Real", f"{ancho_real_m:.2f} m x {alto_real_m:.2f} m")
            st.metric("Carga Estructural (Peso)", f"{peso_total_kg:.1f} kg")
            
        st.metric("Carga Eléctrica Máxima", f"{consumo_total_kw:.2f} kW")
            
        espacio_sobrante_ancho_m = ancho_espacio_m - ancho_real_m
        espacio_sobrante_alto_m = alto_espacio_m - alto_real_m
        
        if espacio_sobrante_ancho_m > 0.001 or espacio_sobrante_alto_m > 0.001:
            st.caption(f"Nota de Estructura: Sobrarán {espacio_sobrante_ancho_m:.2f} m a lo ancho y {espacio_sobrante_alto_m:.2f} m a lo alto.")

    with tab_admin:
        if st.session_state.get('rol') == 'admin':
            st.subheader("Añadir Nuevo Gabinete al Catálogo")
            with st.form("form_nuevo_gabinete"):
                c1, c2 = st.columns(2)
                with c1:
                    marca = st.text_input("Marca", placeholder="Ej: Novastar")
                    serie = st.text_input("Serie/Familia", placeholder="Ej: Serie H")
                    modelo = st.text_input("Modelo", placeholder="Ej: P2.5 Indoor")
                    pitch = st.number_input("Pixel Pitch (mm)", min_value=0.1, value=2.5, format="%.4f")
                    peso = st.number_input("Peso del gabinete (kg)", min_value=0.1, value=7.5, step=0.1)
                with c2:
                    ancho_mm = st.number_input("Ancho (mm)", min_value=10.0, value=500.0, step=1.0)
                    alto_mm = st.number_input("Alto (mm)", min_value=10.0, value=500.0, step=1.0)
                    res_ancho = st.number_input("Resolución Ancho (px)", min_value=1, value=200, step=1)
                    res_alto = st.number_input("Resolución Alto (px)", min_value=1, value=200, step=1)
                    consumo = st.number_input("Consumo Máx (W)", min_value=10, value=150, step=10)
                
                submit = st.form_submit_button("Guardar en Base de Datos")
                
                if submit:
                    if marca and serie and modelo:
                        datos = (marca, serie, modelo, pitch, ancho_mm, alto_mm, res_ancho, res_alto, peso, consumo)
                        guardar_gabinete(datos)
                        st.success("Gabinete guardado exitosamente.")
                        st.rerun()
                    else:
                        st.error("Por favor completa la marca, serie y modelo.")
        else:
            st.warning("Solo los administradores pueden añadir modelos al catálogo.")