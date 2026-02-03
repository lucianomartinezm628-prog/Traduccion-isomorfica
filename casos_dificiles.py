"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 7/13: Casos Léxicos Difíciles - Generador de Soluciones (P6)
════════════════════════════════════════════════════════════════

TRIGGER: P4.F4 (Selección)
INPUT:   Slot_N + Reason
OUTPUT:  N_base → Glosario → P4.F5 (morfología) → P3

RAZONES VÁLIDAS:
  - NO_ROOT: Sin raíz etimológica en español
  - GAP_DERIVATION: Raíz existe, derivación específica no
  - COLLISION: Múltiples candidatos O conflicto de mapeo 1:1
  - IDIOM: Token es parte de locución fija

RESTRICCIONES:
  - Compuestos ETYM(A)-ETYM(B)-...: PERMITIDOS para locuciones (sin límite)
  - Núcleos individuales: NUNCA compuestos
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from constants import (
    TokenStatus, TokenCategoria, CategoriaGramatical,
    Reason, ConsultaCodigo, SUFIJOS, MARGEN_VALORES
)
from models import SlotN, Locucion, Consulta, Opcion
from glossary import Glosario


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════

@dataclass
class ResultadoCasoDificil:
    """Resultado del procesamiento de un caso difícil"""
    n_base: str
    reason: Reason
    exito: bool = True
    requiere_consulta: bool = False
    consulta: Optional[Consulta] = None
    mensaje: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_base": self.n_base,
            "reason": self.reason.name,
            "exito": self.exito,
            "requiere_consulta": self.requiere_consulta,
            "mensaje": self.mensaje
        }


# ══════════════════════════════════════════════════════════════
# TRANSLITERADOR
# ══════════════════════════════════════════════════════════════

class Transliterador:
    """
    Sistema de transliteración DIN 31635 (default)
    """
    
    # Mapeo de caracteres árabes a latino (DIN 31635)
    _MAPA_DIN_31635 = {
        'ء': 'ʾ',
        'ا': 'ā',
        'ب': 'b',
        'ت': 't',
        'ث': 'ṯ',
        'ج': 'ǧ',
        'ح': 'ḥ',
        'خ': 'ḫ',
        'د': 'd',
        'ذ': 'ḏ',
        'ر': 'r',
        'ز': 'z',
        'س': 's',
        'ش': 'š',
        'ص': 'ṣ',
        'ض': 'ḍ',
        'ط': 'ṭ',
        'ظ': 'ẓ',
        'ع': 'ʿ',
        'غ': 'ġ',
        'ف': 'f',
        'ق': 'q',
        'ك': 'k',
        'ل': 'l',
        'م': 'm',
        'ن': 'n',
        'ه': 'h',
        'و': 'w',
        'ي': 'y',
        'ة': 'a',
        'ى': 'ā',
        # Vocales cortas (diacríticos)
        'َ': 'a',
        'ُ': 'u',
        'ِ': 'i',
        # Vocales largas ya incluidas
    }
    
    @classmethod
    def transliterar(cls, texto: str) -> str:
        """Transliterar texto árabe a latino"""
        resultado = []
        for char in texto:
            if char in cls._MAPA_DIN_31635:
                resultado.append(cls._MAPA_DIN_31635[char])
            elif char.isascii():
                resultado.append(char)
            else:
                resultado.append(char)  # Mantener si no está en mapa
        return ''.join(resultado)
    
    @classmethod
    def es_ya_transliterado(cls, texto: str) -> bool:
        """Verificar si el texto ya está transliterado"""
        # Si contiene caracteres árabes, no está transliterado
        for char in texto:
            if char in cls._MAPA_DIN_31635:
                return False
        return True


# ══════════════════════════════════════════════════════════════
# GENERADOR DE SUFIJOS
# ══════════════════════════════════════════════════════════════

