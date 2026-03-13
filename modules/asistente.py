import os
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

def obtener_respuesta_ia(pregunta):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: No se encontró la API Key en el archivo .env", "Error"
            
        api_key = api_key.strip()

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = FAISS.load_local("data/vector_db", embeddings, allow_dangerous_deserialization=True)
        
        resultados = db.similarity_search(pregunta, k=10)
        
        contexto = "\n\n".join([doc.page_content for doc in resultados])
        fuentes = list(set([doc.metadata.get("source", "Manual desconocido") for doc in resultados]))
        
        prompt = f"""
        Eres un asistente técnico experto de soporte en campo. 
        El técnico que te hace la pregunta puede usar nombres acortados, cometer errores ortográficos o no saber el nombre exacto del modelo (por ejemplo, decir "procesadora 300" en lugar de "MCTRL300").
        
        Tu tarea es:
        1. Interpretar la intención real de la pregunta del técnico.
        2. Buscar la respuesta ÚNICAMENTE dentro del CONTEXTO proporcionado.
        3. Si la respuesta está en el contexto, explícala de forma clara y profesional.
        4. Si definitivamente la información técnica para resolver la duda no está en el contexto, indica amablemente que no tienes esa información en la base de manuales.
        
        CONTEXTO TÉCNICO:
        {contexto}
        
        PREGUNTA DEL TÉCNICO:
        {pregunta}
        """
        
        url_models = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        respuesta_modelos = requests.get(url_models)
        
        if respuesta_modelos.status_code != 200:
            return f"Error consultando modelos a Google: {respuesta_modelos.text}", "Error"
            
        modelos_data = respuesta_modelos.json()
        modelo_endpoint = "models/gemini-1.5-flash" 
        
        for m in modelos_data.get('models', []):
            metodos = m.get('supportedGenerationMethods', [])
            nombre = m.get('name', '')
            if 'generateContent' in metodos and 'flash' in nombre:
                modelo_endpoint = nombre
                break 
                
        url = f"https://generativelanguage.googleapis.com/v1beta/{modelo_endpoint}:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        respuesta = requests.post(url, headers=headers, json=data)
        
        if respuesta.status_code == 200:
            respuesta_texto = respuesta.json()['candidates'][0]['content']['parts'][0]['text']
            fuentes_str = ", ".join(fuentes)
            return respuesta_texto, fuentes_str
        else:
            return f"Error en la generación: {respuesta.text}", "Error"
            
    except Exception as e:
        return f"Error procesando la consulta: {str(e)}", "Error"