# ══════════════════════════════════════════════════════════════
# main.py — ORQUESTACIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

from constants import (
    TokenStatus, TokenCategoria, CategoriaGramatical,
    ModoSalida, ModoTransliteracion, ConsultaCodigo
)
from config import obtener_config, ConfiguracionSistema
from models import (
    SlotN, SlotP, MatrizFuente, MatrizTarget,
    MorfologiaFuente, EstadoProceso
)
from glossary import Glosario, RegistroIncompletoError, SinonimiaError
from core import Core, CoreResult
from nucleos import ProcesadorNucleos, crear_slot_n
from particulas import ProcesadorParticulas, crear_slot_p
from casos_dificiles import ProcesadorCasosDificiles
from reparacion import ReparadorSintactico
from formacion import ControladorFormacionLexica
from renderizado import ControladorRenderizado
from utils import Logger
from consultas import GestorConsultas, obtener_gestor_consultas
from comandos import ProcesadorComandos, obtener_procesador_comandos


# ──────────────────────────────────────────────────────────────
# CLASE PRINCIPAL: SISTEMA DE TRADUCCIÓN
# ──────────────────────────────────────────────────────────────

class SistemaTraduccion:
    """
    Sistema de Traducción Isomórfica — Orquestador Principal
    
    Integra todos los protocolos:
      P0:  Modo de Operación
      P1:  Definiciones
      P2:  Constitución
      P3:  Core
      P4:  Núcleos
      P5:  Partículas
      P6:  Casos Difíciles
      P7:  Reparación
      P8:  Glosario
      P9:  Formación
      P10: Renderizado
      P11: Comandos
    """
    
    def __init__(self):
        # Configuración
        self.config = obtener_config()
        
        # Componentes principales
        self.glosario = Glosario()
        self.core = Core(self.glosario)
        
        # Procesadores
        self.proc_nucleos = ProcesadorNucleos()
        self.proc_particulas = ProcesadorParticulas()
        self.proc_casos_dificiles = ProcesadorCasosDificiles()
        self.reparador = ReparadorSintactico()
        self.formacion = ControladorFormacionLexica()
        self.renderizado = ControladorRenderizado()
        
        # Sistema de consultas y comandos
        self.gestor_consultas = obtener_gestor_consultas()
        self.proc_comandos = obtener_procesador_comandos()
        self.proc_comandos.set_glosario(self.glosario)
        
        # Conectar procesadores
        self.core.set_procesador_nucleos(self.proc_nucleos)
        self.core.set_procesador_particulas(self.proc_particulas)
        self.core.set_reparador(self.reparador)
        self.proc_nucleos.set_procesador_casos_dificiles(self.proc_casos_dificiles)
        
        # Estado
        self.estado = EstadoProceso()
        self.proc_comandos.estado = self.estado
        
        # Logger
        self.logger = Logger("SistemaTraduccion")
        
        # Texto y resultados
        self._texto_fuente: str = ""
        self._texto_traducido: str = ""
        self._oraciones_fuente: List[str] = []
        self._oraciones_traducidas: List[str] = []
        
        # Callbacks de control
        self._configurar_callbacks()
    
    def _configurar_callbacks(self) -> None:
        """Configurar callbacks de comandos"""
        self.proc_comandos.set_callback("PAUSA", self._on_pausa)
        self.proc_comandos.set_callback("CONTINUAR", self._on_continuar)
        self.proc_comandos.set_callback("FORZAR", self._on_forzar)
        self.proc_comandos.set_callback("REINICIAR", self._on_reiniciar)
    
    # ══════════════════════════════════════════════════════════
    # FLUJO PRINCIPAL
    # ══════════════════════════════════════════════════════════
    
    def traducir(self, texto_fuente: str) -> str:
        """
        Traducir texto completo
        
        Flujo macro (P0):
          [INPUT] → [P10.A] → [P8.A] → [CONSULTAS] → [P3-P7] → [P10.B] → [OUTPUT]
        """
        self.logger.info("Iniciando traducción")
        self._texto_fuente = texto_fuente
        
        try:
            # P10.A: Limpieza
            self.estado.fase_actual = "P10.A: Limpieza"
            resultado_limpieza = self.renderizado.limpiar_texto(texto_fuente)
            texto_limpio = resultado_limpieza.texto_limpio
            self.logger.info(f"Limpieza completada: {len(resultado_limpieza.ruido_eliminado)} elementos eliminados")
            
            # Dividir en oraciones
            self._oraciones_fuente = Tokenizador.dividir_oraciones(texto_limpio)
            self.estado.total_oraciones = len(self._oraciones_fuente)
            self.logger.info(f"Oraciones detectadas: {self.estado.total_oraciones}")
            
            # P8.A: Análisis léxico (detección + tokenización + registro)
            self.estado.fase_actual = "P8.A: Análisis léxico"
            self._fase_analisis_lexico(texto_limpio)
            
            # Punto de consulta: Pre-traducción
            if self.gestor_consultas.hay_pendientes():
                self._procesar_consultas()
            
            # P3-P7: Traducción de cada oración
            self.estado.fase_actual = "P3-P7: Traducción"
            self._oraciones_traducidas = []
            
            for i, oracion in enumerate(self._oraciones_fuente):
                if self.estado.pausado:
                    self.logger.info("Proceso pausado")
                    break
                
                self.logger.debug(f"Traduciendo oración {i+1}/{self.estado.total_oraciones}")
                oracion_traducida = self._traducir_oracion(oracion)
                self._oraciones_traducidas.append(oracion_traducida)
                self.estado.oraciones_traducidas = i + 1
            
            # P10.B: Presentación
            self.estado.fase_actual = "P10.B: Presentación"
            self._texto_traducido = " ".join(self._oraciones_traducidas)
            
            self.estado.fase_actual = "COMPLETADO"
            self.logger.info("Traducción completada")
            
            return self._texto_traducido
            
        except RegistroIncompletoError as e:
            self.logger.error(f"FALLO CRÍTICO: Registro incompleto - {e}")
            self.estado.errores_criticos += 1
            raise
        
        except SinonimiaError as e:
            self.logger.error(f"FALLO CRÍTICO: Sinonimia - {e}")
            self.estado.errores_criticos += 1
            raise
        
        except Exception as e:
            self.logger.error(f"Error inesperado: {e}")
            raise
    
    def _fase_analisis_lexico(self, texto: str) -> None:
        """
        P8.A: Análisis léxico completo
        
        1. Detección de locuciones
        2. Tokenización
        3. Registro inicial
        4. Verificación de completitud
        """
        # Tokenizar
        tokens = Tokenizador.tokenizar(texto)
        
        # Clasificar tokens
        tokens_clasificados = []
        for token in tokens:
            cat, cat_gram = ClasificadorGramatical.clasificar(token)
            tokens_clasificados.append((token, cat, cat_gram))
        
        # Procesar en glosario
        self.glosario.fase_a_procesar(texto, tokens_clasificados)
        
        # Actualizar estado
        stats = self.glosario.obtener_estadisticas()
        self.estado.glosario_entradas = stats["total"]
        self.estado.glosario_asignadas = stats["asignadas"]
        self.estado.glosario_pendientes = stats["pendientes"]
        
        self.logger.info(f"Glosario: {stats['total']} entradas, {stats['locuciones']} locuciones")
    
    def _traducir_oracion(self, oracion: str) -> str:
        """
        Traducir una oración individual
        
        P3 → P4/P5 → P6 → P7 → resultado
        """
        # Crear matriz fuente
        mtx_s = self._crear_matriz_fuente(oracion)
        
        # Procesar con Core
        resultado = self.core.procesar_oracion(mtx_s)
        
        if not resultado.exito:
            self.logger.warning(f"Error en traducción: {resultado.mensaje}")
            # Intentar serializar lo que haya
            if resultado.mtx_t:
                return self.core.serializar_resultado()
            return f"[ERROR: {oracion}]"
        
        # Serializar resultado
        return self.core.serializar_resultado()
    
    def _crear_matriz_fuente(self, oracion: str) -> MatrizFuente:
        """Crear matriz fuente desde oración"""
        mtx = MatrizFuente()
        tokens = Tokenizador.tokenizar(oracion)
        
        for i, token in enumerate(tokens):
            # Agregar celda
            mtx.agregar_celda(token, i)
            
            # Clasificar y crear slot
            cat, cat_gram = ClasificadorGramatical.clasificar(token)
            
            if cat == TokenCategoria.NUCLEO:
                slot = crear_slot_n(token, cat_gram, i)
                mtx.agregar_slot_n(slot)
            else:
                slot = crear_slot_p(token, cat_gram, i)
                mtx.agregar_slot_p(slot)
        
        # Agregar locuciones del glosario
        for loc_id, loc in self.glosario.obtener_locuciones().items():
            mtx.agregar_locucion(loc)
        
        return mtx
    
    def _procesar_consultas(self) -> None:
        """Procesar consultas pendientes"""
        self.estado.consultas_pendientes = len(self.gestor_consultas.obtener_pendientes())
        
        if self.config.auto_decidir_timeout:
            # Aplicar recomendaciones automáticamente
            self.gestor_consultas.aplicar_recomendaciones_pendientes()
            self.logger.info("Consultas resueltas automáticamente")
        else:
            # Esperar respuesta del usuario (en modo interactivo)
            texto = self.gestor_consultas.formatear_consultas_bloque()
            print(texto)
    
    # ══════════════════════════════════════════════════════════
    # CALLBACKS DE CONTROL
    # ══════════════════════════════════════════════════════════
    
    def _on_pausa(self) -> None:
        """Callback para pausa"""
        self.estado.pausado = True
        self.logger.info("Proceso pausado por usuario")
    
    def _on_continuar(self) -> None:
        """Callback para continuar"""
        self.estado.pausado = False
        self.logger.info("Proceso reanudado")
    
    def _on_forzar(self) -> None:
        """Callback para forzar continuación"""
        self.logger.warning("Continuación forzada por usuario")
    
    def _on_reiniciar(self) -> None:
        """Callback para reiniciar"""
        self.glosario = Glosario()
        self.core = Core(self.glosario)
        self.core.set_procesador_nucleos(self.proc_nucleos)
        self.core.set_procesador_particulas(self.proc_particulas)
        self.core.set_reparador(self.reparador)
        self.estado = EstadoProceso()
        self.proc_comandos.set_glosario(self.glosario)
        self.proc_comandos.estado = self.estado
        self.logger.info("Sistema reiniciado")
    
    # ══════════════════════════════════════════════════════════
    # INTERFAZ PÚBLICA
    # ══════════════════════════════════════════════════════════
    
    def procesar_comando(self, comando: str) -> str:
        """Procesar comando del usuario"""
        resultado = self.proc_comandos.procesar(comando)
        return resultado.mensaje
    
    def obtener_glosario(self) -> str:
        """Obtener glosario formateado"""
        return self.glosario.formatear_glosario()
    
    def obtener_estado(self) -> str:
        """Obtener estado del proceso"""
        return self.estado.formatear()
    
    def exportar_glosario(self, formato: str = "json") -> str:
        """Exportar glosario"""
        if formato == "json":
            return self.glosario.exportar_json()
        elif formato == "csv":
            return self.glosario.exportar_csv()
        return self.glosario.exportar_txt()
    
    def importar_glosario(self, datos: str, formato: str = "json") -> bool:
        """Importar glosario"""
        if formato == "json":
            self.glosario = Glosario.importar_json(datos)
            self.core = Core(self.glosario)
            self.core.set_procesador_nucleos(self.proc_nucleos)
            self.core.set_procesador_particulas(self.proc_particulas)
            self.core.set_reparador(self.reparador)
            self.proc_comandos.set_glosario(self.glosario)
            return True
        return False
    
    def obtener_traduccion(self) -> str:
        """Obtener texto traducido"""
        return self._texto_traducido
    
    def obtener_modo_salida(self) -> ModoSalida:
        """Obtener modo de salida actual"""
        return self.config.modo_salida


