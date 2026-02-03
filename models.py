"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 2/13: Modelos y Estructuras de Datos
════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from enum import Enum

# Importar desde constants.py
from constants import (
    TokenStatus, TokenCategoria, CategoriaGramatical,
    FuncRole, ConsultaCodigo, FalloCritico, Reason,
    DecisionOrigen, MARGEN_VALORES
)


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE SLOTS (P1.B.1)
# ══════════════════════════════════════════════════════════════

@dataclass
class MorfologiaFuente:
    """Morfología del token fuente"""
    numero: str = "singular"  # singular, dual, plural
    genero: Optional[str] = None
    persona: Optional[int] = None  # 1, 2, 3
    tiempo: Optional[str] = None
    voz: Optional[str] = None
    caso: Optional[str] = None  # Ignorado en español
    estado: Optional[str] = None  # definido, indefinido, constructo


@dataclass
class MorfologiaTarget:
    """Morfología aplicada al target"""
    numero: str = "singular"
    genero: str = "masculino"
    persona: Optional[int] = None
    tiempo: Optional[str] = None
    voz: Optional[str] = None


@dataclass
class SlotN:
    """
    Slot de Núcleo Léxico (P1.B.1)
    Sustantivos, adjetivos, adverbios, verbos
    """
    token_src: str
    cat_src: CategoriaGramatical
    morph_src: MorfologiaFuente
    pos_index: int
    status: TokenStatus = TokenStatus.PENDIENTE
    
    # Campos adicionales tras procesamiento
    token_tgt: Optional[str] = None
    cat_tgt: Optional[CategoriaGramatical] = None
    morph_tgt: Optional[MorfologiaTarget] = None
    locucion_id: Optional[str] = None  # Si pertenece a locución
    
    def es_bloqueado(self) -> bool:
        return self.status == TokenStatus.BLOQUEADO
    
    def es_asignado(self) -> bool:
        return self.status == TokenStatus.ASIGNADO
    
    def bloquear(self, locucion_id: str) -> None:
        self.status = TokenStatus.BLOQUEADO
        self.locucion_id = locucion_id
    
    def asignar(self, token_tgt: str, cat_tgt: CategoriaGramatical = None,
                morph_tgt: MorfologiaTarget = None) -> None:
        self.token_tgt = token_tgt
        self.cat_tgt = cat_tgt or self.cat_src
        self.morph_tgt = morph_tgt
        self.status = TokenStatus.ASIGNADO


@dataclass
class SlotP:
    """
    Slot de Partícula (P1.B.1)
    Preposiciones, conjunciones, pronombres
    """
    token_src: str
    cat_src: CategoriaGramatical
    func_role: Optional[FuncRole]
    pos_index: int
    status: TokenStatus = TokenStatus.PENDIENTE
    
    # Campos adicionales
    token_tgt: Optional[str] = None
    candidatos: List[str] = field(default_factory=list)
    locucion_id: Optional[str] = None
    
    def es_bloqueado(self) -> bool:
        return self.status == TokenStatus.BLOQUEADO
    
    def bloquear(self, locucion_id: str) -> None:
        self.status = TokenStatus.BLOQUEADO
        self.locucion_id = locucion_id
    
    def asignar(self, token_tgt: str) -> None:
        self.token_tgt = token_tgt
        self.status = TokenStatus.ASIGNADO


# ══════════════════════════════════════════════════════════════
# ESTRUCTURA DE LOCUCIÓN (P1.A.5)
# ══════════════════════════════════════════════════════════════

@dataclass
class Locucion:
    """
    Unidad compleja - Locución idiomática (P1.A.5)
    Secuencia fija con sentido no composicional
    """
    id: str
    src: str  # Secuencia fuente completa
    componentes: List[str]  # Tokens individuales
    posiciones: List[int]  # Posiciones en matriz
    
    tgt: Optional[str] = None  # ETYM(A)-ETYM(B)-...
    status: str = "UNIDAD_COMPLEJA"
    
    def generar_traduccion(self, traducciones_etym: Dict[str, str]) -> str:
        """
        Generar traducción formato ETYM(A)-ETYM(B)-ETYM(C)-...
        """
        partes = []
        for comp in self.componentes:
            if comp in traducciones_etym:
                partes.append(traducciones_etym[comp])
            else:
                # Si no hay traducción etimológica, usar el componente
                partes.append(comp)
        
        self.tgt = "-".join(partes)
        return self.tgt
    
    def contiene_posicion(self, pos: int) -> bool:
        return pos in self.posiciones
    
    def primera_posicion(self) -> int:
        return min(self.posiciones) if self.posiciones else -1


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE MATRIZ (P1.B.1)
# ══════════════════════════════════════════════════════════════

