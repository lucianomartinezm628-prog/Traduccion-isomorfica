import streamlit as st
import google.generativeai as genai
import json
import os
import time
import random
from google.api_core import exceptions

# --- LISTA DE OPCIONES DE MODELOS ---
MODELOS_DISPONIBLES = {
    "flash_2.0": "gemini-2.0-flash",       
    "flash_lite": "gemini-flash-lite-latest", # <--- EL ELEGIDO
    "pro_latest": "gemini-pro-latest",     
}

# Selección del modelo actual
MODELO_ACTUAL = MODELOS_DISPONIBLES["flash_lite"]

# --- AUTENTICACIÓN ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

class GeminiClient:
    def __init__(self):
        if not api_key:
            st.error("⚠️ No se detectó la API KEY.")
            self.model = None 
            return

        try:
            self.model = genai.GenerativeModel(
                MODELO_ACTUAL, 
                generation_config={"response_mime_type": "application/json"}
            )
            print(f"[*] Sistema conectado al modelo: {MODELO_ACTUAL}")
        except Exception as e:
            st.error(f"Error al inicializar: {e}")
            self.model = None

    def _generar_con_retry(self, prompt: str, intentos_max: int = 5) -> list:
        """
        Maneja automáticamente el error 429 (Cuota excedida)
        esperando unos segundos antes de reintentar.
        """
        if not self.model: return []

        for i in range(intentos_max):
            try:
                response = self.model.generate_content(prompt)
                return json.loads(response.text)
            
            except exceptions.ResourceExhausted:
                # ERROR 429: Cuota excedida.
                # Espera exponencial: 2s, 4s, 8s... + un poco de azar para no colisionar
                tiempo_espera = (2 ** (i + 1)) + random.uniform(0, 1)
                
                msg = f"🚦 Tráfico alto en {MODELO_ACTUAL}. Esperando {int(tiempo_espera)}s..."
                print(msg)
                # Mostramos un aviso flotante en la app si es posible
                try:
                    st.toast(msg)
                except:
                    pass
                
                time.sleep(tiempo_espera)
                continue
                
            except Exception as e:
                print(f"❌ Error irrecuperable en consulta IA: {e}")
                # Si falla, devolvemos lista vacía para que el sistema use P6 (neologismos)
                return []
        
        print("❌ Se agotaron los reintentos.")
        return []

    def consultar_nucleo(self, token: str, contexto: str) -> list:
        """Protocolo P4: Análisis etimológico"""
        prompt = f"""
        Actúa como filólogo experto (P4).
        Analiza el token: '{token}'
        Contexto: '{contexto}'
        Responde JSON: [{{
            "termino": "traducción",
            "origen": "LATINA/GRIEGA/ARABE/TECNICA",
            "raiz": "raíz",
            "derivacion_existe": true,
            "es_metafora_viable": false
        }}]
        """
        return self._generar_con_retry(prompt)

    def consultar_particula(self, token: str, funcion_sintactica: str) -> list:
        """Protocolo P5: Análisis funcional"""
        prompt = f"""
        Actúa como experto gramatical (P5).
        Partícula: '{token}'
        Función: '{funcion_sintactica}'
        Responde JSON: [{{
            "termino": "traducción",
            "es_etimologico": true,
            "cierra_regimen": true
        }}]
        """
        return self._generar_con_retry(prompt)

# Instancia global
ai_engine = GeminiClient()
