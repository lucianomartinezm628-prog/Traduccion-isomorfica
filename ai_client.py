# ai_client.py
import os
import json
import google.generativeai as genai
from typing import List, Dict, Any

# Configura tu API KEY aquí o en variables de entorno
# os.environ["GOOGLE_API_KEY"] = "TU_API_KEY_DE_GOOGLE_AI_STUDIO"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

class GeminiClient:
    def __init__(self):
        # Usamos flash para velocidad o pro para mayor razonamiento etimológico
        self.model = genai.GenerativeModel('gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"})

    def consultar_nucleo(self, token: str, contexto: str) -> List[Dict[str, Any]]:
        """
        Ejecuta P4 (Núcleos) usando Gemini.
        Retorna una lista de candidatos etimológicos.
        """
        prompt = f"""
        Actúa como un filólogo experto en árabe clásico, latín y griego.
        Sigue el PROTOCOLO P4 (Preferencia Etimológica).

        TOKEN A ANALIZAR: "{token}"
        CONTEXTO DE LA FRASE: "{contexto}"

        TU TAREA:
        1. Identifica la raíz del token árabe.
        2. Proporciona candidatos de traducción en español basándote en la JERARQUÍA: [LENGUA_FUENTE > LATINA > GRIEGA > ÁRABE > TÉCNICA].
        3. Prioriza la etimología sobre el uso técnico si es metaforizable.

        Responde ÚNICAMENTE con este JSON:
        [
            {{
                "termino": "traducción_propuesta",
                "origen": "LATINA" | "GRIEGA" | "ARABE" | "TECNICA",
                "raiz": "raíz_etimológica",
                "derivacion_existe": true/false (¿existe esta palabra en español?),
                "es_metafora_viable": true/false
            }},
            ... (más candidatos si hay ambigüedad)
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error consultando a Gemini para '{token}': {e}")
            return [] # Retorna lista vacía para que el sistema use fallback (P6)

    def consultar_particula(self, token: str, funcion_sintactica: str) -> List[Dict[str, Any]]:
        """
        Ejecuta P5 (Partículas) usando Gemini.
        """
        prompt = f"""
        Actúa como experto en gramática comparada árabe-español.
        TOKEN: "{token}"
        FUNCIÓN SINTÁCTICA DETECTADA: "{funcion_sintactica}"
        
        Dame candidatos de traducción (preposiciones/conectores) que cumplan:
        1. Cercanía etimológica.
        2. Validez funcional en español.

        Responde JSON:
        [
            {{
                "termino": "propuesta",
                "es_etimologico": true/false,
                "cierra_regimen": true/false
            }}
        ]
        """
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error consultando partícula '{token}': {e}")
            return []

# Instancia global
ai_engine = GeminiClient()
