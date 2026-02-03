import streamlit as st
import google.generativeai as genai
import json
import os

# --- LISTA DE OPCIONES DE MODELOS ---
MODELOS_DISPONIBLES = {
    "flash_2.0": "gemini-2.0-flash",       # Recomendado: Rápido y moderno
    "flash_lite": "gemini-2.0-flash-lite", # Muy económico
    "pro_latest": "gemini-pro-latest",     # Máxima capacidad de razonamiento
    "gemma_27b": "gemma-3-27b-it",         # Modelo abierto potente
    "experimental": "gemini-exp-1206"      # Versión de prueba avanzada
}

# Selección del modelo actual (Puedes cambiar la clave aquí)
MODELO_ACTUAL = MODELOS_DISPONIBLES["flash_2.0"]

# --- LÓGICA DE AUTENTICACIÓN ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

class GeminiClient:
    def __init__(self):
        if not api_key:
            st.error("⚠️ No se detectó la API KEY de Google.")
            self.model = None 
            return

        try:
            # Iniciamos el modelo seleccionado
            self.model = genai.GenerativeModel(
                MODELO_ACTUAL, 
                generation_config={"response_mime_type": "application/json"}
            )
            print(f"[*] Sistema conectado al modelo: {MODELO_ACTUAL}")
        except Exception as e:
            st.error(f"Error al inicializar el modelo {MODELO_ACTUAL}: {e}")
            self.model = None

    def consultar_nucleo(self, token: str, contexto: str) -> list:
        """Protocolo P4: Análisis etimológico de núcleos léxicos"""
        if not self.model: return []
        
        prompt = f"""
        Actúa como filólogo experto siguiendo el protocolo P4.
        Analiza el token: '{token}'
        Contexto: '{contexto}'
        
        Responde exclusivamente en formato JSON con los campos: 
        termino, origen, raiz, derivacion_existe (bool), es_metafora_viable (bool).
        """
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error en consulta de núcleo ({token}): {e}")
            return []

    def consultar_particula(self, token: str, funcion_sintactica: str) -> list:
        """Protocolo P5: Análisis funcional de partículas"""
        if not self.model: return []

        prompt = f"""
        Actúa como experto gramatical siguiendo el protocolo P5.
        Analiza la partícula: '{token}'
        Función detectada: '{funcion_sintactica}'
        
        Dame candidatos de traducción en JSON con: 
        termino, es_etimologico (bool), cierra_regimen (bool).
        """
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error en consulta de partícula ({token}): {e}")
            return []

# Instancia global para el sistema
ai_engine = GeminiClient()
