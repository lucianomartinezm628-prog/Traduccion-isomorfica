"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 5/13: Núcleos Léxicos - Discriminador Semántico (P4)
════════════════════════════════════════════════════════════════
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Importamos constantes básicas. 
# Si JERARQUIA_ETIMOLOGICA da error de importación, la definimos abajo localmente.
from constants import (
    TokenStatus, TokenCategoria, CategoriaGramatical,
    Reason, FalloCritico
)
try:
    from constants import JERARQUIA_ETIMOLOGICA
except ImportError:
    # Definición de respaldo si no está en constants.py
    JERARQUIA_ETIMOLOGICA = ["LENGUA_FUENTE", "LATINA", "GRIEGA", "ARABE", "TECNICA"]

from models import (
    SlotN, MorfologiaFuente, MorfologiaTarget, ErrorCritico
)
from glossary import Glosario, SinonimiaError
from ai_client import ai_engine 

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
            # Mientras menor índice en la lista, mayor prioridad
            # Invertimos el valor para que sea un score positivo
            idx = JERARQUIA_ETIMOLOGICA.index(self.origen)
            self.prioridad = (len(JERARQUIA_ETIMOLOGICA) - idx) * 10
        except ValueError:
            self.prioridad = 0
        
        # Bonificadores
        if self.es_metafora_viable:
            self.prioridad += 5
        if self.derivacion_existe:
            self.prioridad += 2
            
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
# BASE DE DATOS ETIMOLÓGICA (Simulada + IA)
# ══════════════════════════════════════════════════════════════

class BaseEtimologica:
    def __init__(self):
        # Tu diccionario inicial actúa como CACHÉ (Memoria rápida)
        self._raices: Dict[str, List[Tuple[str, str, str, bool]]] = {
            "kitāb": [("escritura", "LATINA", "script-", True)],
            "ʿaql": [("intelecto", "LATINA", "intelec-", True), ("ligadura", "LATINA", "lig-", True)],
        }
        self._metaforas_viables: Dict[str, List[str]] = {
            "ʿaql": ["ligadura"]
        }

    def _es_metafora_viable(self, token: str, termino: str) -> bool:
        """Verifica si un término es metáfora viable para el token dado"""
        token_key = token.lower()
        if token_key in self._metaforas_viables:
            return termino in self._metaforas_viables[token_key]
        return False

    def buscar_raices(self, token_src: str, contexto: str = "") -> List[CandidatoEtimologico]:
        """Buscar raíces. Si no existen, PREGUNTAR A GEMINI."""
        
        token_key = token_src.lower()

        # 1. Intentar buscar en Caché local (rápido y gratis)
        if token_key in self._raices:
            datos = self._raices[token_key]
            # Convertir tuplas a objetos CandidatoEtimologico
            candidatos = []
            for termino, origen, raiz, deriv_existe in datos:
                cand = CandidatoEtimologico(
                    termino=termino, origen=origen, raiz=raiz,
                    derivacion_existe=deriv_existe,
                    es_metafora_viable=self._es_metafora_viable(token_key, termino)
                )
                cand.calcular_prioridad()
                candidatos.append(cand)
            candidatos.sort(key=lambda c: c.prioridad, reverse=True)
            return candidatos

        # 2. Si no está en caché -> LLAMAR A GEMINI
        print(f"[IA] Consultando etimología para: {token_src}...")
        datos_ia = ai_engine.consultar_nucleo(token_src, contexto)
        
        # 3. Guardar respuesta en Caché (para no pagar dos veces por la misma palabra)
        nuevas_entradas = []
        candidatos_obj = []
        
        for item in datos_ia:
            # Guardar en estructura simple para el diccionario _raices
            nuevas_entradas.append(
                (item['termino'], item['origen'], item['raiz'], item['derivacion_existe'])
            )
            
            # Crear objeto para retorno inmediato
            cand = CandidatoEtimologico(
                termino=item['termino'],
                origen=item['origen'],
                raiz=item['raiz'],
                derivacion_existe=item['derivacion_existe'],
                es_metafora_viable=item.get('es_metafora_viable', False)
            )
            cand.calcular_prioridad()
            candidatos_obj.append(cand)
            
            # Registrar metáfora si aplica
            if item.get('es_metafora_viable'):
                if token_key not in self._metaforas_viables:
                    self._metaforas_viables[token_key] = []
                self._metaforas_viables[token_key].append(item['termino'])

        # Actualizar memoria
        self._raices[token_key] = nuevas_entradas
        
        return candidatos_obj

# Instancia global de BaseEtimologica (necesaria para 'obtener_base_etimologica')
_base_etimologica = BaseEtimologica()

def obtener_base_etimologica() -> BaseEtimologica:
    """Función de acceso global a la base etimológica"""
    return _base_etimologica


# ══════════════════════════════════════════════════════════════
# PROCESADOR DE NÚCLEOS (P4)
# ══════════════════════════════════════════════════════════════

