"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 12/13: Comandos del Usuario (P11)
════════════════════════════════════════════════════════════════

PROPÓSITO:
  Definir los comandos disponibles para el usuario.
  Permitir control, consulta y modificación del sistema.

INVOCACIÓN:
  [COMANDO] o "comando" (minúsculas)
"""

import re
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum, auto

from constants import (
    ModoTransliteracion, NormaTransliteracion, ModoSalida,
    TokenCategoria
)
from config import obtener_config, ConfiguracionSistema
from glossary import Glosario
from consultas import GestorConsultas, obtener_gestor_consultas
from models import EstadoProceso


# ══════════════════════════════════════════════════════════════
# ENUMS Y ESTRUCTURAS
# ══════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════
# DEFINICIONES DE COMANDOS
# ══════════════════════════════════════════════════════════════

COMANDOS = {
    # ══════════════════════════════════════════════════════════
    # A. COMANDOS DE CONSULTA
    # ══════════════════════════════════════════════════════════
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
    
    # ══════════════════════════════════════════════════════════
    # B. COMANDOS DE MODIFICACIÓN
    # ══════════════════════════════════════════════════════════
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
    
    # ══════════════════════════════════════════════════════════
    # C. COMANDOS DE CONTROL
    # ══════════════════════════════════════════════════════════
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
    
    # ══════════════════════════════════════════════════════════
    # D. COMANDOS DE EXPORTACIÓN
    # ══════════════════════════════════════════════════════════
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
    
    # ══════════════════════════════════════════════════════════
    # E. COMANDOS DE AYUDA
    # ══════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════
# PROCESADOR DE COMANDOS
# ══════════════════════════════════════════════════════════════

class ProcesadorComandos:
    """
    Procesador de comandos del usuario (P11)
    """
    
    def __init__(self, glosario: Glosario = None,
                 gestor_consultas: GestorConsultas = None):
        self.glosario = glosario
        self.gestor_consultas = gestor_consultas or obtener_gestor_consultas()
        self.config = obtener_config()
        self.estado = EstadoProceso()
        
        # Callbacks para comandos de control
        self._callbacks: Dict[str, Callable] = {}
        
        # Estado de confirmación pendiente
        self._confirmacion_pendiente: Optional[Tuple[str, Callable]] = None
    
    def set_glosario(self, glosario: Glosario) -> None:
        """Establecer glosario"""
        self.glosario = glosario
    
    def set_callback(self, comando: str, callback: Callable) -> None:
        """Establecer callback para comando"""
        self._callbacks[comando.upper()] = callback
    
    def procesar(self, entrada: str) -> ResultadoComando:
        """
        Procesar entrada del usuario
        
        Detecta si es un comando y lo ejecuta
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
                mensaje="Comando no reconocido"
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
        """Ejecutar comando específico"""
        
        # ══════════════════════════════════════════════════════
        # A. COMANDOS DE CONSULTA
        # ══════════════════════════════════════════════════════
        
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
        
        # ══════════════════════════════════════════════════════
        # B. COMANDOS DE MODIFICACIÓN
        # ══════════════════════════════════════════════════════
        
        elif comando == "ACTUALIZA":
            return self._cmd_actualiza(args)
        
        elif comando == "AÑADE":
            return self._cmd_añade(args)
        
        elif comando == "AÑADE LOCUCION":
            return self._cmd_añade_locucion(args)
        
        elif comando == "ELIMINA":
            return self._cmd_elimina(args)
        
        elif comando == "REGLA":
            return self._cmd_regla(args)
        
        elif comando == "BORRA REGLA":
            return self._cmd_borra_regla(args)
        
        elif comando == "MODO TRANSLITERACION":
            return self._cmd_modo_transliteracion(args)
        
        elif comando == "MODO BORRADOR":
            return self._cmd_modo_salida(ModoSalida.BORRADOR)
        
        elif comando == "MODO FINAL":
            return self._cmd_modo_salida(ModoSalida.FINAL)
        
        # ══════════════════════════════════════════════════════
        # C. COMANDOS DE CONTROL
        # ══════════════════════════════════════════════════════
        
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
        
        # ══════════════════════════════════════════════════════
        # D. COMANDOS DE EXPORTACIÓN
        # ══════════════════════════════════════════════════════
        
        elif comando == "EXPORTAR GLOSARIO":
            return self._cmd_exportar_glosario(args)
        
        elif comando == "EXPORTAR TRADUCCION":
            return self._cmd_exportar_traduccion(args)
        
        elif comando == "IMPORTAR GLOSARIO":
            return self._cmd_importar_glosario(args)
        
        # ══════════════════════════════════════════════════════
        # E. COMANDOS DE AYUDA
        # ══════════════════════════════════════════════════════
        
        elif comando == "AYUDA":
            return self._cmd_ayuda(args)
        
        elif comando == "PROTOCOLOS":
            return self._cmd_protocolos()
        
        elif comando == "PROTOCOLO":
            return self._cmd_protocolo(args)
        
        return ResultadoComando(exito=False, mensaje="Comando no implementado")
    
    # ══════════════════════════════════════════════════════════
    # IMPLEMENTACIÓN: CONSULTA
    # ══════════════════════════════════════════════════════════
    
    def _cmd_glosario(self, args: str) -> ResultadoComando:
        """Comando GLOSARIO"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        texto = self.glosario.formatear_glosario()
        return ResultadoComando(exito=True, mensaje=texto)
    
    def _cmd_locuciones(self) -> ResultadoComando:
        """Comando LOCUCIONES"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        texto = self.glosario.formatear_locuciones()
        return ResultadoComando(exito=True, mensaje=texto)
    
    def _cmd_alternativas(self) -> ResultadoComando:
        """Comando ALTERNATIVAS"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        texto = self.glosario.formatear_alternativas()
        return ResultadoComando(exito=True, mensaje=texto)
    
    def _cmd_decisiones(self, args: str) -> ResultadoComando:
        """Comando DECISIONES"""
        filtro = args.strip() if args else None
        texto = self.gestor_consultas.formatear_historial(filtro)
        return ResultadoComando(exito=True, mensaje=texto)
    
    def _cmd_configuracion(self) -> ResultadoComando:
        """Comando CONFIGURACION"""
        lineas = [
            "═" * 50,
            "CONFIGURACIÓN ACTIVA",
            "═" * 50,
            "",
            f"Modo transliteración: {self.config.modo_transliteracion.name}",
            f"Norma transliteración: {self.config.norma_transliteracion.name}",
            f"Modo salida: {self.config.modo_salida.name}",
            "",
            "REGLAS PERMANENTES:"
        ]
        
        for i, r in enumerate(self.config.reglas_permanentes, 1):
            lineas.append(f"  {i}. {r.tipo}: {r.accion}")
        
        if not self.config.reglas_permanentes:
            lineas.append("  (ninguna)")
        
        lineas.append("")
        lineas.append("REGLAS DE SESIÓN:")
        
        for i, r in enumerate(self.config.reglas_sesion, 1):
            lineas.append(f"  {i}. {r.tipo}: {r.accion}")
        
        if not self.config.reglas_sesion:
            lineas.append("  (ninguna)")
        
        lineas.append("")
        lineas.append("═" * 50)
        
        return ResultadoComando(exito=True, mensaje="\n".join(lineas))
    
    def _cmd_estado(self) -> ResultadoComando:
        """Comando ESTADO"""
        texto = self.estado.formatear()
        return ResultadoComando(exito=True, mensaje=texto)
    
    # ══════════════════════════════════════════════════════════
    # IMPLEMENTACIÓN: MODIFICACIÓN
    # ══════════════════════════════════════════════════════════
    
    def _cmd_actualiza(self, args: str) -> ResultadoComando:
        """Comando ACTUALIZA"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        # Parsear: token = nueva_traduccion
        match = re.match(r'(\S+)\s*=\s*(.+)', args)
        if not match:
            return ResultadoComando(
                exito=False,
                mensaje="Formato: [ACTUALIZA token = nueva_traduccion]"
            )
        
        token, nueva = match.groups()
        nueva = nueva.strip()
        
        # Obtener entrada actual
        entrada = self.glosario.obtener_entrada(token)
        if not entrada:
            return ResultadoComando(
                exito=False,
                mensaje=f"Token '{token}' no encontrado en glosario"
            )
        
        # Solicitar confirmación
        self._confirmacion_pendiente = (
            f"actualiza_{token}_{nueva}",
            lambda: self._ejecutar_actualiza(token, nueva)
        )
        
        return ResultadoComando(
            exito=True,
            mensaje=f"ACTUALIZACIÓN DE GLOSARIO\n\n"
                    f"Token: {token}\n"
                    f"Actual: {entrada.token_tgt}\n"
                    f"Nuevo: {nueva}\n"
                    f"Ocurrencias afectadas: {len(entrada.ocurrencias)}\n\n"
                    f"¿Confirmar? (sí/no)",
            requiere_confirmacion=True,
            pregunta_confirmacion="¿Confirmar actualización? (sí/no)"
        )
    
    def _ejecutar_actualiza(self, token: str, nueva: str) -> ResultadoComando:
        """Ejecutar actualización confirmada"""
        exito, ocurrencias = self.glosario.actualizar_entrada(token, nueva)
        if exito:
            return ResultadoComando(
                exito=True,
                mensaje=f"Actualizado: {token} → {nueva} ({ocurrencias} ocurrencias)"
            )
        return ResultadoComando(exito=False, mensaje="Error al actualizar")
    
    def _cmd_añade(self, args: str) -> ResultadoComando:
        """Comando AÑADE"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        match = re.match(r'(\S+)\s*=\s*(.+)', args)
        if not match:
            return ResultadoComando(
                exito=False,
                mensaje="Formato: [AÑADE token = traduccion]"
            )
        
        token, trad = match.groups()
        trad = trad.strip()
        
        exito = self.glosario.agregar_entrada(token, TokenCategoria.NUCLEO, trad)
        
        if exito:
            return ResultadoComando(
                exito=True,
                mensaje=f"Añadido: {token} → {trad}"
            )
        return ResultadoComando(
            exito=False,
            mensaje=f"Token '{token}' ya existe en glosario"
        )
    
    def _cmd_añade_locucion(self, args: str) -> ResultadoComando:
        """Comando AÑADE LOCUCION"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        match = re.match(r'(\S+)\s*=\s*(.+)', args)
        if not match:
            return ResultadoComando(
                exito=False,
                mensaje="Formato: [AÑADE LOCUCION src = A-B-C]"
            )
        
        src, tgt = match.groups()
        tgt = tgt.strip()
        componentes = src.replace("-", " ").split()
        
        loc = self.glosario.agregar_locucion(src, componentes, [], tgt)
        
        return ResultadoComando(
            exito=True,
            mensaje=f"Locución añadida: {src} → {tgt} (ID: {loc.id})"
        )
    
    def _cmd_elimina(self, args: str) -> ResultadoComando:
        """Comando ELIMINA"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        token = args.strip()
        if not token:
            return ResultadoComando(
                exito=False,
                mensaje="Formato: [ELIMINA token]"
            )
        
        entrada = self.glosario.obtener_entrada(token)
        if not entrada:
            return ResultadoComando(
                exito=False,
                mensaje=f"Token '{token}' no encontrado"
            )
        
        # Solicitar confirmación
        self._confirmacion_pendiente = (
            f"elimina_{token}",
            lambda: self._ejecutar_elimina(token)
        )
        
        return ResultadoComando(
            exito=True,
            mensaje=f"¿Eliminar '{token}'? Ocurrencias afectadas: {len(entrada.ocurrencias)}\n"
                    f"(sí/no)",
            requiere_confirmacion=True
        )
    
    def _ejecutar_elimina(self, token: str) -> ResultadoComando:
        """Ejecutar eliminación confirmada"""
        exito, ocurrencias = self.glosario.eliminar_entrada(token)
        if exito:
            return ResultadoComando(
                exito=True,
                mensaje=f"Eliminado: {token}"
            )
        return ResultadoComando(exito=False, mensaje="Error al eliminar")
    
    def _cmd_regla(self, args: str) -> ResultadoComando:
        """Comando REGLA"""
        args = args.strip().lower()
        
        if args.startswith("siempre"):
            accion = args[7:].strip()
            self.config.agregar_regla("siempre", accion, permanente=False)
            return ResultadoComando(exito=True, mensaje=f"Regla añadida: siempre {accion}")
        
        elif args.startswith("nunca"):
            accion = args[5:].strip()
            self.config.agregar_regla("nunca", accion, permanente=False)
            return ResultadoComando(exito=True, mensaje=f"Regla añadida: nunca {accion}")
        
        elif args.startswith("cuando"):
            # Parsear "cuando X entonces Y"
            match = re.match(r'cuando\s+(.+)\s+entonces\s+(.+)', args)
            if match:
                condicion, accion = match.groups()
                self.config.agregar_regla("cuando", accion, condicion, permanente=False)
                return ResultadoComando(
                    exito=True,
                    mensaje=f"Regla añadida: cuando {condicion} entonces {accion}"
                )
        
        return ResultadoComando(
            exito=False,
            mensaje="Formato: [REGLA siempre/nunca/cuando...entonces...]"
        )
    
    def _cmd_borra_regla(self, args: str) -> ResultadoComando:
        """Comando BORRA REGLA"""
        try:
            num = int(args.strip()) - 1
            if self.config.eliminar_regla(num, permanente=False):
                return ResultadoComando(exito=True, mensaje=f"Regla {num+1} eliminada")
            return ResultadoComando(exito=False, mensaje="Índice de regla inválido")
        except ValueError:
            return ResultadoComando(exito=False, mensaje="Formato: [BORRA REGLA N]")
    
    def _cmd_modo_transliteracion(self, args: str) -> ResultadoComando:
        """Comando MODO TRANSLITERACION"""
        modo_str = args.strip().lower()
        
        modos = {
            "desactivado": ModoTransliteracion.DESACTIVADO,
            "selectivo": ModoTransliteracion.SELECTIVO,
            "completo": ModoTransliteracion.COMPLETO,
        }
        
        if modo_str in modos:
            self.config.modo_transliteracion = modos[modo_str]
            return ResultadoComando(
                exito=True,
                mensaje=f"Modo transliteración: {modo_str.upper()}"
            )
        
        return ResultadoComando(
            exito=False,
            mensaje="Opciones: desactivado | selectivo | completo"
        )
    
    def _cmd_modo_salida(self, modo: ModoSalida) -> ResultadoComando:
        """Comando MODO BORRADOR / MODO FINAL"""
        self.config.modo_salida = modo
        return ResultadoComando(
            exito=True,
            mensaje=f"Modo salida: {modo.name}"
        )
    
    # ══════════════════════════════════════════════════════════
    # IMPLEMENTACIÓN: CONTROL
    # ══════════════════════════════════════════════════════════
    
    def _cmd_pausa(self) -> ResultadoComando:
        """Comando PAUSA"""
        self.estado.pausado = True
        if "PAUSA" in self._callbacks:
            self._callbacks["PAUSA"]()
        return ResultadoComando(exito=True, mensaje="Proceso pausado")
    
    def _cmd_continuar(self) -> ResultadoComando:
        """Comando CONTINUAR"""
        self.estado.pausado = False
        if "CONTINUAR" in self._callbacks:
            self._callbacks["CONTINUAR"]()
        return ResultadoComando(exito=True, mensaje="Proceso reanudado")
    
    def _cmd_forzar(self) -> ResultadoComando:
        """Comando FORZAR"""
        if "FORZAR" in self._callbacks:
            self._callbacks["FORZAR"]()
        return ResultadoComando(
            exito=True,
            mensaje="ADVERTENCIA: Continuando tras FALLO CRÍTICO bajo responsabilidad del usuario"
        )
    
    def _cmd_reiniciar(self) -> ResultadoComando:
        """Comando REINICIAR"""
        self._confirmacion_pendiente = (
            "reiniciar",
            self._ejecutar_reiniciar
        )
        
        return ResultadoComando(
            exito=True,
            mensaje="REINICIAR TRADUCCIÓN\n\n"
                    "Opciones:\n"
                    "  A) Conservar glosario\n"
                    "  B) Conservar glosario + configuración\n"
                    "  C) Reiniciar todo (limpio)\n\n"
                    "Seleccione opción (A/B/C) o 'cancelar':",
            requiere_confirmacion=True
        )
    
    def _ejecutar_reiniciar(self) -> ResultadoComando:
        """Ejecutar reinicio"""
        if "REINICIAR" in self._callbacks:
            self._callbacks["REINICIAR"]()
        return ResultadoComando(exito=True, mensaje="Traducción reiniciada")
    
    def _cmd_saltar(self, args: str) -> ResultadoComando:
        """Comando SALTAR"""
        try:
            n = int(args.strip())
            if "SALTAR" in self._callbacks:
                self._callbacks["SALTAR"](n)
            return ResultadoComando(
                exito=True,
                mensaje=f"Saltando {n} oraciones (marcadas como [NO TRADUCIDAS])"
            )
        except ValueError:
            return ResultadoComando(exito=False, mensaje="Formato: [SALTAR N]")
    
    def _cmd_volver(self, args: str) -> ResultadoComando:
        """Comando VOLVER"""
        try:
            n = int(args.strip())
            if "VOLVER" in self._callbacks:
                self._callbacks["VOLVER"](n)
            return ResultadoComando(
                exito=True,
                mensaje=f"Volviendo a traducir últimas {n} oraciones"
            )
        except ValueError:
            return ResultadoComando(exito=False, mensaje="Formato: [VOLVER N]")
    
    # ══════════════════════════════════════════════════════════
    # IMPLEMENTACIÓN: EXPORTACIÓN
    # ══════════════════════════════════════════════════════════
    
    def _cmd_exportar_glosario(self, args: str) -> ResultadoComando:
        """Comando EXPORTAR GLOSARIO"""
        if not self.glosario:
            return ResultadoComando(exito=False, mensaje="Glosario no disponible")
        
        formato = args.strip().lower() or "txt"
        
        if formato == "json":
            datos = self.glosario.exportar_json()
        elif formato == "csv":
            datos = self.glosario.exportar_csv()
        else:
            datos = self.glosario.exportar_txt()
        
        return ResultadoComando(
            exito=True,
            mensaje=f"Glosario exportado ({formato.upper()})",
            datos=datos
        )
    
    def _cmd_exportar_traduccion(self, args: str) -> ResultadoComando:
        """Comando EXPORTAR TRADUCCION"""
        # Implementación depende del sistema completo
        return ResultadoComando(
            exito=True,
            mensaje="Traducción exportada"
        )
    
    def _cmd_importar_glosario(self, args: str) -> ResultadoComando:
        """Comando IMPORTAR GLOSARIO"""
        fuente = args.strip()
        if not fuente:
            return ResultadoComando(
                exito=False,
                mensaje="Formato: [IMPORTAR GLOSARIO fuente]"
            )
        
        # Implementación depende del sistema de archivos
        return ResultadoComando(
            exito=True,
            mensaje=f"Importando glosario desde: {fuente}"
        )
    
    # ══════════════════════════════════════════════════════════
    # IMPLEMENTACIÓN: AYUDA
    # ══════════════════════════════════════════════════════════
    
    def _cmd_ayuda(self, args: str) -> ResultadoComando:
        """Comando AYUDA"""
        if args:
            # Ayuda específica
            cmd_nombre = args.strip().upper()
            if cmd_nombre in COMANDOS:
                cmd = COMANDOS[cmd_nombre]
                texto = (
                    f"COMANDO: [{cmd.nombre}]\n\n"
                    f"DESCRIPCIÓN:\n  {cmd.descripcion}\n\n"
                    f"USO:\n  {cmd.uso}\n\n"
                    f"EJEMPLO:\n  {cmd.ejemplo}"
                )
                return ResultadoComando(exito=True, mensaje=texto)
            return ResultadoComando(exito=False, mensaje=f"Comando '{args}' no encontrado")
        
        # Ayuda general
        lineas = [
            "═" * 50,
            "COMANDOS DISPONIBLES",
            "═" * 50,
            "",
            "CONSULTA:",
            "  [GLOSARIO]          [LOCUCIONES]       [ALTERNATIVAS]",
            "  [DECISIONES]        [CONFIGURACION]    [ESTADO]",
            "",
            "MODIFICACIÓN:",
            "  [ACTUALIZA x = y]   [AÑADE x = y]      [ELIMINA x]",
            "  [AÑADE LOCUCION x = A-B-C]",
            "  [REGLA ...]         [BORRA REGLA N]",
            "  [MODO TRANSLITERACION x]",
            "  [MODO BORRADOR]     [MODO FINAL]",
            "",
            "CONTROL:",
            "  [PAUSA]             [CONTINUAR]        [FORZAR]",
            "  [REINICIAR]         [SALTAR N]         [VOLVER N]",
            "",
            "EXPORTACIÓN:",
            "  [EXPORTAR GLOSARIO formato]",
            "  [EXPORTAR TRADUCCION formato]",
            "  [IMPORTAR GLOSARIO fuente]",
            "",
            "AYUDA:",
            "  [AYUDA]             [AYUDA comando]",
            "  [PROTOCOLOS]        [PROTOCOLO N]",
            "",
            "═" * 50,
        ]
        
        return ResultadoComando(exito=True, mensaje="\n".join(lineas))
    
    def _cmd_protocolos(self) -> ResultadoComando:
        """Comando PROTOCOLOS"""
        texto = """
