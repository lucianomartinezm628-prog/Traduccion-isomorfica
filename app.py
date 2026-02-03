import streamlit as st
from main import SistemaTraduccion
from glossary import Glosario

# Configuración de la página
st.set_page_config(page_title="Traductor Isomórfico", layout="wide")

st.title("🤖 Sistema de Traducción Isomórfica (Neuro-Simbólico)")
st.markdown("""
Esta herramienta combina **Protocolos Deterministas** (Python) con **Inteligencia Generativa** (Gemini) 
para garantizar consistencia etimológica y estructural.
""")

# 1. INICIALIZACIÓN DEL SISTEMA (Solo una vez)
if 'sistema' not in st.session_state:
    try:
        st.session_state.sistema = SistemaTraduccion()
        st.success("Sistema inicializado correctamente.")
    except Exception as e:
        st.error(f"Error al iniciar el sistema: {e}")

# Sidebar: Estado y Controles
with st.sidebar:
    st.header("Estado del Sistema")
    if 'sistema' in st.session_state:
        # Mostrar estadísticas del glosario
        stats = st.session_state.sistema.glosario.obtener_estadisticas()
        st.metric("Entradas en Glosario", stats['total'])
        st.metric("Locuciones", stats['locuciones'])
        
        if st.button("Ver Glosario Completo"):
            st.text(st.session_state.sistema.obtener_glosario())
            
        if st.button("Reiniciar Sistema"):
            st.session_state.sistema = SistemaTraduccion()
            st.rerun()

# 2. INTERFAZ DE TRADUCCIÓN
col1, col2 = st.columns(2)

with col1:
    st.subheader("Texto Fuente (Árabe/Técnico)")
    texto_input = st.text_area("Pega tu texto aquí...", height=400)
    
    traducir_btn = st.button("Traducir", type="primary")

with col2:
    st.subheader("Traducción Isomórfica")
    output_container = st.empty()

# 3. LÓGICA DE EJECUCIÓN
if traducir_btn and texto_input:
    if not st.secrets.get("GOOGLE_API_KEY"):
        st.error("⚠️ Falta la API KEY. Configúrala en los Secrets de Streamlit.")
    else:
        with st.spinner('Procesando: Limpieza -> Tokenización -> Consultas IA -> Renderizado...'):
            try:
                # Ejecutar traducción usando tu sistema existente
                traduccion = st.session_state.sistema.traducir(texto_input)
                
                # Mostrar resultado
                output_container.text_area("Resultado", value=traduccion, height=400)
                
                # Botón de descarga (Streamlit no guarda en disco local del servidor)
                st.download_button(
                    label="Descargar Traducción (.txt)",
                    data=traduccion,
                    file_name="traduccion_isomorfica.txt",
                    mime="text/plain"
                )
                
                # Botón para descargar el Glosario actualizado (JSON)
                glosario_json = st.session_state.sistema.exportar_glosario("json")
                st.download_button(
                    label="Descargar Glosario (.json)",
                    data=glosario_json,
                    file_name="glosario_actualizado.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"Error durante la traducción: {str(e)}")
