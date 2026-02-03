"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 11/13: Sistema de Consultas e Interacción (P0)
════════════════════════════════════════════════════════════════

PROPÓSITO:
  1. Gestionar la interacción con el usuario.
  2. Acumular y presentar consultas.
  3. Procesar respuestas del usuario.
  4. Economizar procesamiento: si es difícil, preguntar.

PRINCIPIO FUNDAMENTAL:
  El usuario es la máxima autoridad.
  Ante duda → PREGUNTAR.
  Si no hay respuesta → DECIDIR según mejor criterio.
"""

import re
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from constants import ConsultaCodigo, DecisionOrigen, FalloCritico
from models import Consulta, Opcion, Decision, ErrorCritico


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════

class EstadoConsulta(Enum):
    """Estado de una consulta"""
    PENDIENTE = auto()
    RESPONDIDA = auto()
    INFERIDA = auto()
    TIMEOUT = auto()


@dataclass
class ConsultaExtendida:
    """Consulta con estado y metadata"""
    consulta: Consulta
    estado: EstadoConsulta = EstadoConsulta.PENDIENTE
    respuesta: Optional[str] = None
    timestamp_creacion: datetime = field(default_factory=datetime.now)
    timestamp_respuesta: Optional[datetime] = None
    
    def marcar_respondida(self, respuesta: str) -> None:
        self.respuesta = respuesta
        self.estado = EstadoConsulta.RESPONDIDA
        self.timestamp_respuesta = datetime.now()
    
    def marcar_inferida(self, respuesta: str) -> None:
        self.respuesta = respuesta
        self.estado = EstadoConsulta.INFERIDA
        self.timestamp_respuesta = datetime.now()


@dataclass
class RespuestaUsuario:
    """Respuesta parseada del usuario"""
    decisiones: Dict[int, str]  # {numero_consulta: letra_opcion}
    usar_recomendaciones: bool = False
    instrucciones_adicionales: List[str] = field(default_factory=list)
    pausar: bool = False
    
    @classmethod
    def desde_texto(cls, texto: str) -> 'RespuestaUsuario':
        """Parsear respuesta de texto"""
        texto = texto.strip().lower()
        
        # Caso especial: pausa
        if texto == "pausa":
            return cls(decisiones={}, pausar=True)
        
        # Caso especial: todos-rec
        if texto == "todos-rec":
            return cls(decisiones={}, usar_recomendaciones=True)
        
        # Parsear decisiones individuales
        decisiones = {}
        instrucciones = []
        
        # Separar instrucciones adicionales (después de punto)
        if '.' in texto:
            partes = texto.split('.', 1)
            texto = partes[0]
            if len(partes) > 1:
                instrucciones = [partes[1].strip()]
        
        # Patrones de respuesta: "1a", "1-a", "1 a"
        patron = r'(\d+)\s*[-]?\s*([a-z])'
        matches = re.findall(patron, texto)
        
        for num, letra in matches:
            decisiones[int(num)] = letra.upper()
        
        # Verificar "resto-rec"
        usar_rec = "resto-rec" in texto or "resto rec" in texto
        
        return cls(
            decisiones=decisiones,
            usar_recomendaciones=usar_rec,
            instrucciones_adicionales=instrucciones
        )


# ══════════════════════════════════════════════════════════════
# GESTOR DE CONSULTAS
# ══════════════════════════════════════════════════════════════

class GestorConsultas:
    """
    Gestor principal de consultas al usuario (P0)
    
    Funcionalidades:
      - Crear y acumular consultas
      - Presentar consultas en bloque
      - Procesar respuestas
      - Manejar timeouts y respuestas incompletas
    """
    
    def __init__(self):
        self._consultas: List[ConsultaExtendida] = []
        self._decisiones: List[Decision] = []
        self._contador: int = 0
        self._callback_consulta: Optional[Callable] = None
        self._auto_decidir: bool = True
    
    def set_callback(self, callback: Callable[[str], str]) -> None:
        """
        Establecer callback para obtener respuestas del usuario
        
        El callback recibe el texto de las consultas y retorna la respuesta
        """
        self._callback_consulta = callback
    
    def set_auto_decidir(self, valor: bool) -> None:
        """Configurar si decidir automáticamente sin respuesta"""
        self._auto_decidir = valor
    
    # ══════════════════════════════════════════════════════════
    # CREACIÓN DE CONSULTAS
    # ══════════════════════════════════════════════════════════
    
    def crear_consulta(self, codigo: ConsultaCodigo, contexto: str,
                       token_o_frase: str, opciones: List[Tuple[str, str]],
                       recomendacion: str = "A") -> Consulta:
        """
        Crear una nueva consulta
        
        Args:
            codigo: Código de tipo de consulta
            contexto: Descripción del contexto
            token_o_frase: Token o frase en cuestión
            opciones: Lista de (texto, justificacion)
            recomendacion: Letra de opción recomendada
        """
        self._contador += 1
        
        lista_opciones = []
        for i, (texto, just) in enumerate(opciones):
            letra = chr(65 + i)  # A, B, C, ...
            lista_opciones.append(Opcion(letra, texto, just))
        
        consulta = Consulta(
            numero=self._contador,
            codigo=codigo,
            contexto=contexto,
            token_o_frase=token_o_frase,
            opciones=lista_opciones,
            recomendacion=recomendacion
        )
        
        self._consultas.append(ConsultaExtendida(consulta=consulta))
        
        return consulta
    
    def crear_consulta_collision(self, token: str,
                                  candidatos: List[Tuple[str, str]]) -> Consulta:
        """Crear consulta C2 para colisión"""
        opciones = [(cand, f"Origen: {origen}") for cand, origen in candidatos]
        
        return self.crear_consulta(
            ConsultaCodigo.C2_COLLISION_DUDA,
            f"Múltiples candidatos para traducir '{token}'",
            token,
            opciones,
            "A"
        )
    
    def crear_consulta_locucion(self, posible_loc: str,
                                 posicion: int) -> Consulta:
        """Crear consulta C3 para posible locución"""
        return self.crear_consulta(
            ConsultaCodigo.C3_POSIBLE_LOCUCION,
            f"Patrón detectado en posición {posicion}",
            posible_loc,
            [
                ("Sí, es locución fija", "Traducir como unidad ETYM(A)-ETYM(B)-..."),
                ("No, traducir componentes individualmente", "Cada componente por separado")
            ],
            "A"
        )
    
    def crear_consulta_sinonimia(self, token: str, existente: str,
                                  propuesta: str) -> Consulta:
        """Crear consulta C4 para sinonimia"""
        return self.crear_consulta(
            ConsultaCodigo.C4_SINONIMIA,
            f"Intento de asignar traducción diferente a núcleo",
            token,
            [
                (existente, "Mantener traducción existente"),
                (propuesta, "Usar nueva traducción (requiere retraducir)")
            ],
            "A"
        )
    
    def crear_consulta_elemento_dudoso(self, elemento: str,
                                        opciones_elem: List[str]) -> Consulta:
        """Crear consulta C6 para elemento dudoso"""
        opciones = [(op, "") for op in opciones_elem]
        
        return self.crear_consulta(
            ConsultaCodigo.C6_ELEMENTO_DUDOSO,
            "Elemento ambiguo en procesamiento",
            elemento,
            opciones,
            "A"
        )
    
    # ══════════════════════════════════════════════════════════
    # PRESENTACIÓN DE CONSULTAS
    # ══════════════════════════════════════════════════════════
    
    def hay_pendientes(self) -> bool:
        """Verificar si hay consultas pendientes"""
        return any(c.estado == EstadoConsulta.PENDIENTE for c in self._consultas)
    
    def obtener_pendientes(self) -> List[ConsultaExtendida]:
        """Obtener consultas pendientes"""
        return [c for c in self._consultas if c.estado == EstadoConsulta.PENDIENTE]
    
    def formatear_consulta_individual(self, consulta: Consulta) -> str:
        """Formatear una consulta individual"""
        return consulta.formatear()
    
    def formatear_consultas_bloque(self) -> str:
        """Formatear todas las consultas pendientes en bloque"""
        pendientes = self.obtener_pendientes()
        
        if not pendientes:
            return "No hay consultas pendientes."
        
        lineas = [
            "═" * 50,
            f"[CONSULTAS PENDIENTES: {len(pendientes)} decisiones]",
            "═" * 50,
            ""
        ]
        
        for ce in pendientes:
            c = ce.consulta
            lineas.append(f"[{c.numero}] {c.codigo.name}")
            lineas.append(f"    Contexto: {c.contexto}")
            lineas.append(f"    Token/Frase: {c.token_o_frase}")
            
            opciones_str = "  ".join([f"{o.letra}) {o.texto}" for o in c.opciones])
            lineas.append(f"    Opciones: {opciones_str}")
            lineas.append(f"    Recomendación: {c.recomendacion}")
            lineas.append("")
        
        lineas.append("═" * 50)
        lineas.append("FORMATO DE RESPUESTA: 1a, 2b, 3c, ...")
        lineas.append("  'todos-rec' = aceptar todas las recomendaciones")
        lineas.append("  'pausa' = detener para revisar")
        lineas.append("═" * 50)
        
        return "\n".join(lineas)
    
    # ══════════════════════════════════════════════════════════
    # PROCESAMIENTO DE RESPUESTAS
    # ══════════════════════════════════════════════════════════
    
    def solicitar_respuestas(self) -> Optional[RespuestaUsuario]:
        """
        Solicitar respuestas al usuario
        
        Usa el callback si está configurado
        """
        if not self.hay_pendientes():
            return None
        
        texto_consultas = self.formatear_consultas_bloque()
        
        if self._callback_consulta:
            texto_respuesta = self._callback_consulta(texto_consultas)
            if texto_respuesta:
                return RespuestaUsuario.desde_texto(texto_respuesta)
        
        return None
    
    def procesar_respuesta(self, respuesta: RespuestaUsuario) -> Dict[int, str]:
        """
        Procesar respuesta del usuario
        
        Returns:
            Dict de {numero_consulta: opcion_seleccionada}
        """
        resultado = {}
        pendientes = self.obtener_pendientes()
        
        for ce in pendientes:
            num = ce.consulta.numero
            
            # Verificar si hay decisión explícita
            if num in respuesta.decisiones:
                opcion = respuesta.decisiones[num]
                ce.marcar_respondida(opcion)
                resultado[num] = opcion
                self._registrar_decision(ce, opcion, DecisionOrigen.USUARIO)
            
            # Usar recomendación
            elif respuesta.usar_recomendaciones:
                opcion = ce.consulta.recomendacion
                ce.marcar_respondida(opcion)
                resultado[num] = opcion
                self._registrar_decision(ce, opcion, DecisionOrigen.USUARIO)
        
        # Procesar instrucciones adicionales
        for instruccion in respuesta.instrucciones_adicionales:
            self._procesar_instruccion(instruccion)
        
        return resultado
    
    def aplicar_recomendaciones_pendientes(self) -> Dict[int, str]:
        """Aplicar recomendaciones a todas las consultas pendientes"""
        resultado = {}
        
        for ce in self.obtener_pendientes():
            opcion = ce.consulta.recomendacion
            ce.marcar_inferida(opcion)
            resultado[ce.consulta.numero] = opcion
            self._registrar_decision(ce, opcion, DecisionOrigen.AUTOMATICA)
        
        return resultado
    
    def _registrar_decision(self, ce: ConsultaExtendida, opcion: str,
                            origen: DecisionOrigen) -> None:
        """Registrar decisión en historial"""
        decision = Decision(
            consulta_codigo=ce.consulta.codigo,
            contexto=ce.consulta.contexto,
            opciones=[o.texto for o in ce.consulta.opciones],
            decision=opcion,
            origen=origen
        )
        self._decisiones.append(decision)
    
    def _procesar_instruccion(self, instruccion: str) -> None:
        """Procesar instrucción adicional del usuario"""
        # Parsear instrucciones como reglas
        instruccion = instruccion.strip()
        
        if instruccion.lower().startswith("siempre"):
            # Regla permanente
            pass
        elif instruccion.lower().startswith("nunca"):
            # Regla prohibitiva
            pass
        # etc.
    
    # ══════════════════════════════════════════════════════════
    # MANEJO DE ERRORES CRÍTICOS
    # ══════════════════════════════════════════════════════════
    
    def crear_error_critico(self, tipo: FalloCritico, mensaje: str,
                            contexto: Dict[str, Any]) -> ErrorCritico:
        """Crear error crítico"""
        return ErrorCritico(
            tipo=tipo,
            mensaje=mensaje,
            contexto=contexto
        )
    
    def formatear_error_critico(self, error: ErrorCritico) -> str:
        """Formatear error crítico para presentación"""
        return error.formatear()
    
    # ══════════════════════════════════════════════════════════
    # HISTORIAL
    # ══════════════════════════════════════════════════════════
    
    def obtener_historial(self, filtro: Optional[str] = None) -> List[Decision]:
        """
        Obtener historial de decisiones
        
        Args:
            filtro: "usuario", "auto", o código de consulta (ej: "C2")
        """
        if not filtro:
            return self._decisiones.copy()
        
        filtro = filtro.lower()
        
        if filtro == "usuario":
            return [d for d in self._decisiones if d.origen == DecisionOrigen.USUARIO]
        elif filtro == "auto":
            return [d for d in self._decisiones 
                    if d.origen in (DecisionOrigen.AUTOMATICA, DecisionOrigen.INFERIDA)]
        elif filtro.upper().startswith("C"):
            try:
                codigo = ConsultaCodigo[f"{filtro.upper()}_" if not "_" in filtro else filtro.upper()]
                return [d for d in self._decisiones if d.consulta_codigo == codigo]
            except KeyError:
                pass
        
        return self._decisiones.copy()
    
    def formatear_historial(self, filtro: Optional[str] = None) -> str:
        """Formatear historial para presentación"""
        decisiones = self.obtener_historial(filtro)
        
        if not decisiones:
            return "No hay decisiones registradas."
        
        lineas = [
            "═" * 50,
            "HISTORIAL DE DECISIONES",
            "═" * 50,
            ""
        ]
        
        for i, d in enumerate(decisiones, 1):
            lineas.append(f"[{i}] {d.timestamp.strftime('%Y-%m-%d %H:%M')}")
            lineas.append(f"    Tipo: {d.consulta_codigo.name}")
            lineas.append(f"    Contexto: {d.contexto}")
            lineas.append(f"    Decisión: {d.decision}")
            lineas.append(f"    Origen: {d.origen.name}")
            lineas.append("")
        
        lineas.append("═" * 50)
        return "\n".join(lineas)
    
    # ══════════════════════════════════════════════════════════
    # UTILIDADES
    # ══════════════════════════════════════════════════════════
    
    def limpiar_consultas(self) -> None:
        """Limpiar consultas (mantiene historial)"""
        self._consultas = []
    
    def limpiar_todo(self) -> None:
        """Limpiar consultas e historial"""
        self._consultas = []
        self._decisiones = []
        self._contador = 0
    
    def obtener_estadisticas(self) -> Dict[str, int]:
        """Obtener estadísticas de consultas"""
        total = len(self._consultas)
        pendientes = sum(1 for c in self._consultas if c.estado == EstadoConsulta.PENDIENTE)
        respondidas = sum(1 for c in self._consultas if c.estado == EstadoConsulta.RESPONDIDA)
        inferidas = sum(1 for c in self._consultas if c.estado == EstadoConsulta.INFERIDA)
        
        return {
            "total": total,
            "pendientes": pendientes,
            "respondidas": respondidas,
            "inferidas": inferidas,
            "decisiones_historial": len(self._decisiones)
        }


# ══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ══════════════════════════════════════════════════════════════

_gestor_consultas = GestorConsultas()


def obtener_gestor_consultas() -> GestorConsultas:
    """Obtener gestor de consultas global"""
    return _gestor_consultas


def crear_consulta(codigo: ConsultaCodigo, contexto: str,
                   token: str, opciones: List[Tuple[str, str]],
                   recomendacion: str = "A") -> Consulta:
    """Función de conveniencia para crear consulta"""
    return _gestor_consultas.crear_consulta(
        codigo, contexto, token, opciones, recomendacion
    )


def hay_consultas_pendientes() -> bool:
    """Verificar si hay consultas pendientes"""
    return _gestor_consultas.hay_pendientes()


def obtener_consultas_formateadas() -> str:
    """Obtener consultas pendientes formateadas"""
    return _gestor_consultas.formatear_consultas_bloque()
