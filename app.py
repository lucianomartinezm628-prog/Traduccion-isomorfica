import streamlit as st
import pandas as pd
# Asumimos que tu código principal del Word se llama 'main.py'
# y tiene la clase SistemaTraduccion.
# Si pusiste todo en un solo archivo, cambia 'main' por el nombre de ese archivo.
try:
    from main import SistemaTraduccion, ModoSalida
except ImportError:
    st.error("⚠️ No se encontró el archivo 'main.py'. Asegúrate de haber guardado el código del Word en la misma carpeta.")
    st.stop()

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Panel Isomórfico v2.0",
    page_icon="🛡️",
    layout="wide"
)

# --- Inicialización del Estado (Memoria) ---
# Esto evita que el glosario se borre cada vez que tocas un botón
if 'sistema' not in st.session_state:
    st.session_state.sistema = SistemaTraduccion()

# Acceso rápido al sistema
sys = st.session_state.sistema

# --- BARRA LATERAL (Control y Comandos) ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=50)
    st.title("Configuración")
    
    st.markdown("### 🛠️ Comandos Manuales")
    st.info("Aquí puedes cargar el glosario manualmente.")
    
    # Input para comandos (P11)
    comando = st.text_input("Escribe un comando:", placeholder="[AÑADE token = trad]")
    if st.button("Ejecutar Comando"):
        if comando:
            resultado = sys.procesar_comando(comando)
            st.success(f"Sistema: {resultado}")
        else:
            st.warning("Escribe un comando primero.")

    st.markdown("---")
    
    # Visor de Estado del Proceso
    st.markdown("### 📊 Estado del Sistema")
    estado_txt = sys.obtener_estado()
    st.text(estado_txt)

    # Botones de control rápido
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reiniciar"):
            sys.procesar_comando("[REINICIAR]")
            st.rerun()
    with col2:
        if st.button("Ver Glosario"):
            st.session_state.mostrar_glosario = True

# --- PANEL PRINCIPAL ---
st.title("🛡️ Panel de Control Isomórfico v2.0")

# Área de Texto Fuente
st.subheader("Texto Fuente (Árabe/Latín)")
texto_input = st.text_area(
    "Ingresa el texto aquí:",
    height=150,
    placeholder="[2] Dicemus ergo quod dictiones..."
)

col_izq, col_der = st.columns([1, 4])
with col_izq:
    boton_traducir = st.button("Traducir", type="primary", use_container_width=True)

# Lógica de Traducción
if boton_traducir and texto_input:
    with st.spinner('Procesando isomorfismo...'):
        try:
            # 1. Ejecutar traducción
            traduccion_final = sys.traducir(texto_input)
            
            # 2. Mostrar Resultados en Pestañas
            tab1, tab2, tab3 = st.tabs(["📝 Resultado Final", "🔍 Matriz Fuente (Mtx_S)", "🎯 Matriz Destino (Mtx_T)"])
            
            with tab1:
                st.markdown("### Traducción Renderizada")
                st.success(traduccion_final)
                
                # Opción de descargar
                st.download_button(
                    label="Descargar Traducción",
                    data=traduccion_final,
                    file_name="traduccion_isomorfica.txt",
                    mime="text/plain"
                )

            with tab2:
                st.markdown("#### Desglose de Tokens Fuente")
                # Simulamos la visualización de la matriz fuente
                # El backend tiene sys._oraciones_fuente, podemos usarlo
                st.code(sys._oraciones_fuente)

            with tab3:
                st.markdown("#### Estructura Isomórfica de Salida")
                # Usamos el modo borrador para ver la estructura interna
                modo_actual = sys.config.modo_salida
                sys.procesar_comando("[MODO BORRADOR]")
                borrador = sys.obtener_traduccion() # Obtiene la versión debug
                st.text(borrador)
                # Restauramos modo
                sys.config.modo_salida = modo_actual

        except Exception as e:
            st.error(f"Error crítico en el núcleo: {e}")

# --- VISOR DE GLOSARIO (Expander) ---
st.markdown("---")
with st.expander("📚 Ver Glosario Activo", expanded=False):
    glosario_txt = sys.obtener_glosario()
    if glosario_txt:
        st.text(glosario_txt)
    else:
        st.info("El glosario está vacío. Traduce algo o usa comandos para añadir términos.")

