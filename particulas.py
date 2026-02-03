

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

# particulas.py
from typing import Dict, List, Optional, Any
from constants import TokenStatus, FuncRole
from models import SlotP, MatrizFuente
from glossary import Glosario
from ai_client import ai_engine # Importante para la conexión con Gemini

class CandidatoParticula:
    """Candidato para traducción de partícula"""
    def __init__(self, termino, origen, func_role, cierra_regimen, prioridad):
        self.termino = termino
        self.origen = origen
        self.func_role = func_role
        self.cierra_regimen = cierra_regimen
        self.prioridad = prioridad
    
    def __lt__(self, other):
        return self.prioridad > other.prioridad

class BaseParticulas:
    """
    Base de datos de partículas con integración de Gemini (P5)
    """
    def __init__(self):
        # 1. Memoria Local (Caché + Datos Predefinidos)
        self._particulas: Dict[str, Dict[FuncRole, List[tuple]]] = {
            "bi": {
                FuncRole.REGIMEN: [("por", True, True), ("con", False, True)],
                FuncRole.MARCA_CASUAL: [("por", True, True)]
            },
            "li": {
                FuncRole.REGIMEN: [("para", True, True), ("a", False, True)],
                FuncRole.DETERMINACION: [("el", False, True)]
            },
            # ... puedes mantener el resto de tus ejemplos del Bloque 6 aquí ...
        }
        
        self._regimenes: Dict[str, List[str]] = {
            "hablar": ["de", "sobre", "con"],
            "pensar": ["en", "sobre"],
            "consistir": ["en"],
            "depender": ["de"],
            "pertenecer": ["a"],
        }

    def buscar_etimologicos(self, token_src: str, func_role: FuncRole) -> List[CandidatoParticula]:
        token_key = token_src.lower()
        
        # PASO 1: Si NO está en la memoria local, preguntamos a Gemini
        if token_key not in self._particulas or func_role not in self._particulas[token_key]:
            print(f"[IA] Consultando partícula: {token_src} ({func_role.name})...")
            datos_ia = ai_engine.consultar_particula(token_src, func_role.name)
            
            # PASO 2: Guardamos la respuesta en la memoria (Caché)
            if token_key not in self._particulas:
                self._particulas[token_key] = {}
            
            lista_tuplas = []
            for item in datos_ia:
                lista_tuplas.append(
                    (item['termino'], item['es_etimologico'], item['cierra_regimen'])
                )
            self._particulas[token_key][func_role] = lista_tuplas

        # PASO 3: Generamos los objetos CandidatoParticula desde la memoria
        candidatos = []
        datos_funcion = self._particulas[token_key].get(func_role, [])
        
        for termino, es_etim, cierra in datos_funcion:
            if es_etim and cierra:
                cand = CandidatoParticula(
                    termino=termino,
                    origen="ETIMOLOGICO",
                    func_role=func_role,
                    cierra_regimen=cierra,
                    prioridad=10 
                )
                candidatos.append(cand)
        
        return candidatos

    def buscar_funcionales(self, token_src: str, func_role: FuncRole) -> List[CandidatoParticula]:
        """Busca candidatos funcionales (mismo proceso de caché que el anterior)"""
        token_key = token_src.lower()
        candidatos = []
        
        # El proceso de consulta a IA ya se hizo en buscar_etimologicos si era necesario
        datos_funcion = self._particulas.get(token_key, {}).get(func_role, [])
        
        for termino, es_etim, cierra in datos_funcion:
            if cierra:
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
        return self._regimenes.get(nucleo.lower(), [])

# Instancia global y funciones de ayuda
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
