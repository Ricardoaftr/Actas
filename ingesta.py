import os
import fitz
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

load_dotenv()

def extraer_texto_pdf(ruta_pdf):
    documentos = []
    
    # Extraemos el nombre de la carpeta donde está el PDF para usarlo como categoría
    categoria = os.path.basename(os.path.dirname(ruta_pdf))
    if categoria == "repositorio_manuales":
        categoria = "General"
        
    try:
        doc = fitz.open(ruta_pdf)
        for num_pagina in range(len(doc)):
            pagina = doc.load_page(num_pagina)
            texto = pagina.get_text("text")
            if texto.strip():
                doc_langchain = Document(
                    page_content=texto,
                    metadata={
                        "source": os.path.basename(ruta_pdf),
                        "page": num_pagina + 1,
                        "path": ruta_pdf,
                        "categoria": categoria  # <- Guardamos la categoría en la base de datos
                    }
                )
                documentos.append(doc_langchain)
    except Exception as e:
        print(f"Error leyendo {ruta_pdf}: {e}")
    return documentos

def procesar_repositorio():
    ruta_repositorio = "repositorio_manuales"
    ruta_db = "data/vector_db"
    
    if not os.path.exists(ruta_repositorio):
        os.makedirs(ruta_repositorio)
        print("Carpeta repositorio_manuales creada.")
        return

    archivos_pdf = []
    
    # os.walk busca en la carpeta principal y en todas las subcarpetas
    for raiz, directorios, archivos in os.walk(ruta_repositorio):
        for archivo in archivos:
            if archivo.lower().endswith('.pdf'):
                archivos_pdf.append(os.path.join(raiz, archivo))
    
    if not archivos_pdf:
        print("No se encontraron archivos PDF en el repositorio ni en sus subcarpetas.")
        return

    documentos_totales = []
    for ruta_completa in archivos_pdf:
        print(f"Procesando: {ruta_completa}...")
        docs = extraer_texto_pdf(ruta_completa)
        documentos_totales.extend(docs)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    fragmentos = text_splitter.split_documents(documentos_totales)
    
    print(f"Generando vectores para {len(fragmentos)} fragmentos...")
    print("Cargando modelo de embeddings local...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Esto sobrescribe la base de datos anterior con la nueva información categorizada
    vector_db = FAISS.from_documents(fragmentos, embeddings)
    vector_db.save_local(ruta_db)
    
    print("Base de datos vectorial creada y guardada con éxito.")

if __name__ == "__main__":
    procesar_repositorio()