@dataclass
class CeldaMatriz:
    """Celda individual de la matriz"""
    pos: int
    token_src: str
    token_tgt: Optional[str] = None
    tipo: str = "normal"  # normal, inyeccion, nulo, absorbido, locucion
    slot: Optional[Any] = None  # SlotN o SlotP
    
    def es_absorbido(self) -> bool:
        return self.tipo == "absorbido"
    
    def es_inyeccion(self) -> bool:
        return self.tipo == "inyeccion"
    
    def es_nulo(self) -> bool:
        return self.tipo == "nulo"


class MatrizFuente:
    """
    Mtx_S - Matriz Fuente (P1.B.1)
    Representación matricial de la oración fuente
    """
    
    def __init__(self):
        self.celdas: List[CeldaMatriz] = []
        self.slots_n: List[SlotN] = []
        self.slots_p: List[SlotP] = []
        self.locuciones: Dict[str, Locucion] = {}
    
    def agregar_celda(self, token: str, pos: int) -> CeldaMatriz:
        celda = CeldaMatriz(pos=pos, token_src=token)
        self.celdas.append(celda)
        return celda
    
    def agregar_slot_n(self, slot: SlotN) -> None:
        self.slots_n.append(slot)
        if slot.pos_index < len(self.celdas):
            self.celdas[slot.pos_index].slot = slot
    
    def agregar_slot_p(self, slot: SlotP) -> None:
        self.slots_p.append(slot)
        if slot.pos_index < len(self.celdas):
            self.celdas[slot.pos_index].slot = slot
    
    def agregar_locucion(self, locucion: Locucion) -> None:
        self.locuciones[locucion.id] = locucion
        # Marcar componentes como bloqueados
        for pos in locucion.posiciones:
            if pos < len(self.celdas):
                slot = self.celdas[pos].slot
                if slot:
                    slot.bloquear(locucion.id)
    
    def size(self) -> int:
        return len(self.celdas)
    
    def obtener_slot(self, pos: int) -> Optional[Any]:
        if 0 <= pos < len(self.celdas):
            return self.celdas[pos].slot
        return None
    
    def obtener_locucion_en_pos(self, pos: int) -> Optional[Locucion]:
        for loc in self.locuciones.values():
            if loc.contiene_posicion(pos):
                return loc
        return None


class MatrizTarget:
    """
    Mtx_T - Matriz Target (P1.B.1)
    Representación matricial de la oración traducida
    Size(Mtx_T) == Size(Mtx_S) - INMUTABLE
    """
    
    def __init__(self, size: int):
        self._size = size
        self.celdas: List[CeldaMatriz] = [
            CeldaMatriz(pos=i, token_src="", token_tgt=None) 
            for i in range(size)
        ]
        self.inyecciones: List[CeldaMatriz] = []  # Inyecciones no cuentan en size
    
    def size(self) -> int:
        return self._size
    
    def asignar(self, pos: int, token_tgt: str, tipo: str = "normal") -> None:
        if 0 <= pos < self._size:
            self.celdas[pos].token_tgt = token_tgt
            self.celdas[pos].tipo = tipo
    
    def marcar_absorbido(self, pos: int) -> None:
        if 0 <= pos < self._size:
            self.celdas[pos].tipo = "absorbido"
            self.celdas[pos].token_tgt = "[ABSORBIDO]"
    
    def marcar_nulo(self, pos: int) -> None:
        if 0 <= pos < self._size:
            self.celdas[pos].tipo = "nulo"
    
    def insertar_inyeccion(self, token: str, pos_referencia: int) -> None:
        """Insertar inyección (no afecta size)"""
        celda = CeldaMatriz(
            pos=pos_referencia,
            token_src="",
            token_tgt=token,
            tipo="inyeccion"
        )
        self.inyecciones.append(celda)
    
    def obtener_token(self, pos: int) -> Optional[str]:
        if 0 <= pos < self._size:
            return self.celdas[pos].token_tgt
        return None
    
    def verificar_isomorfismo(self, mtx_s: MatrizFuente) -> bool:
        """Verificar que posiciones coinciden (ignorando inyecciones)"""
        if self._size != mtx_s.size():
            return False
        
        for i in range(self._size):
            if self.celdas[i].pos != mtx_s.celdas[i].pos:
                return False
        
        return True


# ══════════════════════════════════════════════════════════════
# ENTRADA DE GLOSARIO (P1.B.5)
# ══════════════════════════════════════════════════════════════

