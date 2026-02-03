import streamlit as st

st.title("🛡️ Panel de Control Isomórfico v2.0")

# Área de entrada
texto_fuente = st.text_area("Texto Fuente (Árabe/Latín)")

# [span_21](start_span)[span_22](start_span)Sidebar para Protocolos[span_21](end_span)[span_22](end_span)
with st.sidebar:
    st.header("Configuración P11")
    modo = st.radio("Modo de Salida", ["BORRADOR", "FINAL"])
    trans = st.selectbox("Transliteración", ["Desactivado", "Selectivo", "Completo"])
    if st.button("Cargar Glosario JSON"):
        # [span_23](start_span)Llamada a [IMPORTAR GLOSARIO][span_23](end_span)
        pass

# [span_24](start_span)[span_25](start_span)Visualización de la Matriz (El corazón del sistema)[span_24](end_span)[span_25](end_span)
if st.button("Traducir"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Mtx_S (Fuente)")
        # Muestra los tokens originales en sus slots
    with col2:
        st.subheader("Mtx_T (Destino)")
        # Muestra la traducción con sus operadores [], {} y -