# ──────────────────────────────────────────────────────────────
# INTERFAZ DE LÍNEA DE COMANDOS
# ──────────────────────────────────────────────────────────────

class CLI:
    """
    Interfaz de línea de comandos
    """
    
    def __init__(self):
        self.sistema = SistemaTraduccion()
        self._ejecutando = True
    
    def ejecutar(self) -> None:
        """Ejecutar CLI interactivo"""
        self._mostrar_bienvenida()
        
        while self._ejecutando:
            try:
                entrada = input("\n> ").strip()
                
                if not entrada:
                    continue
                
                # Comandos especiales
                if entrada.lower() in ["salir", "exit", "quit"]:
                    self._ejecutando = False
                    print("¡Hasta pronto!")
                    continue
                
                if entrada.lower() == "traducir":
                    self._modo_traduccion()
                    continue
                
                # Procesar como comando
                if entrada.startswith('[') or self._es_comando(entrada):
                    resultado = self.sistema.procesar_comando(entrada)
                    print(resultado)
                else:
                    # Texto para traducir
                    traduccion = self.sistema.traducir(entrada)
                    print(f"\n═══ TRADUCCIÓN ═══\n{traduccion}\n══════════════════")
                
            except KeyboardInterrupt:
                print("\n\nUse 'salir' para terminar.")
            except Exception as e:
                print(f"Error: {e}")
    
    def _mostrar_bienvenida(self) -> None:
        """Mostrar mensaje de bienvenida"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║     SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON       ║
║                                                              ║
║  Comandos:                                                   ║
║    [AYUDA]     - Ver comandos disponibles                    ║
║    [GLOSARIO]  - Ver glosario actual                         ║
║    [ESTADO]    - Ver estado del proceso                      ║
║    traducir    - Modo traducción multilínea                  ║
║    salir       - Terminar                                    ║
║                                                              ║
║  Ingrese texto directamente para traducir.                   ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    def _es_comando(self, texto: str) -> bool:
        """Verificar si es un comando"""
        palabras_comando = [
            "glosario", "locuciones", "alternativas", "decisiones",
            "configuracion", "estado", "ayuda", "protocolos",
            "actualiza", "añade", "elimina", "regla", "modo",
            "pausa", "continuar", "forzar", "reiniciar",
            "exportar", "importar"
        ]
        primera = texto.split()[0].lower() if texto else ""
        return primera in palabras_comando
    
    def _modo_traduccion(self) -> None:
        """Modo traducción multilínea"""
        print("Modo traducción. Ingrese texto (línea vacía para terminar):")
        lineas = []
        
        while True:
            linea = input()
            if not linea:
                break
            lineas.append(linea)
        
        if lineas:
            texto = "\n".join(lineas)
            traduccion = self.sistema.traducir(texto)
            print(f"\n═══ TRADUCCIÓN ═══\n{traduccion}\n══════════════════")


# ──────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ──────────────────────────────────────────────────────────────

def main():
    """Punto de entrada principal"""
    import sys
    
    if len(sys.argv) > 1:
        # Modo archivo
        archivo = sys.argv[1]
        if GestorArchivos.existe(archivo):
            texto = GestorArchivos.cargar_texto(archivo)
            if texto:
                sistema = SistemaTraduccion()
                traduccion = sistema.traducir(texto)
                print(traduccion)
                
                # Guardar resultado
                archivo_salida = archivo.rsplit('.', 1)[0] + "_traducido.txt"
                GestorArchivos.guardar_texto(traduccion, archivo_salida)
                print(f"\nTraducción guardada en: {archivo_salida}")
        else:
            print(f"Archivo no encontrado: {archivo}")
    else:
        # Modo interactivo
        cli = CLI()
        cli.ejecutar()


if __name__ == "__main__":
    main()