@dataclass
class EntradaGlosario:
    """Entrada individual del glosario"""
    token_src: str
    categoria: TokenCategoria
    token_tgt: Optional[str] = None
    status: TokenStatus = TokenStatus.PENDIENTE
    margen: int = 0
    ocurrencias: List[int] = field(default_factory=list)
    
    # Para partículas: funciones por posición
    func_roles: Dict[int, FuncRole] = field(default_factory=dict)
    
    # Etiqueta de origen (NO_ROOT, COLLISION, etc.)
    etiqueta: Optional[str] = None
    
    # Para polisemia en partículas
    traducciones_por_funcion: Dict[FuncRole, str] = field(default_factory=dict)
    
    def es_nucleo(self) -> bool:
        return self.categoria == TokenCategoria.NUCLEO
    
    def es_particula(self) -> bool:
        return self.categoria == TokenCategoria.PARTICULA
    
    def es_locucion(self) -> bool:
        return self.categoria == TokenCategoria.LOCUCION
    
    def asignar_traduccion(self, tgt: str, margen: int = 1, 
                           etiqueta: str = None) -> None:
        self.token_tgt = tgt
        self.status = TokenStatus.ASIGNADO
        self.margen = margen
        self.etiqueta = etiqueta
    
    def calcular_margen(self, origen: str) -> int:
        """Calcular margen según origen"""
        return MARGEN_VALORES.get(origen, 1)


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE CONSULTA Y DECISIÓN (P0)
# ══════════════════════════════════════════════════════════════

@dataclass
class Opcion:
    """Opción para consulta"""
    letra: str
    texto: str
    justificacion: Optional[str] = None


@dataclass
class Consulta:
    """Consulta al usuario (P0.6)"""
    numero: int
    codigo: ConsultaCodigo
    contexto: str
    token_o_frase: str
    opciones: List[Opcion]
    recomendacion: str  # Letra de opción recomendada
    
    def formatear(self) -> str:
        """Formatear consulta para presentación"""
        lineas = [
            "═" * 40,
            f"[CONSULTA {self.numero}: {self.codigo.name}]",
            "CONTEXTO:",
            f"  {self.contexto}",
            f"  Token/Frase: {self.token_o_frase}",
            "OPCIONES:"
        ]
        for op in self.opciones:
            linea = f"  {op.letra}) {op.texto}"
            if op.justificacion:
                linea += f" — {op.justificacion}"
            lineas.append(linea)
        lineas.append(f"RECOMENDACIÓN: {self.recomendacion}")
        lineas.append("═" * 40)
        return "\n".join(lineas)


@dataclass
class Decision:
    """Registro de decisión tomada (P0.12)"""
    consulta_codigo: ConsultaCodigo
    contexto: str
    opciones: List[str]
    decision: str
    origen: DecisionOrigen
    timestamp: datetime = field(default_factory=datetime.now)
    regla_derivada: Optional[str] = None


@dataclass
class ErrorCritico:
    """Error crítico que detiene el proceso"""
    tipo: FalloCritico
    mensaje: str
    contexto: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def formatear(self) -> str:
        lineas = [
            "═" * 40,
            f"[FALLO CRÍTICO: {self.tipo.name}]",
            "",
            self.mensaje,
            "",
            "CONTEXTO:"
        ]
        for k, v in self.contexto.items():
            lineas.append(f"  {k}: {v}")
        lineas.append(""),
        lineas.append("ACCIÓN: DETENER. Requiere intervención del usuario.")
        lineas.append("═" * 40)
        return "\n".join(lineas)


# ══════════════════════════════════════════════════════════════
# ESTADO DEL PROCESO
# ══════════════════════════════════════════════════════════════

@dataclass
class EstadoProceso:
    """Estado actual del proceso de traducción"""
    fase_actual: str = "INICIO"
    oraciones_traducidas: int = 0
    total_oraciones: int = 0
    consultas_pendientes: int = 0
    errores_criticos: int = 0
    glosario_entradas: int = 0
    glosario_asignadas: int = 0
    glosario_pendientes: int = 0
    pausado: bool = False
    
    def progreso_porcentaje(self) -> float:
        if self.total_oraciones == 0:
            return 0.0
        return (self.oraciones_traducidas / self.total_oraciones) * 100
    
    def formatear(self) -> str:
        return f"""
ESTADO DEL PROCESO

Fase actual: {self.fase_actual}
Progreso: {self.progreso_porcentaje():.1f}% ({self.oraciones_traducidas}/{self.total_oraciones})
Consultas pendientes: {self.consultas_pendientes}
Errores críticos: {self.errores_criticos}

Glosario: {self.glosario_entradas} entradas ({self.glosario_asignadas} asignadas, {self.glosario_pendientes} pendientes)
""".strip()
