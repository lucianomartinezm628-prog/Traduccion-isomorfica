"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 6/13: Partículas - Generador de Candidatos (P5)
════════════════════════════════════════════════════════════════

TRIGGER: P3.F4 (para cada Slot_P[i] con status ≠ BLOQUEADO)
INPUT:   Slot_P[i] + Contexto
OUTPUT:  Cand[] (lista priorizada) | [BLOQUEADO]

PRINCIPIO: Partículas son POLIVALENTES. Pueden variar según función sintáctica.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from constants import (
    TokenStatus, TokenCategoria, CategoriaGramatical,
    FuncRole, JERARQUIA_ETIMOLOGICA
)
from models import SlotP, MatrizFuente
from glossary import Glosario


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════

@dataclass
class CandidatoParticula:
    """Candidato para traducción de partícula"""
    termino: str
    origen: str  # ETIMOLOGICO o FUNCIONAL
    func_role: FuncRole
    cierra_regimen: bool = True
    prioridad: int = 0
    
    def __lt__(self, other):
        return self.prioridad > other.prioridad  # Mayor prioridad primero


@dataclass
class ResultadoParticula:
    """Resultado del procesamiento de una partícula"""
    candidatos: List[str]
    bloqueado: bool = False
    polivalencia: bool = False
    mensaje: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidatos": self.candidatos,
            "bloqueado": self.bloqueado,
            "polivalencia": self.polivalencia,
            "mensaje": self.mensaje
        }


# ══════════════════════════════════════════════════════════════
# BASE DE DATOS DE PARTÍCULAS
# ══════════════════════════════════════════════════════════════