class GeneradorSufijos:
    """
    Generador de sufijos para neologismos (P9.B.2)
    """
    
    @staticmethod
    def obtener_sufijo(categoria: CategoriaGramatical, subtipo: str = None) -> str:
        """
        Obtener sufijo apropiado para la categoría
        
        Args:
            categoria: Categoría gramatical
            subtipo: Subtipo específico (abstracto, concreto, etc.)
        """
        if categoria not in SUFIJOS:
            return "-ado"  # Default
        
        sufijos_cat = SUFIJOS[categoria]
        
        if subtipo and subtipo in sufijos_cat:
            return sufijos_cat[subtipo][0]  # Primer sufijo del subtipo
        
        # Usar primer sufijo disponible
        for subtipos in sufijos_cat.values():
            if subtipos:
                return subtipos[0]
        
        return "-ado"
    
    @staticmethod
    def aplicar_sufijo(raiz: str, sufijo: str) -> str:
        """Aplicar sufijo a una raíz"""
        # Limpiar raíz
        raiz_limpia = raiz.rstrip("-")
        
        # Ajustar terminación si es necesario
        if raiz_limpia.endswith(('a', 'e', 'i', 'o', 'u')) and sufijo.startswith(('a', 'e', 'i', 'o', 'u')):
            raiz_limpia = raiz_limpia[:-1]
        
        return raiz_limpia + sufijo.lstrip("-")


# ══════════════════════════════════════════════════════════════
# BASE DE DATOS ETIMOLÓGICA PARA LOCUCIONES
# ══════════════════════════════════════════════════════════════

class BaseEtimologicaLocuciones:
    """
    Traducciones etimológicas de componentes para locuciones
    """
    
    _TRADUCCIONES_ETYM = {
        # Preposiciones
        "bi": "por",
        "li": "para",
        "fi": "en",
        "min": "de",
        "ʿan": "sobre",
        "ʿalā": "sobre",
        "ilā": "hacia",
        # Sustantivos comunes en locuciones
        "ʿayn": "ojo",
        "yad": "mano",
        "qalb": "corazón",
        "nafs": "alma",
        "rūḥ": "espíritu",
        "wajh": "rostro",
        "lisān": "lengua",
        "raʾs": "cabeza",
        # Sufijos pronominales
        "hā": "suyo",
        "hu": "suyo",
        "humā": "suyos-dos",
        "hum": "suyos",
        "hunna": "suyas",
        "ka": "tuyo",
        "ki": "tuya",
        "kumā": "vuestros-dos",
        "kum": "vuestros",
        "kunna": "vuestras",
        "ī": "mío",
        "nā": "nuestro",
        # Otros
        "wāḥid": "uno",
        "wāḥida": "una",
    }
    
    @classmethod
    def obtener_traduccion_etym(cls, componente: str) -> str:
        """Obtener traducción etimológica de un componente"""
        comp_limpio = componente.lower().strip("-")
        
        if comp_limpio in cls._TRADUCCIONES_ETYM:
            return cls._TRADUCCIONES_ETYM[comp_limpio]
        
        # Si no está en el diccionario, transliterar
        return Transliterador.transliterar(componente)


# ══════════════════════════════════════════════════════════════
# PROCESADOR DE CASOS DIFÍCILES (P6)
# ══════════════════════════════════════════════════════════════

