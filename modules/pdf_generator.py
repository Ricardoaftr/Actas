import os
import jinja2
import sys
import asyncio
from playwright.sync_api import sync_playwright
from PyPDF2 import PdfMerger

def cargar_plantilla(archivo):
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def unir_pdfs(lista_rutas, salida_path):
    merger = PdfMerger()
    for pdf in lista_rutas:
        if os.path.exists(pdf):
            merger.append(pdf)
    merger.write(salida_path)
    merger.close()

def renderizar_html(template_str, datos):
    template = jinja2.Template(template_str)
    return template.render(datos)

def generar_pdf_playwright(html_final, ruta_pdf):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.set_content(html_final)
        
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
            page.wait_for_timeout(1000) 
        except:
            pass 
            
        page.pdf(
            path=ruta_pdf, 
            format="A4", 
            print_background=True,
            margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"}
        )
        
        browser.close()