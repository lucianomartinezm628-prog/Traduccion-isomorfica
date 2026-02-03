import streamlit as st
import json
from io import StringIO

# Importamos la clase del backend (asegúrate de que el archivo del Word se llame main.py)
try:
    from main import SistemaTraduccion
except ImportError:
    st.error("⚠️ No se encontró el archivo 'main.py'.")
    st.stop()

st.set_page_config(page_title="Traductor Isomórfico", layout="wide")

# --- Inicializar Sistema ---
if 'sistema' not in st.session_state:
    st.session_state.sistema = SistemaTraduccion()

sys = st.session_state.sistema

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # 1. BOTÓN DE REINICIO (Úsalo ahora para borrar los errores "idad")
    if st.button("🔴 REINICIAR SISTEMA (Borrar memoria)", type="primary"):
        st.session_state.sistema = SistemaTraduccion()
        st.rerun()
    
    st.divider()

    # 2. CARGADOR DE GLOSARIO (¡NUEVO!)
    st.subheader("📂 Cargar Glosario")
    archivo_subido = st.file_uploader("Sube un archivo .txt o .json", type=['txt', 'json'])
    
    if archivo_subido is not None:
        if st.button("Procesar Archivo"):
            try:
                # Leer archivo
                stringio = StringIO(archivo_subido.getvalue().decode("utf-8"))
                
                # Caso 1: Archivo JSON (Exportado previamente)
                if archivo_subido.name.endswith('.json'):
                    datos = json.load(stringio)
                    # Aquí habría que conectar con una función de importación en tu backend
                    # Si no existe, simulamos carga manual:
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
                        if linea.startswith("[AÑADE") or linea.startswith("[REGLA"):
                            sys.procesar_comando(linea)
                            count += 1
                        elif linea: # Si hay texto pero no es comando
                            errores += 1
                        barra.progress((i + 1) / len(lineas))
                    
                    st.success(f"✅ Procesados {count} comandos.")
                    if errores > 0:
                        st.warning(f"⚠️ {errores} líneas ignoradas (no eran comandos).")
                        
            except Exception as e:
                st.error(f"Error al leer archivo: {e}")

    st.divider()
    
    # Visor rápido
    st.info(f"Tokens en memoria: {len(sys.glosario.terminos)}")

# --- PANTALLA PRINCIPAL ---
st.title("🛡️ Traductor Isomórfico")

texto = st.text_area("Texto Latín/Árabe", height=150)

if st.button("TRADUCIR", type="primary"):
    if texto:
        res = sys.traducir(texto)
        st.success(res)
        
        with st.expander("Ver Detalles Internos"):
            st.text(sys.obtener_estado())
            st.text("--- GLOSARIO ACTUAL ---")
            st.text(sys.obtener_glosario())