class BaseParticulas:
    """
    Base de datos de partículas y sus equivalentes
    Incluye información etimológica y funcional
    """
    
    def __init__(self):
        # Partículas por token fuente
        # Formato: token_src -> {func_role: [(termino_es, es_etimologico, cierra_regimen)]}
        self._particulas: Dict[str, Dict[FuncRole, List[tuple]]] = {
            # Preposiciones árabes
            "bi": {
                FuncRole.REGIMEN: [
                    ("por", True, True),
                    ("con", False, True),
                    ("en", False, True),
                ],
                FuncRole.MARCA_CASUAL: [
                    ("por", True, True),
                    ("mediante", False, True),
                ],
            },
            "li": {
                FuncRole.REGIMEN: [
                    ("para", True, True),
                    ("a", False, True),
                ],
                FuncRole.DETERMINACION: [
                    ("el", False, True),  # Artículo definido
                ],
            },
            "fi": {
                FuncRole.REGIMEN: [
                    ("en", True, True),
                    ("dentro de", False, True),
                ],
                FuncRole.ADVERBIAL: [
                    ("en", True, True),
                ],
            },
            "min": {
                FuncRole.REGIMEN: [
                    ("de", True, True),
                    ("desde", False, True),
                ],
                FuncRole.MARCA_CASUAL: [
                    ("de", True, True),
                    ("entre", False, True),
                ],
            },
            "ʿan": {
                FuncRole.REGIMEN: [
                    ("sobre", True, True),
                    ("acerca de", False, True),
                    ("de", False, True),
                ],
            },
            "ʿalā": {
                FuncRole.REGIMEN: [
                    ("sobre", True, True),
                    ("en", False, True),
                ],
                FuncRole.ADVERBIAL: [
                    ("sobre", True, True),
                ],
            },
            "ilā": {
                FuncRole.REGIMEN: [
                    ("hacia", True, True),
                    ("a", False, True),
                    ("hasta", False, True),
                ],
            },
            # Conjunciones
            "wa": {
                FuncRole.NEXO_LOGICO: [
                    ("y", True, True),
                    ("e", False, True),
                ],
            },
            "aw": {
                FuncRole.NEXO_LOGICO: [
                    ("o", True, True),
                    ("u", False, True),
                ],
            },
            "fa": {
                FuncRole.NEXO_LOGICO: [
                    ("y", False, True),
                    ("pues", True, True),
                    ("entonces", False, True),
                ],
            },
            "inna": {
                FuncRole.COPULA: [
                    ("ciertamente", True, True),
                    ("en verdad", False, True),
                ],
            },
            "anna": {
                FuncRole.NEXO_LOGICO: [
                    ("que", True, True),
                ],
            },
            # Pronombres/Sufijos
            "huwa": {
                FuncRole.COPULA: [
                    ("él", True, True),
                    ("ello", False, True),
                ],
            },
            "hiya": {
                FuncRole.COPULA: [
                    ("ella", True, True),
                ],
            },
            # Artículo
            "al": {
                FuncRole.DETERMINACION: [
                    ("el", True, True),
                    ("la", False, True),
                    ("lo", False, True),
                ],
            },
            # Relativos
            "alladhī": {
                FuncRole.RELATIVO: [
                    ("que", True, True),
                    ("el cual", False, True),
                    ("quien", False, True),
                ],
            },
            "allatī": {
                FuncRole.RELATIVO: [
                    ("que", True, True),
                    ("la cual", False, True),
                    ("quien", False, True),
                ],
            },
        }
        
        # Requisitos de régimen por núcleo (simplificado)
        self._regimenes: Dict[str, List[str]] = {
            "hablar": ["de", "sobre", "con"],
            "pensar": ["en", "sobre"],
            "consistir": ["en"],
            "depender": ["de"],
            "pertenecer": ["a"],
        }
    
    def buscar_etimologicos(self, token_src: str, func_role: FuncRole) -> List[CandidatoParticula]:
        """Buscar candidatos etimológicos que cierran régimen"""
        candidatos = []
        
        datos_token = self._particulas.get(token_src.lower(), {})
        datos_funcion = datos_token.get(func_role, [])
        
        for termino, es_etim, cierra in datos_funcion:
            if es_etim and cierra:
                cand = CandidatoParticula(
                    termino=termino,
                    origen="ETIMOLOGICO",
                    func_role=func_role,
                    cierra_regimen=cierra,
                    prioridad=10  # Alta prioridad
                )
                candidatos.append(cand)
        
        return candidatos
    
    def buscar_funcionales(self, token_src: str, func_role: FuncRole) -> List[CandidatoParticula]:
        """Buscar candidatos funcionales que cierran régimen"""
        candidatos = []
        
        datos_token = self._particulas.get(token_src.lower(), {})
        datos_funcion = datos_token.get(func_role, [])
        
        for termino, es_etim, cierra in datos_funcion:
            if cierra:  # Incluir todos los que cierran
                cand = CandidatoParticula(
                    termino=termino,
                    origen="ETIMOLOGICO" if es_etim else "FUNCIONAL",
                    func_role=func_role,
                    cierra_regimen=cierra,
                    prioridad=10 if es_etim else 5
                )
                candidatos.append(cand)
        
        return candidatos
    
    def obtener_regimen_nucleo(self, nucleo: str) -> List[str]:
        """Obtener preposiciones que cierra el régimen de un núcleo"""
        return self._regimenes.get(nucleo.lower(), [])


# Instancia global
_base_particulas = BaseParticulas()


def obtener_base_particulas() -> BaseParticulas:
    return _base_particulas


# ══════════════════════════════════════════════════════════════
# PROCESADOR DE PARTÍCULAS (P5)
# ══════════════════════════════════════════════════════════════

