import os
import time
import shutil

def limpiar_archivos_temporales(directorio_temp="temp", antiguedad_segundos=3600):
    """
    Borra archivos en el directorio especificado que sean más viejos que 
    el tiempo indicado (por defecto 1 hora).
    """
    if not os.path.exists(directorio_temp):
        return

    ahora = time.time()
    for nombre_archivo in os.listdir(directorio_temp):
        ruta_completa = os.path.join(directorio_temp, nombre_archivo)
        
        # Solo procesar archivos (evitar borrar carpetas críticas si las hay)
        if os.path.isfile(ruta_completa):
            try:
                # Verificar la última fecha de modificación
                fecha_modificacion = os.path.getmtime(ruta_completa)
                
                if (ahora - fecha_modificacion) > antiguedad_segundos:
                    os.remove(ruta_completa)
                    print(f"Limpieza: Archivo {nombre_archivo} eliminado.")
            except Exception as e:
                print(f"Error al limpiar {nombre_archivo}: {e}")