"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 5/13: Núcleos Léxicos - Discriminador Semántico (P4)
════════════════════════════════════════════════════════════════

TRIGGER: P3.F2 (para cada Slot_N[i] con status ≠ BLOQUEADO)
INPUT:   Slot_N = {token_src, cat_src, morph_src, pos_index, status}
OUTPUT:  Slot_N_Out = {token_src, cat_t, morph_t, pos_index, token_tgt}

PRINCIPIO: Núcleos son INVARIABLES. Una traducción por token, siempre.

JERARQUÍA ETIMOLÓGICA:
  [LENGUA_FUENTE > LATINA > GRIEGA > ÁRABE > TÉCNICA]

REGLA DE PREFERENCIA:
  Si etimología ≠ uso técnico pero metáfora viable → ETIMOLOGÍA.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from constants import (
    TokenStatus, TokenCategoria, CategoriaGramatical,
    Reason, JERARQUIA_ETIMOLOGICA, FalloCritico
)
from models import (
    SlotN, MorfologiaFuente, MorfologiaTarget, ErrorCritico
)
from glossary import Glosario, SinonimiaError


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════

@dataclass
class CandidatoEtimologico:
    """Candidato encontrado en búsqueda etimológica"""
    termino: str
    origen: str  # LENGUA_FUENTE, LATINA, GRIEGA, ARABE, TECNICA
    raiz: str
    derivacion_existe: bool = True
    es_metafora_viable: bool = False
    prioridad: int = 0
    
    def calcular_prioridad(self) -> int:
        """Calcular prioridad según jerarquía etimológica"""
        try:
            self.prioridad = len(JERARQUIA_ETIMOLOGICA) - JERARQUIA_ETIMOLOGICA.index(self.origen)
        except ValueError:
            self.prioridad = 0
        return self.prioridad


@dataclass
class ResultadoNucleo:
    """Resultado del procesamiento de un núcleo"""
    exito: bool
    token_tgt: Optional[str] = None
    morph_tgt: Optional[MorfologiaTarget] = None
    bloqueado: bool = False
    restart: bool = False
    reason: Optional[Reason] = None
    mensaje: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exito": self.exito,
            "token_tgt": self.token_tgt,
            "morph_tgt": self.morph_tgt,
            "bloqueado": self.bloqueado,
            "restart": self.restart,
            "reason": self.reason.name if self.reason else None,
            "mensaje": self.mensaje
        }


# ══════════════════════════════════════════════════════════════
# BASE DE DATOS ETIMOLÓGICA (Simulada)
# ══════════════════════════════════════════════════════════════

class BaseEtimologica:
    """
    Base de datos etimológica simplificada
    En producción, esto sería una base de datos real
    """
    
    def __init__(self):
        # Diccionario de raíces conocidas
        # Formato: token_src -> [(termino_es, origen, raiz, derivacion_existe)]
        self._raices: Dict[str, List[Tuple[str, str, str, bool]]] = {
            # Ejemplos árabes
            "ʿaql": [
                ("intelecto", "LATINA", "intellec-", True),
                ("razón", "LATINA", "ration-", True),
                ("ligadura", "LATINA", "ligatur-", True),  # Etimológico: "atar"
            ],
            "nafs": [
                ("alma", "LATINA", "anim-", True),
                ("espíritu", "LATINA", "spirit-", True),
                ("psique", "GRIEGA", "psych-", True),
            ],
            "ʿayn": [
                ("ojo", "LATINA", "ocul-", True),
                ("esencia", "LATINA", "essent-", True),
                ("fuente", "LATINA", "font-", True),
            ],
            "kalima": [
                ("palabra", "LATINA", "parabola-", True),
                ("verbo", "LATINA", "verb-", True),
            ],
            "wujūd": [
                ("existencia", "LATINA", "existent-", True),
                ("ser", "LATINA", "ess-", True),
            ],
            "maʿqūl": [
                ("inteligido", "LATINA", "intellec-", False),  # Derivación no existe
                ("intelectado", "LATINA", "intellec-", False),
            ],
            "ḥaqq": [
                ("verdad", "LATINA", "verit-", True),
                ("derecho", "LATINA", "direct-", True),
                ("real", "LATINA", "real-", True),
            ],
        }
        
        # Términos que permiten lectura metafórica
        self._metaforas_viables: Dict[str, List[str]] = {
            "ʿaql": ["ligadura", "sujeción"],  # "lo que ata/sujeta"
            "ʿayn": ["esencia", "fuente"],     # "ojo" como esencia
        }
    
    def buscar_raices(self, token_src: str) -> List[CandidatoEtimologico]:
        """Buscar raíces etimológicas para un token"""
        candidatos = []
        
        datos = self._raices.get(token_src.lower(), [])
        
        for termino, origen, raiz, deriv_existe in datos:
            cand = CandidatoEtimologico(
                termino=termino,
                origen=origen,
                raiz=raiz,
                derivacion_existe=deriv_existe,
                es_metafora_viable=self._es_metafora_viable(token_src, termino)
            )
            cand.calcular_prioridad()
            candidatos.append(cand)
        
        # Ordenar por prioridad (mayor primero)
        candidatos.sort(key=lambda c: c.prioridad, reverse=True)
        
        return candidatos
    
    def _es_metafora_viable(self, token_src: str, termino: str) -> bool:
        """Verificar si el término permite lectura metafórica"""
        metaforas = self._metaforas_viables.get(token_src.lower(), [])
        return termino.lower() in [m.lower() for m in metaforas]
    
    def obtener_raiz(self, token_src: str) -> Optional[str]:
        """Obtener raíz principal de un token"""
        datos = self._raices.get(token_src.lower(), [])
        if datos:
            return datos[0][2]  # Primera raíz
        return None


