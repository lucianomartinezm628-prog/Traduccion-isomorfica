import streamlit as st
import google.generativeai as genai
import json
import pandas as pd

# ==============================================================================
# CONFIGURACIÓN Y ESTADO (PROTOCOLO 0 & 2)
# ==============================================================================

st.set_page_config(page_title="Sistema Isomórfico v2.0", page_icon="🏛️", layout="wide")

# Inicialización de Estado (Memoria Persistente)
if "glossary" not in st.session_state:
    st.session_state.glossary = {} # P8: Glosario acumulativo
if "stage" not in st.session_state:
    st.session_state.stage = "INPUT" # Etapas: INPUT -> ANALYSIS -> DECISION -> TRANSLATION
if "current_text" not in st.session_state:
    st.session_state.current_text = ""
if "pending_decisions" not in st.session_state:
    st.session_state.pending_decisions = []
if "translation_result" not in st.session_state:
    st.session_state.translation_result = ""

# ==============================================================================
# INTERFAZ LATERAL (SIDEBAR - P11 COMANDOS)
# ==============================================================================

with st.sidebar:
    st.title("⚙️ Sala de Máquinas")
    
    # Configuración de API (Crucial para que funcione)
    api_key = st.text_input("Gemini API Key", type="password", help="Pega tu clave de Google AI Studio aquí")
    
    st.divider()
    
    # Visualizador de Glosario (P11 [GLOSARIO])
    st.subheader(f"📚 Glosario Activo ({len(st.session_state.glossary)})")
    if st.session_state.glossary:
        df_glossary = pd.DataFrame(list(st.session_state.glossary.items()), columns=["Token (Src)", "Traducción (Tgt)"])
        st.dataframe(df_glossary, use_container_width=True)
    else:
        st.info("Glosario vacío. Inicia el proceso.")

    # Control de Flujo (P11.C)
    if st.button("🔄 REINICIAR PROCESO", type="primary"):
        st.session_state.stage = "INPUT"
        st.session_state.current_text = ""
        st.session_state.pending_decisions = []
        st.session_state.translation_result = ""
        st.rerun()

    if st.button("🗑️ BORRAR GLOSARIO COMPLETO"):
        st.session_state.glossary = {}
        st.rerun()

# ==============================================================================
# LÓGICA DEL SISTEMA (BACKEND)
# ==============================================================================

def configure_genai():
    if not api_key:
        st.error("⚠️ Por favor ingresa tu API Key en la barra lateral para continuar.")
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash') # Modelo rápido y eficiente

# --- Prompt del Sistema (La "Constitución" P2 inyectada en la IA) ---
SYSTEM_PROMPT = """
Actúas como el motor semántico del 'Sistema de Traducción Isomórfica v2.0'.
Tus Protocolos son INVIOLABLES:
1. P2: Literalidad máxima. Isomorfismo posicional. No parafrasear.
2. P4: Núcleos léxicos invariables (1 token fuente = 1 traducción siempre).
3. P8: Respetar ESTRICTAMENTE el glosario proporcionado.
4. P9: Aplicar transliteración o neologismos si no hay equivalente exacto.
"""

def analyze_lexicon(text, model):
    """
    Implementa P8.A: Detección de nuevos términos y locuciones.
    Devuelve un JSON con los términos que NO están en el glosario actual.
    """
    existing_keys = list(st.session_state.glossary.keys())
    
    prompt = f"""
    {SYSTEM_PROMPT}
    TAREA (P8.A): Analiza el siguiente texto árabe.
    Identifica:
    1. Locuciones idiomáticas (P9.D).
    2. Términos técnicos o ambiguos (P6) que requieran decisión del usuario.
    
    IGNORA los términos que ya están en esta lista de glosario existente: {existing_keys}
    
    Devuelve un JSON puro (sin markdown) con esta estructura para los NUEVOS términos/dudas:
    [
        {{
            "token_src": "palabra_arabe",
            "context": "breve explicación",
            "options": ["Opción A (Etimológica)", "Opción B (Técnica)", "Opción C (Transliterada)"],
            "recommendation": "Opción A"
        }}
    ]
    
    TEXTO:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        # Limpieza básica de JSON por si el modelo pone ```json ... ```
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        st.error(f"Error en análisis P8.A: {e}")
        return []

def execute_translation(text, model):
    """
    Implementa P3-P7: Traducción final aplicando el glosario sellado.
    """
    glossary_str = json.dumps(st.session_state.glossary, ensure_ascii=False)
    
    prompt = f"""
    {SYSTEM_PROMPT}
    TAREA (P3-P7): Traduce el texto árabe al español.
    
    REGLA DE ORO (P8): Debes usar OBLIGATORIAMENTE las siguientes traducciones del glosario.
    Si un token está en el glosario, su traducción es INMUTABLE.
    
    GLOSARIO ACTIVO:
    {glossary_str}
    
    INSTRUCCIONES DE FORMATO (P10.B):
    - Mantén los corchetes de párrafo [1], [2]...
    - Usa guiones para locuciones (ej: por-ojo-su).
    - Marca inyecciones gramaticales con [corchetes].
    
    TEXTO A TRADUCIR:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