class ProcesadorParticulas:
    """
    P5: Partículas - Generador de Candidatos
    
    Flujo:
      F1. Verificación de bloqueo
      F2. Recepción
      F3. Análisis relacional
      F4. Generación de conjuntos
      F5. Construcción de lista
      F6. Salida
    """
    
    def __init__(self, base_part: BaseParticulas = None):
        self.base_part = base_part or obtener_base_particulas()
    
    def procesar(self, slot_p: SlotP, mtx_s: MatrizFuente,
                 glosario: Glosario) -> Dict[str, Any]:
        """
        Procesar una partícula
        
        Args:
            slot_p: Slot de la partícula
            mtx_s: Matriz fuente completa (contexto)
            glosario: Glosario del sistema
        
        Returns:
            Diccionario con candidatos o indicador de bloqueo
        """
        resultado = ResultadoParticula(candidatos=[])
        
        # F1. Verificación de bloqueo
        if self._f1_verificar_bloqueo(slot_p, glosario):
            resultado.bloqueado = True
            resultado.mensaje = "Token bloqueado - parte de locución"
            return resultado.to_dict()
        
        # F2. Recepción
        datos = self._f2_recepcion(slot_p, mtx_s)
        
        # F3. Análisis relacional
        func_role, requisito = self._f3_analisis_relacional(slot_p, datos)
        
        # F4. Generación de conjuntos
        set_a, set_b = self._f4_generar_conjuntos(slot_p, func_role, requisito)
        
        # F5. Construcción de lista
        candidatos = self._f5_construir_lista(set_a, set_b)
        
        # F6. Salida
        resultado.candidatos = candidatos
        resultado.polivalencia = len(set_a) == 0 and len(candidatos) > 0
        
        if resultado.polivalencia:
            resultado.mensaje = "Polivalencia funcional activa"
        
        return resultado.to_dict()
    
    # ══════════════════════════════════════════════════════════
    # F1. VERIFICACIÓN DE BLOQUEO
    # ══════════════════════════════════════════════════════════
    
    def _f1_verificar_bloqueo(self, slot_p: SlotP, glosario: Glosario) -> bool:
        """F1. Verificación de bloqueo"""
        if slot_p.status == TokenStatus.BLOQUEADO:
            return True
        
        loc_id = glosario.fase_b_verificar_bloqueo(slot_p.token_src, slot_p.pos_index)
        if loc_id:
            slot_p.bloquear(loc_id)
            return True
        
        return False
    
    # ══════════════════════════════════════════════════════════
    # F2. RECEPCIÓN
    # ══════════════════════════════════════════════════════════
    
    def _f2_recepcion(self, slot_p: SlotP, mtx_s: MatrizFuente) -> Dict[str, Any]:
        """F2. Recepción de datos de entrada"""
        datos = {
            "token_src": slot_p.token_src,
            "cat_src": slot_p.cat_src,
            "pos_index": slot_p.pos_index,
            "nucleo_izq": None,
            "nucleo_der": None,
            "contexto": mtx_s
        }
        
        # Buscar núcleos adyacentes
        pos = slot_p.pos_index
        
        # Núcleo izquierdo
        if pos > 0:
            slot_izq = mtx_s.obtener_slot(pos - 1)
            if slot_izq and hasattr(slot_izq, 'token_tgt'):
                datos["nucleo_izq"] = slot_izq
        
        # Núcleo derecho
        if pos < mtx_s.size() - 1:
            slot_der = mtx_s.obtener_slot(pos + 1)
            if slot_der and hasattr(slot_der, 'token_tgt'):
                datos["nucleo_der"] = slot_der
        
        return datos
    
    # ══════════════════════════════════════════════════════════
    # F3. ANÁLISIS RELACIONAL
    # ══════════════════════════════════════════════════════════
    
    def _f3_analisis_relacional(self, slot_p: SlotP,
                                 datos: Dict[str, Any]) -> tuple:
        """
        F3. Análisis relacional
        
        Determinar func_role y requisito de régimen
        """
        # Usar func_role del slot si está definido
        func_role = slot_p.func_role
        
        if not func_role:
            # Inferir función según contexto
            func_role = self._inferir_funcion(slot_p, datos)
        
        # Determinar requisito de régimen
        requisito = self._determinar_requisito(datos, func_role)
        
        return func_role, requisito
    
    def _inferir_funcion(self, slot_p: SlotP, datos: Dict[str, Any]) -> FuncRole:
        """Inferir función sintáctica de la partícula"""
        token = slot_p.token_src.lower()
        
        # Heurísticas básicas
        if token in ["wa", "aw", "fa"]:
            return FuncRole.NEXO_LOGICO
        elif token in ["al"]:
            return FuncRole.DETERMINACION
        elif token in ["alladhī", "allatī", "man", "mā"]:
            return FuncRole.RELATIVO
        elif token in ["huwa", "hiya", "inna"]:
            return FuncRole.COPULA
        elif token in ["bi", "li", "fi", "min", "ʿan", "ʿalā", "ilā"]:
            return FuncRole.REGIMEN
        
        return FuncRole.REGIMEN  # Default
    
    def _determinar_requisito(self, datos: Dict[str, Any],
                               func_role: FuncRole) -> List[str]:
        """Determinar qué exige el núcleo para cerrar régimen"""
        requisito = []
        
        # Verificar núcleo regente
        nucleo = datos.get("nucleo_izq") or datos.get("nucleo_der")
        
        if nucleo and hasattr(nucleo, 'token_tgt') and nucleo.token_tgt:
            # Buscar régimen del núcleo
            requisito = self.base_part.obtener_regimen_nucleo(nucleo.token_tgt)
        
        return requisito
    
    # ══════════════════════════════════════════════════════════
    # F4. GENERACIÓN DE CONJUNTOS
    # ══════════════════════════════════════════════════════════
    
    def _f4_generar_conjuntos(self, slot_p: SlotP, func_role: FuncRole,
                               requisito: List[str]) -> tuple:
        """
        F4. Generación de conjuntos
        
        SET A: Etimológicos que cierran régimen
        SET B: Funcionales que cierran régimen
        """
        # SET A: Etimológicos
        set_a = self.base_part.buscar_etimologicos(slot_p.token_src, func_role)
        
        # Filtrar por requisito si existe
        if requisito:
            set_a = [c for c in set_a if c.termino in requisito or not requisito]
        
        # SET B: Funcionales
        set_b = self.base_part.buscar_funcionales(slot_p.token_src, func_role)
        
        if requisito:
            set_b = [c for c in set_b if c.termino in requisito or not requisito]
        
        return set_a, set_b
    
    # ══════════════════════════════════════════════════════════
    # F5. CONSTRUCCIÓN DE LISTA
    # ══════════════════════════════════════════════════════════
    
    def _f5_construir_lista(self, set_a: List[CandidatoParticula],
                            set_b: List[CandidatoParticula]) -> List[str]:
        """
        F5. Construcción de lista de candidatos
        
        Orden:
          1. Etimológicos (set_a) ordenados por prioridad
          2. Funcionales (set_b) sin duplicados
        """
        candidatos = []
        vistos = set()
        
        # Ordenar ambos conjuntos
        set_a.sort()
        set_b.sort()
        
        # Agregar etimológicos primero
        for cand in set_a:
            if cand.termino not in vistos:
                candidatos.append(cand.termino)
                vistos.add(cand.termino)
        
        # Agregar funcionales (sin duplicados)
        for cand in set_b:
            if cand.termino not in vistos:
                candidatos.append(cand.termino)
                vistos.add(cand.termino)
        
        return candidatos


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA
# ══════════════════════════════════════════════════════════════

def crear_slot_p(token_src: str, cat_src: CategoriaGramatical,
                 pos_index: int, func_role: FuncRole = None) -> SlotP:
    """Crear un SlotP con valores por defecto"""
    return SlotP(
        token_src=token_src,
        cat_src=cat_src,
        func_role=func_role,
        pos_index=pos_index,
        status=TokenStatus.PENDIENTE
    )