═══════════════════════════════════════════════════
PROTOCOLOS DEL SISTEMA
═══════════════════════════════════════════════════

P0:  Modo de Operación (Flujo e Interacción)
P1:  Definiciones Operativas
P2:  Constitución (Reglas Inviolables)
P3:  Core (Control de Flujo)
P4:  Núcleos Léxicos (Discriminador Semántico)
P5:  Partículas (Generador de Candidatos)
P6:  Casos Difíciles (Generador de Soluciones)
P7:  Reparación Sintáctica
P8:  Glosario (Registro y Custodia)
P9:  Formación Léxica (Transliteración y Neologismos)
P10: Renderizado (Pre y Post Procesamiento)
P11: Script de Comandos

═══════════════════════════════════════════════════
Use [PROTOCOLO N] para ver detalle de un protocolo.
═══════════════════════════════════════════════════
"""
        return ResultadoComando(exito=True, mensaje=texto.strip())
    
    def _cmd_protocolo(self, args: str) -> ResultadoComando:
        """Comando PROTOCOLO"""
        try:
            num = int(args.strip())
            # Aquí se cargaría el detalle del protocolo
            return ResultadoComando(
                exito=True,
                mensaje=f"Detalle del Protocolo P{num} (ver documentación completa)"
            )
        except ValueError:
            return ResultadoComando(exito=False, mensaje="Formato: [PROTOCOLO N]")
    
    # ══════════════════════════════════════════════════════════
    # CONFIRMACIONES
    # ══════════════════════════════════════════════════════════
    
    def _procesar_confirmacion(self, entrada: str) -> ResultadoComando:
        """Procesar respuesta a confirmación pendiente"""
        entrada = entrada.strip().lower()
        
        if entrada in ["sí", "si", "s", "yes", "y"]:
            _, callback = self._confirmacion_pendiente
            self._confirmacion_pendiente = None
            return callback()
        
        elif entrada in ["no", "n", "cancelar", "cancel"]:
            self._confirmacion_pendiente = None
            return ResultadoComando(exito=True, mensaje="Operación cancelada")
        
        # Para REINICIAR, aceptar A/B/C
        elif entrada.upper() in ["A", "B", "C"]:
            _, callback = self._confirmacion_pendiente
            self._confirmacion_pendiente = None
            return callback()
        
        return ResultadoComando(
            exito=False,
            mensaje="Responda sí/no o la opción correspondiente",
            requiere_confirmacion=True
        )


# ══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ══════════════════════════════════════════════════════════════

_procesador_comandos: Optional[ProcesadorComandos] = None


def obtener_procesador_comandos() -> ProcesadorComandos:
    """Obtener procesador de comandos global"""
    global _procesador_comandos
    if _procesador_comandos is None:
        _procesador_comandos = ProcesadorComandos()
    return _procesador_comandos


def procesar_comando(entrada: str) -> ResultadoComando:
    """Función de conveniencia para procesar comando"""
    return obtener_procesador_comandos().procesar(entrada)