class ProcesadorNucleos:
    """
    P4: Núcleos Léxicos - Discriminador Semántico
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
        Returns: Diccionario con resultado del procesamiento
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
        if slot_n.status == TokenStatus.BLOQUEADO:
            return True
        loc_id = glosario.fase_b_verificar_bloqueo(slot_n.token_src, slot_n.pos_index)
        if loc_id:
            slot_n.bloquear(loc_id)
            return True
        return False
    
    # ══════════════════════════════════════════════════════════
    # F2. CACHE CHECK
    # ══════════════════════════════════════════════════════════
    
    def _f2_cache_check(self, slot_n: SlotN, glosario: Glosario) -> Optional[str]:
        entrada = glosario.obtener_entrada(slot_n.token_src)
        if entrada and entrada.status == TokenStatus.ASIGNADO:
            return entrada.token_tgt
        return None
    
    # ══════════════════════════════════════════════════════════
    # F3. BÚSQUEDA DE LEXEMAS
    # ══════════════════════════════════════════════════════════
    
    def _f3_busqueda_lexemas(self, slot_n: SlotN) -> List[CandidatoEtimologico]:
        return self.base_etim.buscar_raices(slot_n.token_src)
    
    # ══════════════════════════════════════════════════════════
    # F4. SELECCIÓN
    # ══════════════════════════════════════════════════════════
    
    def _f4_seleccion(self, slot_n: SlotN, candidatos: List[CandidatoEtimologico],
                      glosario: Glosario) -> Tuple[str, Optional[Reason]]:
        count = len(candidatos)
        
        if count == 0:
            return self._manejar_caso_dificil(slot_n, Reason.NO_ROOT, glosario)
        
        if count > 1:
            primer_cand = candidatos[0]
            if primer_cand.es_metafora_viable:
                return primer_cand.termino, None
            return self._manejar_caso_dificil(slot_n, Reason.COLLISION, glosario, candidatos)
        
        cand = candidatos[0]
        if not cand.derivacion_existe:
            return self._manejar_caso_dificil(slot_n, Reason.GAP_DERIVATION, glosario)
        
        return cand.termino, None
    
    def _manejar_caso_dificil(self, slot_n: SlotN, reason: Reason,
                              glosario: Glosario,
                              candidatos: List[CandidatoEtimologico] = None) -> Tuple[str, Reason]:
        if self._procesador_casos_dificiles:
            resultado = self._procesador_casos_dificiles.procesar(
                slot_n, reason, glosario, candidatos
            )
            return resultado.get("n_base", slot_n.token_src), reason
        
        # Fallback simple
        if reason == Reason.NO_ROOT:
            return slot_n.token_src + "-ado", reason
        elif reason == Reason.GAP_DERIVATION:
            return slot_n.token_src + "-ado", reason
        elif reason == Reason.COLLISION:
            return candidatos[0].termino if candidatos else slot_n.token_src, reason
        
        return slot_n.token_src, reason
    
    # ══════════════════════════════════════════════════════════
    # F5. MORFOLOGÍA ADAPTATIVA
    # ══════════════════════════════════════════════════════════
    
    def _f5_morfologia(self, n_base: str, morph_src: MorfologiaFuente) -> Tuple[str, MorfologiaTarget]:
        morph_tgt = MorfologiaTarget()
        n_flexionado = n_base
        
        # NÚMERO
        if morph_src.numero == "singular":
            morph_tgt.numero = "singular"
        elif morph_src.numero == "dual":
            morph_tgt.numero = "plural"
            n_flexionado = self._pluralizar(n_base)
        elif morph_src.numero == "plural":
            morph_tgt.numero = "plural"
            n_flexionado = self._pluralizar(n_base)
        
        # GÉNERO
        if morph_src.genero:
            morph_tgt.genero = self._adaptar_genero(n_base, morph_src.genero)
        else:
            morph_tgt.genero = self._inferir_genero(n_base)
        
        # PERSONA Y TIEMPO (Simplificado)
        if morph_src.persona:
            morph_tgt.persona = morph_src.persona
        if morph_src.tiempo:
            morph_tgt.tiempo = morph_src.tiempo
        if morph_src.voz:
            morph_tgt.voz = morph_src.voz
        
        return n_flexionado, morph_tgt
    
    def _pluralizar(self, termino: str) -> str:
        if termino.endswith(("a", "e", "i", "o", "u")):
            return termino + "s"
        elif termino.endswith(("s", "x", "z")):
            return termino + "es" if termino.endswith("z") else termino
        else:
            return termino + "es"
    
    def _adaptar_genero(self, termino: str, genero_src: str) -> str:
        # Simplificado
        return "masculino" 
    
    def _inferir_genero(self, termino: str) -> str:
        if termino.endswith("a") and not termino.endswith(("ma", "ta")):
            return "femenino"
        elif termino.endswith(("ción", "sión", "dad", "tad", "tud")):
            return "femenino"
        return "masculino"
    
    # ══════════════════════════════════════════════════════════
    # F6 Y F7
    # ══════════════════════════════════════════════════════════
    
    def _f6_verificar_paridad(self, slot_n: SlotN, n_base: str, glosario: Glosario) -> None:
        glosario.fase_b_verificar_sinonimia(slot_n.token_src, n_base)
    
    def _f7_salida(self, slot_n: SlotN, n_base: str, glosario: Glosario,
                   reason: Optional[Reason] = None) -> None:
        margen = 6 if reason == Reason.IDIOM else (5 if reason == Reason.COLLISION else 1)
        etiqueta = reason.name if reason else None
        
        glosario.fase_b_asignar(
            slot_n.token_src,
            n_base,
            margen=margen,
            etiqueta=etiqueta
        )


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA (Exports)
# ══════════════════════════════════════════════════════════════

def crear_slot_n(token_src: str, cat_src: CategoriaGramatical,
                 pos_index: int, morph: MorfologiaFuente = None) -> SlotN:
    return SlotN(
        token_src=token_src,
        cat_src=cat_src,
        morph_src=morph or MorfologiaFuente(),
        pos_index=pos_index,
        status=TokenStatus.PENDIENTE
    )

def es_metafora_viable(token_src: str, contexto: str = None) -> bool:
    base = obtener_base_etimologica()
    candidatos = base.buscar_raices(token_src)
    return any(c.es_metafora_viable for c in candidatos)
