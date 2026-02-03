import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions

# ==============================================================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==============================================================================
st.set_page_config(
    page_title="Sistema de Traducción Isomórfica (Chat)",
    page_icon="🛡️",
    layout="wide"
)

# --- TUS PROTOCOLOS EXACTOS (CONSTITUCIÓN) ---
CONSTITUCION = """
ACTÚA ESTRICTAMENTE BAJO LOS SIGUIENTES PROTOCOLOS. NO TE SALGAS DEL PERSONAJE.
ERES EL SISTEMA DE TRADUCCIÓN ISOMÓRFICA. TU ÚNICO OBJETIVO ES EJECUTAR ESTAS REGLAS:

════════════════════════════════════════════════════════════════
PROTOCOLO 0: MODO DE OPERACIÓN (Flujo e Interacción)
════════════════════════════════════════════════════════════════
PRINCIPIO FUNDAMENTAL:
  El usuario es la máxima autoridad. Ante duda → PREGUNTAR.

0.1. FLUJO MACRO
  Input → P10.A (Limpieza) → P8.A (Análisis) → [CONSULTA PRE] → P3-P7 (Traducción) → [CONSULTA DURANTE] → P10.B (Salida).

0.5. FALLO CRÍTICO
  Si detectas: Registro incompleto, Sinonimia en núcleo, o Token no registrado:
  DETENTE INMEDIATAMENTE. Pide intervención.

0.13. MODO DE SALIDA
  Por defecto opera en MODO BORRADOR (con marcas de debug si necesario).
  Si el usuario pide MODO FINAL, entrega texto limpio.

════════════════════════════════════════════════════════════════
PROTOCOLO 1.A: DEFINICIONES — Conceptos
════════════════════════════════════════════════════════════════
1.A.2. JERARQUÍA: ESTILO > IDENTIDAD > COHESIÓN.
  Si el autor es oscuro, la traducción es oscura.
  
1.A.3. REGLA ETIMOLÓGICA:
  Si etimología ≠ uso técnico pero metáfora viable → ELEGIR ETIMOLOGÍA.

1.A.4. TOKENS:
  NÚCLEOS (Sust, Verb, Adj, Adv): INVARIABLES (1:1). Sinonimia PROHIBIDA.
  PARTÍCULAS (Prep, Conj, Pron): POLIVALENTES (según función).

════════════════════════════════════════════════════════════════
PROTOCOLO 2: CONSTITUCIÓN (Reglas Inviolables)
════════════════════════════════════════════════════════════════
PROHIBIDO:
  - Crear coherencia sin permiso.
  - Reordenar tokens (Isomorfismo posicional estricto).
  - Eliminar tokens (usar {...} para nulidad).
  - Usar sinónimos en núcleos.
  - Traducir componentes de locuciones por separado.

PERMITIDO:
  - Inyecciones [...] para soporte gramatical mínimo (Whitelist P7).
  - Agramaticalidad si proviene del isomorfismo.

════════════════════════════════════════════════════════════════
PROTOCOLO 3 & 4: CORE Y NÚCLEOS
════════════════════════════════════════════════════════════════
P3: Mantener Size(Mtx_T) == Size(Mtx_S).
P4: Prioridad Etimológica: LENGUA_FUENTE > LATINA > GRIEGA > ÁRABE.

════════════════════════════════════════════════════════════════
PROTOCOLO 8: GLOSARIO
════════════════════════════════════════════════════════════════
A4. VERIFICACIÓN: Antes de traducir, verifica que cada palabra tenga definición.
B3. SINONIMIA: Si intentas usar una palabra diferente para un núcleo ya traducido antes -> ALERTA DE ERROR.

════════════════════════════════════════════════════════════════
PROTOCOLO 9: FORMACIÓN LÉXICA
════════════════════════════════════════════════════════════════
Si no hay raíz en español (NO_ROOT):
  Transliterar + Sufijo Español (ej: ma'qúl -> ma'qulado).
Si es locución (IDIOM):
  Traducir componentes etimológicamente y unir con guiones (ej: por-ojo-suyo).

════════════════════════════════════════════════════════════════
PROTOCOLO 11: COMANDOS
════════════════════════════════════════════════════════════════
Reconoce y ejecuta comandos como: [GLOSARIO], [ESTADO], [PAUSA], [FORZAR], [ACTUALIZA x=y].

--- INSTRUCCIÓN FINAL PARA LA IA ---
1. Analiza el input del usuario.
2. Si es un COMANDO, ejecútalo y muestra el resultado.
3. Si es TEXTO A TRADUCIR, aplica el flujo P10->P8->P3...
4. Si encuentras dudas (C1-C6), DETENTE y pregunta usando el FORMATO DE CONSULTA (0.6).
5. NO traduzcas de golpe si hay palabras nuevas; primero presenta el GLOSARIO PRELIMINAR (P8.A) para aprobación.
"""

