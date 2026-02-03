import streamlit as st
import google.generativeai as genai
import json
import os

# --- LÓGICA DE AUTENTICACIÓN ROBUSTA ---

# 1. Intentamos obtener la API KEY de los Secretos de Streamlit (Prioridad)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]

# 2. Si no está, intentamos variables de entorno (para uso local)
else:
    api_key = os.getenv("GOOGLE_API_KEY")

# 3. Configuración condicional
if api_key:
    genai.configure(api_key=api_key)
else:
    # No configuramos todavía para evitar que la app explote al iniciarse.
    # Se mostrará un error visual en la interfaz más adelante.
    pass

class GeminiClient:
    def __init__(self):
        # Verificación en tiempo de ejecución
        if not api_key:
            st.error("⚠️ ERROR CRÍTICO: No se detectó la GOOGLE_API_KEY. Ve a Settings -> Secrets en Streamlit Cloud y configúrala.")
            # Creamos un objeto dummy para evitar error de atributo, 
            # aunque las llamadas fallarán controladamente
            self.model = None 
            return

        try:
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )
        except Exception as e:
            st.error(f"Error conectando con Gemini: {e}")

    def consultar_nucleo(self, token: str, contexto: str) -> list:
        if not self.model: return []
        
        prompt = f"""
        Actúa como filólogo experto (Protocolo P4).
        Token: "{token}"
        Contexto: "{contexto}"
        Responde SOLO JSON:
        [
            {{
                "termino": "traducción",
                "origen": "LATINA/GRIEGA/ARABE/TECNICA",
                "raiz": "raíz_detectada",
                "derivacion_existe": true,
                "es_metafora_viable": false
            }}
        ]
        """
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error IA: {e}")
            return []

    def consultar_particula(self, token: str, funcion_sintactica: str) -> list:
        if not self.model: return []

        prompt = f"""
        Actúa como experto gramatical (Protocolo P5).
        Partícula: "{token}"
        Función: "{funcion_sintactica}"
        Responde SOLO JSON:
        [
            {{
                "termino": "traducción",
                "es_etimologico": true,
                "cierra_regimen": true
            }}
        ]
        """
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error IA: {e}")
            return []

# Instancia global
ai_engine = GeminiClient()
