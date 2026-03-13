import os
import google.generativeai as genai
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
modelo = genai.GenerativeModel('gemini-1.5-flash')

def obtener_respuesta_ia(pregunta):
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        db = FAISS.load_local("data/vector_db", embeddings, allow_dangerous_deserialization=True)
        
        resultados = db.similarity_search(pregunta, k=4)
        
        contexto = "\n\n".join([doc.page_content for doc in resultados])
        fuentes = list(set([doc.metadata.get("source", "Manual desconocido") for doc in resultados]))
        
        prompt = f"""
        Eres un asistente técnico experto. Responde la pregunta basándote ÚNICAMENTE en el siguiente contexto extraído de manuales técnicos.
        Si la respuesta no está en el contexto, indica estrictamente que no tienes esa información en tu base de datos actual.
        
        CONTEXTO:
        {contexto}
        
        PREGUNTA:
        {pregunta}
        """
        
        respuesta = modelo.generate_content(prompt)
        fuentes_str = ", ".join(fuentes)
        
        return respuesta.text, fuentes_str
        
    except Exception as e:
        return f"Error procesando la consulta: {str(e)}", "Error"