class ProcesadorCasosDificiles:
    """
    P6: Casos Léxicos Difíciles - Generador de Soluciones
    
    Estrategias:
      - NO_ROOT: Neologismo radical (TRANSLIT + sufijo)
      - GAP_DERIVATION: Neologismo derivativo (raíz_ES + sufijo)
      - COLLISION: Selección o transliteración para distinguir
      - IDIOM: Compuesto ETYM(A)-ETYM(B)-ETYM(C)-...
    """
    
    def __init__(self):
        self.transliterador = Transliterador()
        self.generador_sufijos = GeneradorSufijos()
        self.base_etym_loc = BaseEtimologicaLocuciones()
        self._consultas_pendientes: List[Consulta] = []
    
    def procesar(self, slot_n: SlotN, reason: Reason, glosario: Glosario,
                 candidatos: List[Any] = None) -> Dict[str, Any]:
        """
        Procesar un caso difícil
        
        Args:
            slot_n: Slot del núcleo
            reason: Razón del caso difícil
            glosario: Glosario del sistema
            candidatos: Lista de candidatos (para COLLISION)
        
        Returns:
            Diccionario con n_base y metadata
        """
        resultado = ResultadoCasoDificil(
            n_base=slot_n.token_src,
            reason=reason
        )
        
        if reason == Reason.NO_ROOT:
            resultado = self._estrategia_no_root(slot_n)
        
        elif reason == Reason.GAP_DERIVATION:
            resultado = self._estrategia_gap_derivation(slot_n, candidatos)
        
        elif reason == Reason.COLLISION:
            resultado = self._estrategia_collision(slot_n, candidatos, glosario)
        
        elif reason == Reason.IDIOM:
            resultado = self._estrategia_idiom(slot_n, glosario)
        
        # Registrar en glosario
        if resultado.exito and not resultado.requiere_consulta:
            self._registrar_en_glosario(slot_n, resultado, glosario)
        
        return resultado.to_dict()
    
    # ══════════════════════════════════════════════════════════
    # ESTRATEGIA: NO_ROOT
    # ══════════════════════════════════════════════════════════
    
    def _estrategia_no_root(self, slot_n: SlotN) -> ResultadoCasoDificil:
        """
        NO_ROOT: Neologismo radical
        
        N_base = TRANSLITERAR(raíz_fuente) + SUFIJO_ES(categoría)
        """
        # Transliterar token fuente
        translit = Transliterador.transliterar(slot_n.token_src)
        
        # Obtener sufijo según categoría
        sufijo = self.generador_sufijos.obtener_sufijo(slot_n.cat_src)
        
        # Formar neologismo
        n_base = self.generador_sufijos.aplicar_sufijo(translit, sufijo)
        
        return ResultadoCasoDificil(
            n_base=n_base,
            reason=Reason.NO_ROOT,
            mensaje=f"Neologismo radical: {slot_n.token_src} → {n_base}"
        )
    
    # ══════════════════════════════════════════════════════════
    # ESTRATEGIA: GAP_DERIVATION
    # ══════════════════════════════════════════════════════════
    
    def _estrategia_gap_derivation(self, slot_n: SlotN,
                                    candidatos: List[Any] = None) -> ResultadoCasoDificil:
        """
        GAP_DERIVATION: Neologismo derivativo
        
        N_base = raíz_española_existente + SUFIJO_ES(categoría)
        Si colisiona con existente → usar NO_ROOT
        """
        raiz_es = None
        
        # Obtener raíz española del primer candidato
        if candidatos and len(candidatos) > 0:
            cand = candidatos[0]
            if hasattr(cand, 'raiz'):
                raiz_es = cand.raiz
        
        if not raiz_es:
            # Fallback a NO_ROOT
            return self._estrategia_no_root(slot_n)
        
        # Obtener sufijo
        sufijo = self.generador_sufijos.obtener_sufijo(slot_n.cat_src, "participial")
        
        # Formar neologismo derivativo
        n_base = self.generador_sufijos.aplicar_sufijo(raiz_es, sufijo)
        
        # Verificar colisión con palabra existente
        if self._palabra_existe(n_base):
            # Colisión → usar NO_ROOT
            return self._estrategia_no_root(slot_n)
        
        return ResultadoCasoDificil(
            n_base=n_base,
            reason=Reason.GAP_DERIVATION,
            mensaje=f"Neologismo derivativo: {raiz_es} + {sufijo} → {n_base}"
        )
    
    def _palabra_existe(self, palabra: str) -> bool:
        """Verificar si una palabra ya existe en español (simplificado)"""
        # En producción, se consultaría un diccionario real
        palabras_existentes = {
            "intelectual", "intelectualidad", "inteligente",
            "racional", "racionalidad", "espiritual"
        }
        return palabra.lower() in palabras_existentes
    
    # ══════════════════════════════════════════════════════════
    # ESTRATEGIA: COLLISION
    # ══════════════════════════════════════════════════════════
    
    def _estrategia_collision(self, slot_n: SlotN, candidatos: List[Any],
                               glosario: Glosario) -> ResultadoCasoDificil:
        """
        COLLISION: Múltiples candidatos O mapeo duplicado
        
        1. Aplicar regla de preferencia etimológica si hay metáfora viable
        2. Evaluar candidatos
        3. Si duda → consultar usuario
        4. Si duplicado → transliterar para distinguir
        """
        if not candidatos or len(candidatos) == 0:
            return self._estrategia_no_root(slot_n)
        
        # Verificar si hay candidato con metáfora viable (preferencia etimológica)
        for cand in candidatos:
            if hasattr(cand, 'es_metafora_viable') and cand.es_metafora_viable:
                return ResultadoCasoDificil(
                    n_base=cand.termino,
                    reason=Reason.COLLISION,
                    mensaje=f"Preferencia etimológica (metáfora): {cand.termino}"
                )
        
        # Evaluar candidatos
        mejor_cand = self._evaluar_candidatos(candidatos)
        
        if mejor_cand:
            # Verificar si ya está en glosario con otra traducción
            entrada = glosario.obtener_entrada(slot_n.token_src)
            if entrada and entrada.token_tgt and entrada.token_tgt != mejor_cand.termino:
                # Mapeo duplicado → transliterar para distinguir
                translit = Transliterador.transliterar(slot_n.token_src)
                return ResultadoCasoDificil(
                    n_base=translit,
                    reason=Reason.COLLISION,
                    mensaje=f"Transliteración para distinguir: {translit}"
                )
            
            return ResultadoCasoDificil(
                n_base=mejor_cand.termino,
                reason=Reason.COLLISION,
                mensaje=f"Mejor candidato: {mejor_cand.termino}"
            )
        
        # Duda → crear consulta para usuario
        consulta = self._crear_consulta_collision(slot_n, candidatos)
        
        return ResultadoCasoDificil(
            n_base=candidatos[0].termino if hasattr(candidatos[0], 'termino') else str(candidatos[0]),
            reason=Reason.COLLISION,
            requiere_consulta=True,
            consulta=consulta,
            mensaje="Requiere decisión del usuario"
        )
    
    def _evaluar_candidatos(self, candidatos: List[Any]) -> Optional[Any]:
        """
        Evaluar candidatos por:
        - Cercanía etimológica (mayor = mejor)
        - Riesgo de colapso (menor = mejor)
        """
        if not candidatos:
            return None
        
        mejor = candidatos[0]
        mejor_score = 0
        
        for cand in candidatos:
            score = 0
            
            # Prioridad etimológica
            if hasattr(cand, 'prioridad'):
                score += cand.prioridad * 2
            
            # Metáfora viable
            if hasattr(cand, 'es_metafora_viable') and cand.es_metafora_viable:
                score += 5
            
            # Derivación existe
            if hasattr(cand, 'derivacion_existe') and cand.derivacion_existe:
                score += 3
            
            if score > mejor_score:
                mejor_score = score
                mejor = cand
        
        # Si la diferencia es clara, retornar mejor
        if mejor_score > 3:
            return mejor
        
        # Duda → retornar None para consultar
        return None
    
    def _crear_consulta_collision(self, slot_n: SlotN,
                                   candidatos: List[Any]) -> Consulta:
        """Crear consulta C2 para colisión"""
        opciones = []
        for i, cand in enumerate(candidatos[:5]):  # Máximo 5 opciones
            letra = chr(65 + i)  # A, B, C, ...
            termino = cand.termino if hasattr(cand, 'termino') else str(cand)
            origen = cand.origen if hasattr(cand, 'origen') else "N/A"
            opciones.append(Opcion(letra, termino, f"Origen: {origen}"))
        
        return Consulta(
            numero=len(self._consultas_pendientes) + 1,
            codigo=ConsultaCodigo.C2_COLLISION_DUDA,
            contexto=f"Múltiples candidatos para '{slot_n.token_src}'",
            token_o_frase=slot_n.token_src,
            opciones=opciones,
            recomendacion="A"
        )
    
    # ══════════════════════════════════════════════════════════
    # ESTRATEGIA: IDIOM
    # ══════════════════════════════════════════════════════════
    
    def _estrategia_idiom(self, slot_n: SlotN, glosario: Glosario) -> ResultadoCasoDificil:
        """
        IDIOM: Token es parte de locución fija
        
        N_base = ETYM(A)-ETYM(B)-ETYM(C)-...
        Sin límite de componentes
        """
        # Buscar locución en glosario
        locucion = None
        for loc_id, loc in glosario.obtener_locuciones().items():
            if slot_n.token_src in loc.componentes:
                locucion = loc
                break
        
        if not locucion:
            # No encontrada → fallback a NO_ROOT
            return self._estrategia_no_root(slot_n)
        
        # Si ya tiene traducción, usarla
        if locucion.tgt:
            return ResultadoCasoDificil(
                n_base=locucion.tgt,
                reason=Reason.IDIOM,
                mensaje=f"Locución existente: {locucion.tgt}"
            )
        
        # Generar traducción ETYM(A)-ETYM(B)-ETYM(C)-...
        partes_etym = []
        for comp in locucion.componentes:
            etym = self.base_etym_loc.obtener_traduccion_etym(comp)
            partes_etym.append(etym)
        
        n_base = "-".join(partes_etym)
        
        # Actualizar locución
        locucion.tgt = n_base
        
        return ResultadoCasoDificil(
            n_base=n_base,
            reason=Reason.IDIOM,
            mensaje=f"Locución: {locucion.src} → {n_base}"
        )
    
    def generar_traduccion_locucion(self, locucion: Locucion) -> str:
        """
        Generar traducción para una locución
        Formato: ETYM(A)-ETYM(B)-ETYM(C)-...
        """
        partes = []
        for comp in locucion.componentes:
            etym = self.base_etym_loc.obtener_traduccion_etym(comp)
            partes.append(etym)
        
        return "-".join(partes)
    
    # ══════════════════════════════════════════════════════════
    # REGISTRO EN GLOSARIO
    # ══════════════════════════════════════════════════════════
    
    def _registrar_en_glosario(self, slot_n: SlotN, resultado: ResultadoCasoDificil,
                                glosario: Glosario) -> None:
        """Registrar resultado en glosario"""
        margen = MARGEN_VALORES.get(resultado.reason.name, 3)
        
        glosario.fase_b_asignar(
            slot_n.token_src,
            resultado.n_base,
            margen=margen,
            etiqueta=resultado.reason.name
        )
    
    # ══════════════════════════════════════════════════════════
    # CONSULTAS
    # ══════════════════════════════════════════════════════════
    
    def obtener_consultas_pendientes(self) -> List[Consulta]:
        """Obtener consultas pendientes"""
        return self._consultas_pendientes.copy()
    
    def limpiar_consultas(self) -> None:
        """Limpiar consultas pendientes"""
        self._consultas_pendientes.clear()
    
    def aplicar_decision_usuario(self, consulta_num: int, opcion: str,
                                  slot_n: SlotN, glosario: Glosario) -> Dict[str, Any]:
        """Aplicar decisión del usuario a una consulta"""
        # Buscar consulta
        consulta = None
        for c in self._consultas_pendientes:
            if c.numero == consulta_num:
                consulta = c
                break
        
        if not consulta:
            return {"exito": False, "mensaje": "Consulta no encontrada"}
        
        # Buscar opción seleccionada
        for op in consulta.opciones:
            if op.letra.upper() == opcion.upper():
                n_base = op.texto
                
                resultado = ResultadoCasoDificil(
                    n_base=n_base,
                    reason=Reason.COLLISION,
                    mensaje=f"Decisión usuario: {n_base}"
                )
                
                self._registrar_en_glosario(slot_n, resultado, glosario)
                
                # Remover consulta de pendientes
                self._consultas_pendientes = [
                    c for c in self._consultas_pendientes if c.numero != consulta_num
                ]
                
                return resultado.to_dict()
        
        return {"exito": False, "mensaje": "Opción no válida"}


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA
# ══════════════════════════════════════════════════════════════

def transliterar(texto: str) -> str:
    """Función de conveniencia para transliterar"""
    return Transliterador.transliterar(texto)


def generar_neologismo_radical(token_src: str, categoria: CategoriaGramatical) -> str:
    """Generar neologismo radical (NO_ROOT)"""
    translit = Transliterador.transliterar(token_src)
    sufijo = GeneradorSufijos.obtener_sufijo(categoria)
    return GeneradorSufijos.aplicar_sufijo(translit, sufijo)


def generar_neologismo_derivativo(raiz_es: str, categoria: CategoriaGramatical) -> str:
    """Generar neologismo derivativo (GAP_DERIVATION)"""
    sufijo = GeneradorSufijos.obtener_sufijo(categoria, "participial")
    return GeneradorSufijos.aplicar_sufijo(raiz_es, sufijo)


def generar_traduccion_locucion(componentes: List[str]) -> str:
    """Generar traducción de locución ETYM(A)-ETYM(B)-..."""
    partes = []
    for comp in componentes:
        etym = BaseEtimologicaLocuciones.obtener_traduccion_etym(comp)
        partes.append(etym)
    return "-".join(partes)
