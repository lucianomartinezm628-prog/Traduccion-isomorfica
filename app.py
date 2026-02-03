import streamlit as st
from main import SistemaTraduccion
from constants import ModoSalida, ModoTransliteracion

# Inicialización del Sistema (Orquestación Bloque 13)
if 'sistema' not in st.session_state:
    st.session_state.sistema = SistemaTraduccion()

st.set_page_config(page_title="Sistema de Traducción Isomórfica v2.0", layout="wide")

st.title("🛡️ Sistema de Traducción Isomórfica")
st.markdown("---")

# Sidebar: Configuración (P0 y P11)
with st.sidebar:
    st.header("Configuración del Sistema")
    modo_salida = st.selectbox("Modo de Salida", ["FINAL", "BORRADOR"])
    modo_trans = st.selectbox("Transliteración", ["DESACTIVADO", "SELECTIVO", "COMPLETO"])
    
    # Aplicar configuración vía Comandos (P11)
    st.session_state.sistema.procesar_comando(f"[MODO {modo_salida}]")
    st.session_state.sistema.procesar_comando(f"[MODO TRANSLITERACION {modo_trans}]")
    
    st.divider()
    st.subheader("Gestión de Glosario (P8)")
    archivo_glosario = st.file_uploader("Importar Glosario JSON", type=['json'])
    if archivo_glosario:
        datos = archivo_glosario.read().decode("utf-8")
        st.session_state.sistema.importar_glosario(datos)
        st.success("Glosario Cargado")

# Cuerpo Principal: Traducción
col1, col2 = st.columns(2)

with col1:
    st.subheader("Texto Fuente (Input)")
    texto_input = st.text_area("Ingrese texto árabe/transliterado:", height=300)
    if st.button("Ejecutar Traducción (P3-P7)"):
        with st.spinner("Procesando Isomorfismo..."):
            traduccion = st.session_state.sistema.traducir(texto_input)
            st.session_state.output = traduccion

with col2:
    st.subheader("Texto Traducido (Output)")
    output = st.session_state.get('output', "")
    st.text_area("Resultado Isomórfico:", value=output, height=300, disabled=True)

# Panel de Auditoría e Historial (P11)
st.divider()
tab1, tab2, tab3 = st.tabs(["Glosario Activo", "Historial de Decisiones", "Estado del Proceso"])

with tab1:
    st.text(st.session_state.sistema.obtener_glosario())

with tab2:
    # Muestra el Historial de Decisiones (P0.12)
    st.text(st.session_state.sistema.proc_comandos.gestor_consultas.formatear_historial())

with tab3:
    # Estadísticas del Proceso (Bloque 2)
    st.text(st.session_state.sistema.obtener_estado())
