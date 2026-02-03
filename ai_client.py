import streamlit as st
import google.generativeai as genai
import json
import os
import time
import random
from google.api_core import exceptions

# ──────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN DE MODELOS DISPONIBLES
# ──────────────────────────────────────────────────────────────
MODELOS_DISPONIBLES = {
    "flash_2.0": "gemini-2.0-flash",       
    "flash_lite": "gemini-flash-lite-latest", 
    "pro_latest": "gemini-pro-latest",     
}

# Selección del modelo (puedes cambiar la clave según prefieras)
MODELO_ACTUAL = MODELOS_DISPONIBLES["flash_lite"]

# ──────────────────────────────────────────────────────────────
# 2. AUTENTICACIÓN SEGURA (Streamlit Secrets / Env)
# ──────────────────────────────────────────────────────────────
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

# ──────────────────────────────────────────────────────────────
# 3. CLIENTE GEMINI CON GESTIÓN DE TRÁFICO
# ──────────────────────────────────────────────────────────────

class GeminiClient:
    def __init__(self):
        if not api_key:
            st.error("⚠️ No se detectó la GOOGLE_API_KEY. Configúrala en los Secrets de Streamlit.")
            self.model = None 
            return

        try:
            self.model = genai.GenerativeModel(
                MODELO_ACTUAL, 
                generation_config={"response_mime_type": "application/json"}
            )
            print(f"[*] Sistema conectado al modelo: {MODELO_ACTUAL}")
        except Exception as e:
            st.error(f"Error al inicializar el modelo {MODELO_ACTUAL}: {e}")
            self.model = None

    def _generar_con_retry(self, prompt: str, intentos_max: int = 5) -> list:
        """
        Maneja el error 429 (Cuota excedida) aplicando una espera
        exponencial antes de reintentar la consulta.
        """
        if not self.model: 
            return []

        for i in range(intentos_max):
            try:
                response = self.model.generate_content(prompt)
                return json.loads(response.text)
            
            except exceptions.ResourceExhausted:
                # Error 429: Demasiado tráfico. 
                # Espera base de 5s + aumento exponencial (2^i) + azar
                tiempo_espera = 5 + (2 ** i) + random.uniform(0, 2)
                
                msg = f"🚦 Alto tráfico en {MODELO_ACTUAL}. Esperando {int(tiempo_espera)}s..."
                print(msg)
                try:
                    st.toast(msg, icon="⏳")
                except:
                    pass
                
                time.sleep(tiempo_espera)
                continue # Reintentar
                
            except Exception as e:
                print(f"❌ Error en consulta IA: {e}")
                return []
        
        print("❌ Se agotaron los reintentos para este token.")
        return []

    def consultar_nucleo(self, token: str, contexto: str) -> list:
        """Protocolo P4: Análisis etimológico de núcleos léxicos"""
        prompt = f"""
        Actúa como filólogo experto siguiendo el protocolo P4.
        Analiza el token: '{token}'
        Contexto: '{contexto}'
        
        Responde exclusivamente en formato JSON con una LISTA de objetos: 
        [{{
            "termino": "traducción_española",
            "origen": "LATINA" | "GRIEGA" | "ARABE" | "TECNICA",
            "raiz": "raiz_etimológica",
            "derivacion_existe": bool,
            "es_metafora_viable": bool
        }}]
        """
        return self._generar_con_retry(prompt)

    def consultar_particula(self, token: str, funcion_sintactica: str) -> list:
        """Protocolo P5: Análisis funcional de partículas"""
        prompt = f"""
        Actúa como experto gramatical siguiendo el protocolo P5.
        Analiza la partícula: '{token}'
        Función: '{funcion_sintactica}'
        
        Responde exclusivamente en formato JSON con una LISTA de objetos: 
        [{{
            "termino": "traducción",
            "es_etimologico": bool,
            "cierra_regimen": bool
        }}]
        """
        return self._generar_con_retry(prompt)

# Instancia global para el orquestador
ai_engine = GeminiClient()