# Instancia global
_base_etimologica = BaseEtimologica()


def obtener_base_etimologica() -> BaseEtimologica:
    """Obtener base etimológica global"""
    return _base_etimologica


# ══════════════════════════════════════════════════════════════
# PROCESADOR DE NÚCLEOS (P4)
# ══════════════════════════════════════════════════════════════

class ProcesadorNucleos:
    """
    P4: Núcleos Léxicos - Discriminador Semántico
    
    Flujo:
      F1. Verificación de bloqueo
      F2. Cache check
      F3. Búsqueda de lexemas
      F4. Selección
      F5. Morfología adaptativa
      F6. Verificación de paridad
      F7. Salida
    """
    
    def __init__(self, base_etim: BaseEtimologica = None):
        self.base_etim = base_etim or obtener_base_etimologica()
        self._procesador_casos_dificiles = None  # P6
    
    def set_procesador_casos_dificiles(self, procesador) -> None:
        """Inyectar procesador de casos difíciles (P6)"""
        self._procesador_casos_dificiles = procesador
    
    def procesar(self, slot_n: SlotN, glosario: Glosario) -> Dict[str, Any]:
        """
        Procesar un núcleo léxico
        
        Args:
            slot_n: Slot del núcleo a procesar
            glosario: Glosario del sistema
        
        Returns:
            Diccionario con resultado del procesamiento
        """
        resultado = ResultadoNucleo(exito=False)
        
        try:
            # F1. Verificación de bloqueo
            if self._f1_verificar_bloqueo(slot_n, glosario):
                resultado.bloqueado = True
                resultado.exito = True
                resultado.mensaje = "Token bloqueado - parte de locución"
                return resultado.to_dict()
            
            # F2. Cache check
            n_base = self._f2_cache_check(slot_n, glosario)
            
            if n_base is None:
                # F3. Búsqueda de lexemas
                candidatos = self._f3_busqueda_lexemas(slot_n)
                
                # F4. Selección
                n_base, reason = self._f4_seleccion(slot_n, candidatos, glosario)
                
                if reason:
                    resultado.reason = reason
                    resultado.restart = True
            
            # F5. Morfología adaptativa
            n_flexionado, morph_tgt = self._f5_morfologia(n_base, slot_n.morph_src)
            
            # F6. Verificación de paridad
            self._f6_verificar_paridad(slot_n, n_base, glosario)
            
            # F7. Salida
            self._f7_salida(slot_n, n_base, glosario, resultado.reason)
            
            # Asignar al slot
            slot_n.token_tgt = n_flexionado
            slot_n.morph_tgt = morph_tgt
            slot_n.status = TokenStatus.ASIGNADO
            
            resultado.exito = True
            resultado.token_tgt = n_flexionado
            resultado.morph_tgt = morph_tgt
            
        except SinonimiaError as e:
            resultado.exito = False
            resultado.mensaje = f"FALLO CRÍTICO: Sinonimia - {str(e)}"
        
        except Exception as e:
            resultado.exito = False
            resultado.mensaje = f"Error: {str(e)}"
        
        return resultado.to_dict()
    
    # ══════════════════════════════════════════════════════════
    # F1. VERIFICACIÓN DE BLOQUEO
    # ══════════════════════════════════════════════════════════
    
    def _f1_verificar_bloqueo(self, slot_n: SlotN, glosario: Glosario) -> bool:
        """
        F1. Verificación de bloqueo (P4.F1)
        
        Si token está BLOQUEADO → parte de locución, no traducir individualmente
        """
        if slot_n.status == TokenStatus.BLOQUEADO:
            return True
        
        # Verificar también en glosario
        loc_id = glosario.fase_b_verificar_bloqueo(slot_n.token_src, slot_n.pos_index)
        if loc_id:
            slot_n.bloquear(loc_id)
            return True
        
        return False
    
    # ══════════════════════════════════════════════════════════
    # F2. CACHE CHECK
    # ══════════════════════════════════════════════════════════
    
    def _f2_cache_check(self, slot_n: SlotN, glosario: Glosario) -> Optional[str]:
        """
        F2. Cache check (P4.F2)
        
        Si token ya está en glosario con traducción asignada → usar esa
        """
        entrada = glosario.obtener_entrada(slot_n.token_src)
        
        if entrada and entrada.status == TokenStatus.ASIGNADO:
            return entrada.token_tgt
        
        return None
    
    # ══════════════════════════════════════════════════════════
    # F3. BÚSQUEDA DE LEXEMAS
    # ══════════════════════════════════════════════════════════
    
    def _f3_busqueda_lexemas(self, slot_n: SlotN) -> List[CandidatoEtimologico]:
        """
        F3. Búsqueda de lexemas (P4.F3)
        
        Buscar raíces etimológicas y ordenar según jerarquía
        """
        candidatos = self.base_etim.buscar_raices(slot_n.token_src)
        
        # Ya vienen ordenados por prioridad desde la base
        return candidatos
    
    # ══════════════════════════════════════════════════════════
    # F4. SELECCIÓN
    # ══════════════════════════════════════════════════════════
    
    def _f4_seleccion(self, slot_n: SlotN, candidatos: List[CandidatoEtimologico],
                      glosario: Glosario) -> Tuple[str, Optional[Reason]]:
        """
        F4. Selección (P4.F4)
        
        Seleccionar traducción según número de candidatos y reglas
        """
        count = len(candidatos)
        
        # CASE: Sin candidatos (NO_ROOT)
        if count == 0:
            return self._manejar_caso_dificil(slot_n, Reason.NO_ROOT, glosario)
        
        # CASE: Múltiples candidatos (posible COLLISION)
        if count > 1:
            # Aplicar regla de preferencia etimológica
            # Si el primero es etimológico y permite metáfora → preferir
            primer_cand = candidatos[0]
            
            if primer_cand.es_metafora_viable:
                # Preferir etimología sobre uso técnico
                return primer_cand.termino, None
            
            # Si no hay metáfora clara → posible COLLISION
            return self._manejar_caso_dificil(
                slot_n, Reason.COLLISION, glosario, candidatos
            )
        
        # CASE: Candidato único
        cand = candidatos[0]
        
        # Verificar si derivación existe
        if not cand.derivacion_existe:
            return self._manejar_caso_dificil(slot_n, Reason.GAP_DERIVATION, glosario)
        
        return cand.termino, None
    
    def _manejar_caso_dificil(self, slot_n: SlotN, reason: Reason,
                              glosario: Glosario,
                              candidatos: List[CandidatoEtimologico] = None) -> Tuple[str, Reason]:
        """Delegar a P6 para casos difíciles"""
        if self._procesador_casos_dificiles:
            resultado = self._procesador_casos_dificiles.procesar(
                slot_n, reason, glosario, candidatos
            )
            return resultado.get("n_base", slot_n.token_src), reason
        
        # Fallback si no hay P6 configurado
        if reason == Reason.NO_ROOT:
            # Transliterar
            return slot_n.token_src + "-ado", reason
        elif reason == Reason.GAP_DERIVATION:
            # Usar raíz con sufijo forzado
            raiz = self.base_etim.obtener_raiz(slot_n.token_src)
            if raiz:
                return raiz.rstrip("-") + "ado", reason
            return slot_n.token_src + "-ado", reason
        elif reason == Reason.COLLISION:
            # Usar primer candidato
            if candidatos:
                return candidatos[0].termino, reason
            return slot_n.token_src, reason
        
        return slot_n.token_src, reason
    
    # ══════════════════════════════════════════════════════════
    # F5. MORFOLOGÍA ADAPTATIVA
    # ══════════════════════════════════════════════════════════
    
    def _f5_morfologia(self, n_base: str, morph_src: MorfologiaFuente) -> Tuple[str, MorfologiaTarget]:
        """
        F5. Morfología adaptativa (P4.F5)
        
        Aplicar: número, persona, tiempo, voz
        Ignorar: caso gramatical
        Género: heredar del español o adaptar
        """
        morph_tgt = MorfologiaTarget()
        n_flexionado = n_base
        
        # NÚMERO
        if morph_src.numero == "singular":
            morph_tgt.numero = "singular"
        elif morph_src.numero == "dual":
            # Dual → "ambos" o "los dos" o plural
            morph_tgt.numero = "plural"  # Simplificado
            n_flexionado = self._pluralizar(n_base)
        elif morph_src.numero == "plural":
            morph_tgt.numero = "plural"
            n_flexionado = self._pluralizar(n_base)
        
        # GÉNERO
        if morph_src.genero:
            morph_tgt.genero = self._adaptar_genero(n_base, morph_src.genero)
        else:
            morph_tgt.genero = self._inferir_genero(n_base)
        
        # PERSONA (verbos)
        if morph_src.persona:
            morph_tgt.persona = morph_src.persona
            n_flexionado = self._conjugar_persona(n_flexionado, morph_src.persona)
        
        # TIEMPO (verbos)
        if morph_src.tiempo:
            morph_tgt.tiempo = morph_src.tiempo
            n_flexionado = self._conjugar_tiempo(n_flexionado, morph_src.tiempo)
        
        # VOZ (verbos)
        if morph_src.voz:
            morph_tgt.voz = morph_src.voz
        
        return n_flexionado, morph_tgt
    
    def _pluralizar(self, termino: str) -> str:
        """Pluralizar un término en español"""
        if termino.endswith(("a", "e", "i", "o", "u")):
            return termino + "s"
        elif termino.endswith(("s", "x", "z")):
            return termino + "es" if termino.endswith("z") else termino
        else:
            return termino + "es"
    
    def _adaptar_genero(self, termino: str, genero_src: str) -> str:
        """Adaptar género según el español"""
        # Simplificado - en producción se usaría diccionario
        if termino.endswith("a"):
            return "femenino"
        elif termino.endswith("o"):
            return "masculino"
        return "masculino"  # Default
    
    def _inferir_genero(self, termino: str) -> str:
        """Inferir género del término en español"""
        if termino.endswith("a") and not termino.endswith(("ma", "ta")):
            return "femenino"
        elif termino.endswith(("ción", "sión", "dad", "tad", "tud")):
            return "femenino"
        return "masculino"
    
    def _conjugar_persona(self, termino: str, persona: int) -> str:
        """Conjugar verbo según persona (simplificado)"""
        # Esto requeriría un conjugador completo
        return termino
    
    def _conjugar_tiempo(self, termino: str, tiempo: str) -> str:
        """Conjugar verbo según tiempo (simplificado)"""
        return termino
    
    # ══════════════════════════════════════════════════════════
    # F6. VERIFICACIÓN DE PARIDAD
    # ══════════════════════════════════════════════════════════
    
    def _f6_verificar_paridad(self, slot_n: SlotN, n_base: str, glosario: Glosario) -> None:
        """
        F6. Verificación de paridad (P4.F6)
        
        Verificar mapeo 1:1 - si ya está mapeado a OTRO token_tgt → FALLO CRÍTICO
        """
        # Esto se delega al glosario que lanza SinonimiaError si hay conflicto
        glosario.fase_b_verificar_sinonimia(slot_n.token_src, n_base)
    
    # ══════════════════════════════════════════════════════════
    # F7. SALIDA
    # ══════════════════════════════════════════════════════════
    
    def _f7_salida(self, slot_n: SlotN, n_base: str, glosario: Glosario,
                   reason: Optional[Reason] = None) -> None:
        """
        F7. Salida (P4.F7)
        
        Registrar en glosario y preparar salida
        """
        # Calcular margen
        if reason:
            margen = self._calcular_margen(reason)
            etiqueta = reason.name
        else:
            margen = 1  # Mapeo directo
            etiqueta = None
        
        # Registrar en glosario
        glosario.fase_b_asignar(
            slot_n.token_src,
            n_base,
            margen=margen,
            etiqueta=etiqueta
        )
    
    def _calcular_margen(self, reason: Reason) -> int:
        """Calcular margen de decisión según razón"""
        margenes = {
            Reason.IDIOM: 6,
            Reason.COLLISION: 5,
            Reason.NO_ROOT: 4,
            Reason.GAP_DERIVATION: 4,
        }
        return margenes.get(reason, 1)


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA
# ══════════════════════════════════════════════════════════════

def crear_slot_n(token_src: str, cat_src: CategoriaGramatical,
                 pos_index: int, morph: MorfologiaFuente = None) -> SlotN:
    """Crear un SlotN con valores por defecto"""
    return SlotN(
        token_src=token_src,
        cat_src=cat_src,
        morph_src=morph or MorfologiaFuente(),
        pos_index=pos_index,
        status=TokenStatus.PENDIENTE
    )


def es_metafora_viable(token_src: str, contexto: str = None) -> bool:
    """
    Verificar si un token permite lectura metafórica en el contexto
    
    Implementación de la regla:
    Si etimología ≠ uso técnico pero metáfora viable → ETIMOLOGÍA
    """
    base = obtener_base_etimologica()
    candidatos = base.buscar_raices(token_src)
    
    return any(c.es_metafora_viable for c in candidatos)