# ==============================================================================
# INTERFAZ PRINCIPAL (MAIN STAGE)
# ==============================================================================

st.title("🏛️ Sistema de Traducción Isomórfica")
st.markdown("**Versión Full 2.0** | Protocolos P0-P11 Activos")

model = configure_genai()

# --- FASE 1: INPUT (P10.A) ---
if st.session_state.stage == "INPUT":
    st.info("Paso 1: Ingreso de Texto Fuente")
    text_input = st.text_area("Texto Árabe:", height=200, value=st.session_state.current_text)
    
    if st.button("Iniciar Análisis (P8.A) ➡️"):
        if text_input and model:
            st.session_state.current_text = text_input
            with st.spinner("Ejecutando P8.A: Análisis léxico y detección de dudas..."):
                # Llamada a la IA para buscar dudas
                new_terms = analyze_lexicon(text_input, model)
                
                if new_terms:
                    st.session_state.pending_decisions = new_terms
                    st.session_state.stage = "DECISION"
                else:
                    # Si no hay dudas, pasamos directo a traducir
                    st.session_state.stage = "TRANSLATION"
            st.rerun()

# --- FASE 2: DECISIÓN (P0 / CONSULTAS) ---
elif st.session_state.stage == "DECISION":
    st.warning(f"⚠️ CONSULTAS PENDIENTES: {len(st.session_state.pending_decisions)} decisiones requeridas.")
    st.write("El sistema ha detectado términos nuevos o ambiguos. Tú decides (P0).")
    
    # Formulario para resolver dudas
    with st.form("decision_form"):
        decisions_made = {}
        
        for idx, item in enumerate(st.session_state.pending_decisions):
            st.markdown(f"### {idx+1}. Token: **{item['token_src']}**")
            st.caption(f"Contexto: {item['context']}")
            
            # Crear opciones para el Radio Button
            options = item['options']
            # Añadimos una opción custom
            options.append("Otra (Manual)")
            
            choice = st.radio(
                f"Selecciona traducción para '{item['token_src']}':",
                options,
                key=f"radio_{idx}",
                index=0 # Por defecto la recomendación (A)
            )
            
            final_val = choice
            if choice == "Otra (Manual)":
                final_val = st.text_input(f"Escribe traducción manual para {item['token_src']}", key=f"manual_{idx}")
            
            decisions_made[item['token_src']] = final_val.split(" (")[0] # Limpiamos "Opción (Explicación)" a solo "Opción"
            st.divider()
        
        submitted = st.form_submit_button("Confirmar Decisiones y Sellar Glosario ➡️")
        
        if submitted:
            # Actualizar Glosario (P8.B)
            st.session_state.glossary.update(decisions_made)
            st.success("Glosario actualizado.")
            st.session_state.stage = "TRANSLATION"
            st.rerun()

# --- FASE 3: TRADUCCIÓN Y OUTPUT (P3-P7 / P10.B) ---
elif st.session_state.stage == "TRANSLATION":
    if not st.session_state.translation_result:
        with st.spinner("Ejecutando P3 (Core) + P7 (Reparación)..."):
            st.session_state.translation_result = execute_translation(st.session_state.current_text, model)
    
    st.success("✅ [CORE-OK] Traducción Completada")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Fuente")
        st.text_area("Árabe", st.session_state.current_text, height=400, disabled=True)
    with col2:
        st.subheader("Destino (Isomórfico)")
        st.text_area("Español", st.session_state.translation_result, height=400)
    
    st.markdown("---")
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("⬅️ Traducir otro fragmento"):
            st.session_state.stage = "INPUT"
            st.session_state.current_text = ""
            st.session_state.translation_result = ""
            st.session_state.pending_decisions = []
            st.rerun()
    with col_btn2:
        st.info("Nota: El glosario se mantiene activo para el siguiente fragmento para asegurar consistencia.")