# ==============================================================================
# 2. FUNCIONES AUXILIARES (MANEJO DE ERRORES)
# ==============================================================================

def generar_respuesta_con_retry(model, prompt, chat_history):
    """
    Intenta generar respuesta manejando el error 429 (Cuota excedida)
    con espera exponencial (Backoff).
    """
    max_retries = 3
    base_wait = 10 # Segundos de espera inicial

    for attempt in range(max_retries):
        try:
            # Iniciamos el chat con el historial
            chat = model.start_chat(history=chat_history)
            
            # Devolvemos el generador de respuesta (stream)
            return chat.send_message(prompt, stream=True)

        except exceptions.ResourceExhausted:
            # Error 429: Cuota excedida
            wait_time = base_wait * (attempt + 1)
            msg = f"⏳ Tráfico alto (Error 429). Reintentando en {wait_time}s... (Intento {attempt+1}/{max_retries})"
            st.toast(msg, icon="⚠️")
            time.sleep(wait_time)
            continue
        
        except exceptions.NotFound:
             st.error("❌ Error 404: El modelo seleccionado no está disponible en tu región o fue retirado. Cambia el modelo en la barra lateral.")
             return None
             
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            return None
    
    st.error("⛔ Se agotaron los intentos. El servicio está saturado. Intenta con un modelo 'Lite' o espera un minuto.")
    return None

# ==============================================================================
# 3. INTERFAZ Y LÓGICA DE CHAT
# ==============================================================================

def main():
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Configuración P0")
        api_key = st.text_input("Gemini API Key", type="password")
        
        # LISTA ESTRICTA DE TUS MODELOS COMPATIBLES
        # Se pone primero el más seguro (Latest)
        modelos_disponibles = [
            "gemini-flash-latest",          # Alias seguro (suele ser 1.5 o 2.0 estable)
            "gemini-flash-lite-latest",     # Alias ligero seguro
            "gemini-2.0-flash-lite",        # Rápido, propenso a 429 en free tier
            "gemini-2.0-flash",             # Potente, propenso a 429
            "gemini-2.5-flash-lite",        # Preview
            "gemini-2.5-flash",             # Preview
            "gemini-pro-latest",
            "gemma-3-27b-it"                # Modelo abierto servido por API
        ]
        
        modelo = st.selectbox(
            "Modelo Activo", 
            modelos_disponibles, 
            index=0,
            help="Si recibes errores de 'Quota exceeded', prueba con 'flash-latest' o 'lite'."
        )
        
        st.divider()
        st.info("Sistema cargado con Protocolos P0-P11.")
        
        if st.button("🗑️ Reiniciar Sesión"):
            st.session_state.messages = []
            st.rerun()

    st.title("🛡️ Sistema de Traducción Isomórfica")
    st.caption(f"Operando con: **{modelo}** | Temperatura: 0.0 (Estricta)")

    # --- Inicializar Historial ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Sistema P0 Iniciado. Protocolos cargados. Esperando Input o Comandos (ej: [GLOSARIO], [ESTADO])."}
        ]

    # --- Mostrar Historial ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- Capturar Input del Usuario ---
    if prompt := st.chat_input("Escribe texto para traducir o comando..."):
        
        if not api_key:
            st.error("⚠️ Por favor ingresa tu API Key en la barra lateral.")
            return

        # 1. Guardar mensaje usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Llamar a Gemini
        genai.configure(api_key=api_key)
        
        # Configuración ESTRICTA
        generation_config = {
            "temperature": 0.0,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 8192,
        }

        try:
            model_instance = genai.GenerativeModel(
                model_name=modelo,
                system_instruction=CONSTITUCION,
                generation_config=generation_config
            )

            # Preparar historial para la API
            chat_history_api = []
            for m in st.session_state.messages[:-1]: # Excluir el último prompt que ya enviamos
                role = "user" if m["role"] == "user" else "model"
                chat_history_api.append({"role": role, "parts": [m["content"]]})

            # Generar respuesta (Con reintentos)
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                # Llamada segura con retry
                response_stream = generar_respuesta_con_retry(model_instance, prompt, chat_history_api)
                
                if response_stream:
                    try:
                        for chunk in response_stream:
                            if chunk.text:
                                full_response += chunk.text
                                response_placeholder.markdown(full_response + "▌")
                        
                        response_placeholder.markdown(full_response)
                        
                        # 3. Guardar respuesta asistente solo si hubo éxito
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    except Exception as stream_err:
                        st.error(f"Error procesando respuesta: {stream_err}")

        except Exception as e:
            st.error(f"Error de Configuración: {str(e)}")

if __name__ == "__main__":
    main()
