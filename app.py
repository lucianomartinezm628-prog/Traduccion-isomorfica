import streamlit as st
import json
from io import StringIO

# Importamos la clase del backend (asegúrate de que el archivo del Word se llame main.py)
try:
    from main import SistemaTraduccion
except ImportError:
    st.error("⚠️ No se encontró el archivo 'main.py'. Asegúrate de que está en la misma carpeta.")
    st.stop()

st.set_page_config(page_title="Traductor Isomórfico", layout="wide")

# --- Inicializar Sistema ---
if 'sistema' not in st.session_state:
    st.session_state.sistema = SistemaTraduccion()

sys = st.session_state.sistema

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # 1. BOTÓN DE REINICIO
    if st.button("🔴 REINICIAR SISTEMA (Borrar memoria)", type="primary"):
        st.session_state.sistema = SistemaTraduccion()
        st.rerun()
    
    st.divider()

    # 2. CARGADOR DE GLOSARIO
    st.subheader("📂 Cargar Glosario")
    archivo_subido = st.file_uploader("Sube un archivo .txt o .json", type=['txt', 'json'])
    
    if archivo_subido is not None:
        if st.button("Procesar Archivo"):
            try:
                # Leer archivo
                stringio = StringIO(archivo_subido.getvalue().decode("utf-8"))
                
                # Caso 1: Archivo JSON
                if archivo_subido.name.endswith('.json'):
                    datos = json.load(stringio)
                    # Simulamos carga manual si no hay importador directo expuesto
                    count = 0
                    for k, v in datos.items():
                        cmd = f"[AÑADE {k} = {v['traduccion']}]"
                        sys.procesar_comando(cmd)
                        count += 1
                    st.success(f"✅ Se cargaron {count} términos desde JSON.")

                # Caso 2: Archivo de Texto (Lista de comandos)
                else:
                    lineas = stringio.readlines()
                    count = 0
                    errores = 0
                    barra = st.progress(0)
                    for i, linea in enumerate(lineas):
                        linea = linea.strip()
                        # Solo procesamos si parece un comando o una regla
                        if linea.startswith("["):
                            sys.procesar_comando(linea)
                            count += 1
                        elif linea: 
                            errores += 1
                        barra.progress((i + 1) / len(lineas))
                    
                    st.success(f"✅ Procesados {count} comandos.")
                    if errores > 0:
                        st.warning(f"⚠️ {errores} líneas ignoradas (no tenían formato [COMANDO]).")
                        
            except Exception as e:
                st.error(f"Error al leer archivo: {e}")

    st.divider()
    
    # Visor rápido (CORREGIDO AQUÍ)
    # Accedemos a _entradas en lugar de terminos
    st.info(f"Tokens en memoria: {len(sys.glosario._entradas)}")

# --- PANTALLA PRINCIPAL ---
st.title("🛡️ Traductor Isomórfico")

col1, col2 = st.columns([3, 1])

with col1:
    texto = st.text_area("Texto Latín/Árabe", height=150, placeholder="Escribe aquí tu texto...")

    if st.button("TRADUCIR", type="primary"):
        if texto:
            with st.spinner("Procesando..."):
                try:
                    res = sys.traducir(texto)
                    st.success("### Traducción:")
                    st.write(res)
                    
                    # Mostrar detalles técnicos en un desplegable
                    with st.expander("Ver Detalles Internos (Debug)"):
                        st.text(sys.obtener_estado())
                        st.text("--- GLOSARIO ACTUAL ---")
                        st.text(sys.obtener_glosario())
                except Exception as e:
                    st.error(f"Error durante la traducción: {e}")
        else:
            st.warning("Por favor escribe un texto para traducir.")

with col2:
    st.markdown("### Comandos Rápidos")
    cmd_manual = st.text_input("Comando manual:", placeholder="[AÑADE palabra = trad]")
    if st.button("Ejecutar"):
        if cmd_manual:
            resp = sys.procesar_comando(cmd_manual)
            st.info(f"Sistema: {resp}")
