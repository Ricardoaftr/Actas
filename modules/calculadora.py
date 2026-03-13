import streamlit as st

def calcular_led():
    st.header("Calculadora de Resolución LED")
    st.write("Calcula la resolución final y la cantidad de módulos necesarios según el espacio físico.")

    st.subheader("1. Espacio Disponible")
    col1, col2 = st.columns(2)
    with col1:
        ancho_espacio_m = st.number_input("Ancho del área (metros)", min_value=0.1, value=3.0, step=0.1)
    with col2:
        alto_espacio_m = st.number_input("Alto del área (metros)", min_value=0.1, value=2.0, step=0.1)

    st.subheader("2. Especificaciones del Módulo LED")
    col3, col4, col5 = st.columns(3)
    with col3:
        pitch = st.number_input("Pixel Pitch (mm)", min_value=0.1, max_value=50.0, value=2.5, step=0.1)
    with col4:
        ancho_modulo_mm = st.number_input("Ancho del módulo (mm)", min_value=10, value=320, step=10)
    with col5:
        alto_modulo_mm = st.number_input("Alto del módulo (mm)", min_value=10, value=160, step=10)

    if pitch > 0 and ancho_modulo_mm > 0 and alto_modulo_mm > 0:
        res_ancho_modulo = int(ancho_modulo_mm / pitch)
        res_alto_modulo = int(alto_modulo_mm / pitch)
        
        ancho_espacio_mm = ancho_espacio_m * 1000
        alto_espacio_mm = alto_espacio_m * 1000
        
        modulos_horizontal = int(ancho_espacio_mm // ancho_modulo_mm)
        modulos_vertical = int(alto_espacio_mm // alto_modulo_mm)
        
        ancho_real_m = (modulos_horizontal * ancho_modulo_mm) / 1000
        alto_real_m = (modulos_vertical * alto_modulo_mm) / 1000
        
        res_total_ancho = modulos_horizontal * res_ancho_modulo
        res_total_alto = modulos_vertical * res_alto_modulo
        total_pixeles = res_total_ancho * res_total_alto
        total_modulos = modulos_horizontal * modulos_vertical

        st.divider()
        st.subheader("Resultados de la Instalación")
        
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Resolución Final", f"{res_total_ancho} x {res_total_alto} px")
            st.metric("Total Píxeles", f"{total_pixeles:,}")
        with r2:
            st.metric("Disposición de Módulos", f"{modulos_horizontal} x {modulos_vertical}")
            st.metric("Total Módulos", f"{total_modulos}")
        with r3:
            st.metric("Tamaño Real Pantalla", f"{ancho_real_m:.2f}m x {alto_real_m:.2f}m")
            st.metric("Resolución por Módulo", f"{res_ancho_modulo} x {res_alto_modulo} px")
            
        espacio_sobrante_ancho = (ancho_espacio_m - ancho_real_m) * 100
        espacio_sobrante_alto = (alto_espacio_m - alto_real_m) * 100
        
        st.info(f"Para cubrir el área solicitada se utilizarán {total_modulos} módulos.")
        if espacio_sobrante_ancho > 0 or espacio_sobrante_alto > 0:
            st.caption(f"Nota: Al ajustar los módulos enteros, sobrarán {espacio_sobrante_ancho:.1f} cm a lo ancho y {espacio_sobrante_alto:.1f} cm a lo alto en la estructura.")