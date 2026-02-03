# ==============================================================================
# 12. GESTOR DE COMANDOS DEL USUARIO (P11) - VERSIÓN COMPLETA
# ==============================================================================

import re
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum, auto

# Asegúrate de que estas referencias apunten a tus clases definidas anteriormente
# Si has unificado el archivo, estas clases ya deberían estar disponibles en el scope global.

# ------------------------------------------------------------------------------
# ENUMS Y ESTRUCTURAS
# ------------------------------------------------------------------------------

class CategoriaComando(Enum):
    """Categorías de comandos"""
    CONSULTA = auto()
    MODIFICACION = auto()
    CONTROL = auto()
    EXPORTACION = auto()
    AYUDA = auto()


@dataclass
class ResultadoComando:
    """Resultado de ejecución de comando"""
    exito: bool
    mensaje: str
    datos: Optional[Any] = None
    requiere_confirmacion: bool = False
    pregunta_confirmacion: str = ""


@dataclass
class DefinicionComando:
    """Definición de un comando"""
    nombre: str
    aliases: List[str]
    categoria: CategoriaComando
    descripcion: str
    uso: str
    ejemplo: str


# ------------------------------------------------------------------------------
# DEFINICIONES DE COMANDOS (REGISTRO COMPLETO)
# ------------------------------------------------------------------------------

COMANDOS = {
    # --- A. COMANDOS DE CONSULTA ---
    "GLOSARIO": DefinicionComando(
        nombre="GLOSARIO",
        aliases=["glosario", "g"],
        categoria=CategoriaComando.CONSULTA,
        descripcion="Mostrar estado actual del glosario",
        uso="[GLOSARIO]",
        ejemplo="[GLOSARIO]"
    ),
    "LOCUCIONES": DefinicionComando(
        nombre="LOCUCIONES",
        aliases=["locuciones", "loc"],
        categoria=CategoriaComando.CONSULTA,
        descripcion="Mostrar locuciones detectadas",
        uso="[LOCUCIONES]",
        ejemplo="[LOCUCIONES]"
    ),
    "ALTERNATIVAS": DefinicionComando(
        nombre="ALTERNATIVAS",
        aliases=["alternativas", "alt"],
        categoria=CategoriaComando.CONSULTA,
        descripcion="Mostrar opciones para términos de alto margen",
        uso="[ALTERNATIVAS]",
        ejemplo="[ALTERNATIVAS]"
    ),
    "DECISIONES": DefinicionComando(
        nombre="DECISIONES",
        aliases=["decisiones", "dec"],
        categoria=CategoriaComando.CONSULTA,
        descripcion="Mostrar historial de decisiones",
        uso="[DECISIONES] [filtro]",
        ejemplo="[DECISIONES usuario]"
    ),
    "CONFIGURACION": DefinicionComando(
        nombre="CONFIGURACION",
        aliases=["configuracion", "config", "conf"],
        categoria=CategoriaComando.CONSULTA,
        descripcion="Mostrar configuración activa",
        uso="[CONFIGURACION]",
        ejemplo="[CONFIGURACION]"
    ),
    "ESTADO": DefinicionComando(
        nombre="ESTADO",
        aliases=["estado", "est"],
        categoria=CategoriaComando.CONSULTA,
        descripcion="Mostrar estado del proceso",
        uso="[ESTADO]",
        ejemplo="[ESTADO]"
    ),
    
    # --- B. COMANDOS DE MODIFICACIÓN ---
    "ACTUALIZA": DefinicionComando(
        nombre="ACTUALIZA",
        aliases=["actualiza", "act"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Modificar entrada del glosario",
        uso="[ACTUALIZA token = nueva_traduccion]",
        ejemplo="[ACTUALIZA nafs = espíritu]"
    ),
    "AÑADE": DefinicionComando(
        nombre="AÑADE",
        aliases=["añade", "add"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Añadir entrada nueva",
        uso="[AÑADE token = traduccion]",
        ejemplo="[AÑADE kalima = verbo]"
    ),
    "AÑADE_LOCUCION": DefinicionComando(
        nombre="AÑADE LOCUCION",
        aliases=["añade locucion", "add loc"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Registrar nueva locución",
        uso="[AÑADE LOCUCION src = A-B-C]",
        ejemplo="[AÑADE LOCUCION bi-ʿayni-hā = por-ojo-suyo]"
    ),
    "ELIMINA": DefinicionComando(
        nombre="ELIMINA",
        aliases=["elimina", "del"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Eliminar entrada del glosario",
        uso="[ELIMINA token]",
        ejemplo="[ELIMINA nafs]"
    ),
    "REGLA": DefinicionComando(
        nombre="REGLA",
        aliases=["regla"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Añadir regla personalizada",
        uso="[REGLA siempre/nunca/cuando...]",
        ejemplo="[REGLA siempre transliterar términos técnicos]"
    ),
    "BORRA_REGLA": DefinicionComando(
        nombre="BORRA REGLA",
        aliases=["borra regla"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Eliminar regla personalizada",
        uso="[BORRA REGLA N]",
        ejemplo="[BORRA REGLA 2]"
    ),
    "MODO_TRANSLITERACION": DefinicionComando(
        nombre="MODO TRANSLITERACION",
        aliases=["modo transliteracion", "modo translit"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Cambiar modo de transliteración",
        uso="[MODO TRANSLITERACION desactivado|selectivo|completo]",
        ejemplo="[MODO TRANSLITERACION selectivo]"
    ),
    "MODO_BORRADOR": DefinicionComando(
        nombre="MODO BORRADOR",
        aliases=["modo borrador"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Activar modo borrador",
        uso="[MODO BORRADOR]",
        ejemplo="[MODO BORRADOR]"
    ),
    "MODO_FINAL": DefinicionComando(
        nombre="MODO FINAL",
        aliases=["modo final"],
        categoria=CategoriaComando.MODIFICACION,
        descripcion="Activar modo final",
        uso="[MODO FINAL]",
        ejemplo="[MODO FINAL]"
    ),
    
    # --- C. COMANDOS DE CONTROL ---
    "PAUSA": DefinicionComando(
        nombre="PAUSA",
        aliases=["pausa", "pause"],
        categoria=CategoriaComando.CONTROL,
        descripcion="Detener traducción",
        uso="[PAUSA]",
        ejemplo="[PAUSA]"
    ),
    "CONTINUAR": DefinicionComando(
        nombre="CONTINUAR",
        aliases=["continuar", "cont"],
        categoria=CategoriaComando.CONTROL,
        descripcion="Reanudar traducción",
        uso="[CONTINUAR]",
        ejemplo="[CONTINUAR]"
    ),
    "FORZAR": DefinicionComando(
        nombre="FORZAR",
        aliases=["forzar", "force"],
        categoria=CategoriaComando.CONTROL,
        descripcion="Continuar tras FALLO CRÍTICO",
        uso="[FORZAR]",
        ejemplo="[FORZAR]"
    ),
    "REINICIAR": DefinicionComando(
        nombre="REINICIAR",
        aliases=["reiniciar", "reset"],
        categoria=CategoriaComando.CONTROL,
        descripcion="Reiniciar traducción",
        uso="[REINICIAR]",
        ejemplo="[REINICIAR]"
    ),
    "SALTAR": DefinicionComando(
        nombre="SALTAR",
        aliases=["saltar", "skip"],
        categoria=CategoriaComando.CONTROL,
        descripcion="Saltar N oraciones",
        uso="[SALTAR N]",
        ejemplo="[SALTAR 5]"
    ),
    "VOLVER": DefinicionComando(
        nombre="VOLVER",
        aliases=["volver", "back"],
        categoria=CategoriaComando.CONTROL,
        descripcion="Retraducir últimas N oraciones",
        uso="[VOLVER N]",
        ejemplo="[VOLVER 3]"
    ),
    
    # --- D. COMANDOS DE EXPORTACIÓN ---
    "EXPORTAR_GLOSARIO": DefinicionComando(
        nombre="EXPORTAR GLOSARIO",
        aliases=["exportar glosario", "export glos"],
        categoria=CategoriaComando.EXPORTACION,
        descripcion="Exportar glosario",
        uso="[EXPORTAR GLOSARIO txt|csv|json]",
        ejemplo="[EXPORTAR GLOSARIO json]"
    ),
    "EXPORTAR_TRADUCCION": DefinicionComando(
        nombre="EXPORTAR TRADUCCION",
        aliases=["exportar traduccion", "export trad"],
        categoria=CategoriaComando.EXPORTACION,
        descripcion="Exportar texto traducido",
        uso="[EXPORTAR TRADUCCION txt|md]",
        ejemplo="[EXPORTAR TRADUCCION md]"
    ),
    "IMPORTAR_GLOSARIO": DefinicionComando(
        nombre="IMPORTAR GLOSARIO",
        aliases=["importar glosario", "import glos"],
        categoria=CategoriaComando.EXPORTACION,
        descripcion="Importar glosario",
        uso="[IMPORTAR GLOSARIO fuente]",
        ejemplo="[IMPORTAR GLOSARIO glosario_anterior.json]"
    ),
    
    # --- E. COMANDOS DE AYUDA ---
    "AYUDA": DefinicionComando(
        nombre="AYUDA",
        aliases=["ayuda", "help", "?"],
        categoria=CategoriaComando.AYUDA,
        descripcion="Mostrar lista de comandos",
        uso="[AYUDA] [comando]",
        ejemplo="[AYUDA ACTUALIZA]"
    ),
    "PROTOCOLOS": DefinicionComando(
        nombre="PROTOCOLOS",
        aliases=["protocolos", "prot"],
        categoria=CategoriaComando.AYUDA,
        descripcion="Mostrar resumen de protocolos",
        uso="[PROTOCOLOS]",
        ejemplo="[PROTOCOLOS]"
    ),
    "PROTOCOLO": DefinicionComando(
        nombre="PROTOCOLO",
        aliases=["protocolo"],
        categoria=CategoriaComando.AYUDA,
        descripcion="Mostrar detalle de protocolo",
        uso="[PROTOCOLO N]",
        ejemplo="[PROTOCOLO 6]"
    ),
}

# ------------------------------------------------------------------------------
# PROCESADOR DE COMANDOS
# ------------------------------------------------------------------------------

class ProcesadorComandos:
    """
    Procesador de comandos del usuario (P11)
    """
    
    def __init__(self, glosario: Glosario = None, 
                 config: ConfiguracionSistema = None, 
                 estado: EstadoProceso = None):
        self.glosario = glosario
        self.config = config
        self.estado = estado
        
        # Gestor de consultas (necesario para ver historial)
        # Nota: En una estructura unificada, esto podría pasarse o ser una global
        self.gestor_consultas = GestorConsultas() 
        
        # Callbacks para comandos de control
        self._callbacks: Dict[str, Callable] = {}
        
        # Estado de confirmación pendiente
        self._confirmacion_pendiente: Optional[Tuple[str, Callable]] = None
    
    def set_glosario(self, glosario: Glosario) -> None:
        """Establecer glosario dinámicamente"""
        self.glosario = glosario
    
    def set_callback(self, comando: str, callback: Callable) -> None:
        """Establecer callback para comando"""
        self._callbacks[comando.upper()] = callback
    
    def procesar(self, entrada: str) -> ResultadoComando:
        """
        Procesar entrada del usuario.
        Detecta si es un comando y lo ejecuta.
        """
        entrada = entrada.strip()
        
        # Verificar si hay confirmación pendiente
        if self._confirmacion_pendiente:
            return self._procesar_confirmacion(entrada)
        
        # Detectar comando
        comando, args = self._parsear_comando(entrada)
        
        if not comando:
            return ResultadoComando(
                exito=False,
                mensaje="Comando no reconocido. Use [AYUDA]."
            )
        
        # Ejecutar comando
        return self._ejecutar_comando(comando, args)
    
    def _parsear_comando(self, entrada: str) -> Tuple[Optional[str], str]:
        """Parsear entrada para extraer comando y argumentos"""
        # Quitar corchetes si los hay
        if entrada.startswith('[') and entrada.endswith(']'):
            entrada = entrada[1:-1]
        
        entrada = entrada.strip()
        
        # Buscar comando
        for nombre, defn in COMANDOS.items():
            # Verificar nombre exacto
            if entrada.upper().startswith(nombre):
                args = entrada[len(nombre):].strip()
                return nombre, args
            
            # Verificar aliases
            for alias in defn.aliases:
                if entrada.lower().startswith(alias):
                    args = entrada[len(alias):].strip()
                    return nombre, args
        
        return None, ""
    
    def _ejecutar_comando(self, comando: str, args: str) -> ResultadoComando:
        """Ejecutar comando específico según su definición"""
        
        # --- A. CONSULTA ---
        if comando == "GLOSARIO":
            return self._cmd_glosario(args)
        
        elif comando == "LOCUCIONES":
            return self._cmd_locuciones()
        
        elif comando == "ALTERNATIVAS":
            return self._cmd_alternativas()
        
        elif comando == "DECISIONES":
            return self._cmd_decisiones(args)
        
        elif comando == "CONFIGURACION":
            return self._cmd_configuracion()
        
        elif comando == "ESTADO":
            return self._cmd_estado()
        
        # --- B. MODIFICACIÓN ---
        elif comando == "ACTUALIZA":
            return self._cmd_actualiza(args)
        
        elif comando == "AÑADE":
            return self._cmd_añade(args)
        
        elif comando == "AÑADE_LOCUCION": # Alias: AÑADE LOCUCION -> Nombre: AÑADE LOCUCION
            return self._cmd_añade_locucion(args)
        
        elif comando == "ELIMINA":
            return self._cmd_elimina(args)
        
        elif comando == "REGLA":
            return self._cmd_regla(args)
        
        elif comando == "BORRA_REGLA":
            return self._cmd_borra_regla(args)
        
        elif comando == "MODO_TRANSLITERACION":
            return self._cmd_modo_transliteracion(args)
        
        elif comando == "MODO_BORRADOR":
            return self._cmd_modo_salida(ModoSalida.BORRADOR)
        
        elif comando == "MODO_FINAL":
            return self._cmd_modo_salida(ModoSalida.FINAL)
        
        # --- C. CONTROL ---
        elif comando == "PAUSA":
            return self._cmd_pausa()
        
        elif comando == "CONTINUAR":
            return self._cmd_continuar()
        
        elif comando == "FORZAR":
            return self._cmd_forzar()
        
        elif comando == "REINICIAR":
            return self._cmd_reiniciar()
        
        elif comando == "SALTAR":
            return self._cmd_saltar(args)
        
        elif comando == "VOLVER":
            return self._cmd_volver(args)
        
        # --- D. EXPORTACIÓN ---
        elif comando == "EXPORTAR_GLOSARIO":
            return self._cmd_exportar_glosario(args)
        
        elif comando == "EXPORTAR_TRADUCCION":
            return self._cmd_exportar_traduccion(args)
        
        elif comando == "IMPORTAR_GLOSARIO":
            return self._cmd_importar_glosario(args)
        
        # --- E. AYUDA ---
        elif comando == "AYUDA":
            return self._cmd_ayuda(args)
        
        elif comando == "PROTOCOLOS":
            return self._cmd_protocolos()
        
        elif comando == "PROTOCOLO":
            return self._cmd_protocolo(args)
        
        return ResultadoComando(exito=False, mensaje="Comando reconocido pero no implementado en dispatch.")

    # --------------------------------------------------------------------------
    # IMPLEMENTACIÓN: CONSULTA
    # --------------------------------------------------------------------------
    
    def _cmd_glosario(self, args: str) -> ResultadoComando:
        if not self.glosario: return ResultadoComando(False, "Glosario no disponible")
        texto = self.glosario.formatear_glosario()
        return ResultadoComando(True, texto)
    
    def _cmd_locuciones(self) -> ResultadoComando:
        if not self.glosario: return ResultadoComando(False, "Glosario no disponible")
        texto = self.glosario.formatear_locuciones()
        return ResultadoComando(True, texto)
    
    def _cmd_alternativas(self) -> ResultadoComando:
        if not self.glosario: return ResultadoComando(False, "Glosario no disponible")
        texto = self.glosario.formatear_alternativas()
        return ResultadoComando(True, texto)
    
    def _cmd_decisiones(self, args: str) -> ResultadoComando:
        # Requiere acceso al gestor de consultas real usado por el sistema
        # Aquí asumimos una conexión básica
        filtro = args.strip() if args else None
        texto = self.gestor_consultas.formatear_historial(filtro)
        return ResultadoComando(True, texto)
    
    def _cmd_configuracion(self) -> ResultadoComando:
        lineas = ["CONFIGURACIÓN ACTIVA", "="*20,
                  f"Modo Transliteración: {self.config.modo_transliteracion.name}",
                  f"Modo Salida: {self.config.modo_salida.name}",
                  "", "REGLAS ACTIVAS:"]
        for r in self.config.reglas_permanentes + self.config.reglas_sesion:
            lineas.append(f"- {r.tipo}: {r.accion} ({r.condicion or 'global'})")
        return ResultadoComando(True, "\n".join(lineas))
    
    def _cmd_estado(self) -> ResultadoComando:
        if not self.estado: return ResultadoComando(False, "Estado no disponible")
        return ResultadoComando(True, self.estado.formatear())

    # --------------------------------------------------------------------------
    # IMPLEMENTACIÓN: MODIFICACIÓN
    # --------------------------------------------------------------------------

    def _cmd_actualiza(self, args: str) -> ResultadoComando:
        if not self.glosario: return ResultadoComando(False, "Glosario no disponible")
        match = re.match(r'(\S+)\s*=\s*(.+)', args)
        if not match: return ResultadoComando(False, "Formato: [ACTUALIZA token = nueva]")
        token, nueva = match.groups()
        token = token.strip()
        nueva = nueva.strip()

        entrada = self.glosario.obtener_entrada(token)
        if not entrada: return ResultadoComando(False, f"Token '{token}' no existe.")

        self._confirmacion_pendiente = (f"upd_{token}", lambda: self._ejecutar_actualiza(token, nueva))
        return ResultadoComando(True, f"¿Cambiar '{entrada.token_tgt}' a '{nueva}' para '{token}'?", requiere_confirmacion=True)

    def _ejecutar_actualiza(self, token, nueva):
        self.glosario.actualizar_entrada(token, nueva)
        return ResultadoComando(True, f"Actualizado: {token} -> {nueva}")

    def _cmd_añade(self, args: str) -> ResultadoComando:
        if not self.glosario: return ResultadoComando(False, "Glosario no disponible")
        match = re.match(r'(\S+)\s*=\s*(.+)', args)
        if not match: return ResultadoComando(False, "Formato: [AÑADE token = traduccion]")
        token, trad = match.groups()
        
        if self.glosario.agregar_entrada(token.strip(), TokenCategoria.NUCLEO, trad.strip()):
            return ResultadoComando(True, f"Añadido: {token} -> {trad}")
        return ResultadoComando(False, f"Token '{token}' ya existe.")

    def _cmd_añade_locucion(self, args: str) -> ResultadoComando:
        if not self.glosario: return ResultadoComando(False, "Glosario no disponible")
        match = re.match(r'(\S+)\s*=\s*(.+)', args)
        if not match: return ResultadoComando(False, "Formato: [AÑADE LOCUCION src = A-B-C]")
        src, tgt = match.groups()
        componentes = src.replace("-", " ").split()
        # Generar posiciones dummy, se ajustarán en runtime real
        self.glosario.agregar_locucion(src.strip(), componentes, [], tgt.strip())
        return ResultadoComando(True, f"Locución registrada: {src} -> {tgt}")

    def _cmd_elimina(self, args: str) -> ResultadoComando:
        token = args.strip()
        if not self.glosario.obtener_entrada(token): return ResultadoComando(False, "Token no encontrado")
        self._confirmacion_pendiente = (f"del_{token}", lambda: self._ejecutar_elimina(token))
        return ResultadoComando(True, f"¿Eliminar '{token}' del glosario?", requiere_confirmacion=True)

    def _ejecutar_elimina(self, token):
        self.glosario.eliminar_entrada(token)
        return ResultadoComando(True, f"Eliminado: {token}")

    def _cmd_regla(self, args: str) -> ResultadoComando:
        tipo = "siempre"
        if args.lower().startswith("nunca"): tipo = "nunca"
        elif args.lower().startswith("cuando"): tipo = "cuando"
        self.config.agregar_regla(tipo, args)
        return ResultadoComando(True, f"Regla registrada: {args}")

    def _cmd_borra_regla(self, args: str) -> ResultadoComando:
        try:
            idx = int(args) - 1
            if self.config.eliminar_regla(idx): return ResultadoComando(True, "Regla eliminada")
            return ResultadoComando(False, "Índice inválido")
        except: return ResultadoComando(False, "Use un número")

    def _cmd_modo_transliteracion(self, args: str) -> ResultadoComando:
        modos = {"desactivado": ModoTransliteracion.DESACTIVADO, "selectivo": ModoTransliteracion.SELECTIVO, "completo": ModoTransliteracion.COMPLETO}
        if args.lower() in modos:
            self.config.modo_transliteracion = modos[args.lower()]
            return ResultadoComando(True, f"Modo transliteración: {args.upper()}")
        return ResultadoComando(False, "Modos: desactivado | selectivo | completo")

    def _cmd_modo_salida(self, modo: ModoSalida) -> ResultadoComando:
        self.config.modo_salida = modo
        return ResultadoComando(True, f"Modo salida: {modo.name}")

    # --------------------------------------------------------------------------
    # IMPLEMENTACIÓN: CONTROL
    # --------------------------------------------------------------------------

    def _cmd_pausa(self) -> ResultadoComando:
        if "PAUSA" in self._callbacks: self._callbacks["PAUSA"]()
        return ResultadoComando(True, "Sistema pausado")

    def _cmd_continuar(self) -> ResultadoComando:
        if "CONTINUAR" in self._callbacks: self._callbacks["CONTINUAR"]()
        return ResultadoComando(True, "Sistema reanudado")

    def _cmd_forzar(self) -> ResultadoComando:
        if "FORZAR" in self._callbacks: self._callbacks["FORZAR"]()
        return ResultadoComando(True, "Continuando forzosamente")

    def _cmd_reiniciar(self) -> ResultadoComando:
        self._confirmacion_pendiente = ("reset", self._ejecutar_reiniciar)
        return ResultadoComando(True, "REINICIAR: A) Conservar Glosario, B) Todo Nuevo. ¿A o B?", requiere_confirmacion=True)

    def _ejecutar_reiniciar(self):
        # La lógica real de reiniciar depende del callback en main
        if "REINICIAR" in self._callbacks: self._callbacks["REINICIAR"]()
        return ResultadoComando(True, "Sistema reiniciado")

    def _cmd_saltar(self, args: str) -> ResultadoComando:
        # Implementación stub para demo
        return ResultadoComando(True, f"Saltando {args} oraciones (Stub)")

    def _cmd_volver(self, args: str) -> ResultadoComando:
        return ResultadoComando(True, f"Volviendo {args} oraciones (Stub)")

    # --------------------------------------------------------------------------
    # IMPLEMENTACIÓN: EXPORTACIÓN
    # --------------------------------------------------------------------------

    def _cmd_exportar_glosario(self, args: str) -> ResultadoComando:
        fmt = args.lower() if args else "txt"
        if not self.glosario: return ResultadoComando(False, "Sin glosario")
        if fmt == "json": res = self.glosario.exportar_json()
        elif fmt == "csv": res = self.glosario.exportar_csv()
        else: res = self.glosario.exportar_txt()
        return ResultadoComando(True, f"Glosario exportado ({fmt}):\n{res[:100]}...")

    def _cmd_exportar_traduccion(self, args: str) -> ResultadoComando:
        return ResultadoComando(True, "Traducción exportada (Stub)")

    def _cmd_importar_glosario(self, args: str) -> ResultadoComando:
        return ResultadoComando(True, f"Importando desde {args} (Stub)")

    # --------------------------------------------------------------------------
    # IMPLEMENTACIÓN: AYUDA
    # --------------------------------------------------------------------------

    def _cmd_ayuda(self, args: str) -> ResultadoComando:
        if args:
            nombre = args.upper()
            if nombre in COMANDOS:
                cmd = COMANDOS[nombre]
                return ResultadoComando(True, f"{cmd.nombre}\n{cmd.descripcion}\nUso: {cmd.uso}")
            return ResultadoComando(False, "Comando no encontrado")
        
        # Ayuda general
        lista = sorted(COMANDOS.keys())
        return ResultadoComando(True, "Comandos disponibles:\n" + ", ".join([f"[{c}]" for c in lista]))

    def _cmd_protocolos(self) -> ResultadoComando:
        return ResultadoComando(True, "Lista de protocolos: P0..P11 (Ver documentación)")

    def _cmd_protocolo(self, args: str) -> ResultadoComando:
        return ResultadoComando(True, f"Detalle del protocolo {args} (Stub)")

    # --------------------------------------------------------------------------
    # LÓGICA DE CONFIRMACIÓN
    # --------------------------------------------------------------------------

    def _procesar_confirmacion(self, entrada: str) -> ResultadoComando:
        entrada = entrada.lower()
        if entrada in ["sí", "si", "s", "yes", "y", "a", "b"]: # A/B para reinicio
            _, callback = self._confirmacion_pendiente
            self._confirmacion_pendiente = None
            return callback()
        elif entrada in ["no", "n", "cancelar"]:
            self._confirmacion_pendiente = None
            return ResultadoComando(True, "Operación cancelada")
        else:
            return ResultadoComando(False, "Responda sí o no", requiere_confirmacion=True)

# Instancia global para facilitar acceso
_procesador_comandos = ProcesadorComandos()
def obtener_procesador_comandos(): return _procesador_comandos
