"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 9/13: Formación Léxica - Transliteración y Neologismos (P9)
════════════════════════════════════════════════════════════════

PROPÓSITO:
  Definir las reglas de formación para términos sin equivalente directo.

ALCANCE:
  - Núcleos léxicos: SÍ
  - Locuciones: SÍ (formato especial ETYM)
  - Partículas sueltas: PROHIBIDO

SECCIONES:
  A. Reglas de Transliteración
  B. Reglas de Neologismos Radicales
  C. Reglas de Neologismos Derivativos
  D. Reglas de Locuciones
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto

from constants import (
    TokenCategoria, CategoriaGramatical,
    ModoTransliteracion, NormaTransliteracion,
    Reason, SUFIJOS
)
from config import obtener_config


# ══════════════════════════════════════════════════════════════
# SECCIÓN A: TRANSLITERACIÓN
# ══════════════════════════════════════════════════════════════

class SistemaTransliteracion:
    """
    P9.A: Sistema de Transliteración
    
    Normas disponibles:
      - DIN 31635 (estándar académico para árabe) [DEFAULT]
      - ISO 233
      - Simplificada (sin diacríticos)
    """
    
    # Mapeo DIN 31635 (estándar académico)
    _MAPA_DIN_31635 = {
        # Consonantes
        'ء': 'ʾ', 'ا': 'ā', 'ب': 'b', 'ت': 't', 'ث': 'ṯ',
        'ج': 'ǧ', 'ح': 'ḥ', 'خ': 'ḫ', 'د': 'd', 'ذ': 'ḏ',
        'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'š', 'ص': 'ṣ',
        'ض': 'ḍ', 'ط': 'ṭ', 'ظ': 'ẓ', 'ع': 'ʿ', 'غ': 'ġ',
        'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        # Letras especiales
        'ة': 'a', 'ى': 'ā', 'أ': 'ʾa', 'إ': 'ʾi', 'آ': 'ʾā',
        'ؤ': 'ʾ', 'ئ': 'ʾ',
        # Vocales cortas (diacríticos)
        'َ': 'a', 'ُ': 'u', 'ِ': 'i',
        # Tanwin
        'ً': 'an', 'ٌ': 'un', 'ٍ': 'in',
        # Shadda y sukun
        'ّ': '', 'ْ': '',
    }
    
    # Mapeo ISO 233
    _MAPA_ISO_233 = {
        'ء': 'ʼ', 'ا': 'ʼā', 'ب': 'b', 'ت': 't', 'ث': 'ṯ',
        'ج': 'ǧ', 'ح': 'ḥ', 'خ': 'ẖ', 'د': 'd', 'ذ': 'ḏ',
        'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'š', 'ص': 'ṣ',
        'ض': 'ḍ', 'ط': 'ṭ', 'ظ': 'ẓ', 'ع': 'ʻ', 'غ': 'ġ',
        'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        'ة': 'ẗ', 'ى': 'ỳ',
        'َ': 'a', 'ُ': 'u', 'ِ': 'i',
    }
    
    # Mapeo Simplificado (sin diacríticos)
    _MAPA_SIMPLIFICADO = {
        'ء': "'", 'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th',
        'ج': 'j', 'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'dh',
        'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's',
        'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': "'", 'غ': 'gh',
        'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        'ة': 'a', 'ى': 'a',
        'َ': 'a', 'ُ': 'u', 'ِ': 'i',
    }
    
    def __init__(self, norma: NormaTransliteracion = None):
        config = obtener_config()
        self.norma = norma or config.norma_transliteracion
        self._seleccionar_mapa()
    
    def _seleccionar_mapa(self) -> None:
        """Seleccionar mapa según norma"""
        if self.norma == NormaTransliteracion.DIN_31635:
            self._mapa = self._MAPA_DIN_31635
        elif self.norma == NormaTransliteracion.ISO_233:
            self._mapa = self._MAPA_ISO_233
        elif self.norma == NormaTransliteracion.SIMPLIFICADA:
            self._mapa = self._MAPA_SIMPLIFICADO
        else:
            self._mapa = self._MAPA_DIN_31635  # Default
    
    def cambiar_norma(self, norma: NormaTransliteracion) -> None:
        """Cambiar norma de transliteración"""
        self.norma = norma
        self._seleccionar_mapa()
    
    def transliterar(self, texto: str) -> str:
        """
        Transliterar texto árabe a latino
        
        Args:
            texto: Texto en árabe o mixto
        
        Returns:
            Texto transliterado según norma seleccionada
        """
        resultado = []
        
        for char in texto:
            if char in self._mapa:
                resultado.append(self._mapa[char])
            elif char.isascii():
                resultado.append(char)
            elif char.isspace():
                resultado.append(char)
            else:
                # Mantener caracteres desconocidos
                resultado.append(char)
        
        return ''.join(resultado)
    
    def es_transliterado(self, texto: str) -> bool:
        """Verificar si el texto ya está transliterado"""
        for char in texto:
            if char in self._mapa:
                return False
        return True
    
    def normalizar_lema(self, texto: str) -> str:
        """
        Normalizar a forma de lema
        
        - Verbos: infinitivo
        - Nominales: singular
        """
        translit = self.transliterar(texto)
        # Eliminar diacríticos de caso
        translit = translit.rstrip('aiun')
        return translit


# Instancia global
_sistema_transliteracion = SistemaTransliteracion()


def obtener_transliterador() -> SistemaTransliteracion:
    """Obtener sistema de transliteración global"""
    return _sistema_transliteracion


def transliterar(texto: str) -> str:
    """Función de conveniencia para transliterar"""
    return _sistema_transliteracion.transliterar(texto)


# ══════════════════════════════════════════════════════════════
# SECCIÓN B: NEOLOGISMOS RADICALES
# ══════════════════════════════════════════════════════════════

class GeneradorNeologismosRadicales:
    """
    P9.B: Neologismos Radicales
    
    TRIGGER: P6 → Reason: "NO_ROOT"
    CONTEXTO: No existe raíz etimológica equivalente en español.
    
    ESTRUCTURA: N_base = TRANSLITERAR(raíz_fuente) + SUFIJO_ES(categoría)
    """
    
    def __init__(self, transliterador: SistemaTransliteracion = None):
        self.transliterador = transliterador or obtener_transliterador()
    
    def generar(self, token_src: str, categoria: CategoriaGramatical,
                subtipo: str = None) -> str:
        """
        Generar neologismo radical
        
        Args:
            token_src: Token fuente
            categoria: Categoría gramatical
            subtipo: Subtipo específico (abstracto, concreto, etc.)
        
        Returns:
            Neologismo formado
        """
        # Transliterar
        translit = self.transliterador.transliterar(token_src)
        translit = self._limpiar_raiz(translit)
        
        # Obtener sufijo
        sufijo = self._obtener_sufijo(categoria, subtipo)
        
        # Combinar
        return self._combinar(translit, sufijo)
    
    def _limpiar_raiz(self, raiz: str) -> str:
        """Limpiar raíz para combinación"""
        # Eliminar caracteres finales problemáticos
        raiz = raiz.rstrip("-'ʾʿ")
        return raiz
    
    def _obtener_sufijo(self, categoria: CategoriaGramatical, 
                        subtipo: str = None) -> str:
        """Obtener sufijo según categoría"""
        if categoria not in SUFIJOS:
            return "-ado"  # Default
        
        sufijos_cat = SUFIJOS[categoria]
        
        # Si hay subtipo específico
        if subtipo and subtipo in sufijos_cat:
            return sufijos_cat[subtipo][0]
        
        # Sufijos por defecto según categoría
        defaults = {
            CategoriaGramatical.SUSTANTIVO: "-idad",
            CategoriaGramatical.ADJETIVO: "-ado",
            CategoriaGramatical.VERBO: "-ar",
            CategoriaGramatical.ADVERBIO: "-mente",
        }
        
        return defaults.get(categoria, "-ado")
    
    def _combinar(self, raiz: str, sufijo: str) -> str:
        """Combinar raíz con sufijo"""
        raiz = raiz.rstrip("-")
        sufijo = sufijo.lstrip("-")
        
        # Ajustar si terminan/empiezan con vocal
        if raiz and sufijo:
            if raiz[-1] in "aeiouāīū" and sufijo[0] in "aeiou":
                raiz = raiz[:-1]
        
        return raiz + sufijo


# ══════════════════════════════════════════════════════════════
# SECCIÓN C: NEOLOGISMOS DERIVATIVOS
# ══════════════════════════════════════════════════════════════

class GeneradorNeologismosDerivativos:
    """
    P9.C: Neologismos Derivativos
    
    TRIGGER: P6 → Reason: "GAP_DERIVATION"
    CONTEXTO: Raíz existe en español, pero la derivación específica no.
    
    ESTRUCTURA: N_base = raíz_española_existente + SUFIJO_ES(categoría)
    """
    
    # Palabras existentes en español (para verificar colisión)
    _PALABRAS_EXISTENTES = {
        "intelectual", "intelectualidad", "inteligente", "inteligencia",
        "racional", "racionalidad", "razón", "razonamiento",
        "espiritual", "espiritualidad", "espíritu",
        "anímico", "animosidad", "alma",
        "verbal", "verbalidad", "verbo",
        "existente", "existencia", "existir",
    }
    
    def __init__(self):
        self.generador_radical = GeneradorNeologismosRadicales()
    
    def generar(self, raiz_es: str, categoria: CategoriaGramatical,
                subtipo: str = None) -> Tuple[str, bool]:
        """
        Generar neologismo derivativo
        
        Args:
            raiz_es: Raíz española existente
            categoria: Categoría gramatical
            subtipo: Subtipo específico
        
        Returns:
            Tupla (neologismo, exito)
            Si hay colisión, retorna (neologismo_radical, False)
        """
        # Limpiar raíz
        raiz = raiz_es.rstrip("-")
        
        # Obtener sufijo
        sufijo = self._obtener_sufijo(categoria, subtipo)
        
        # Formar neologismo
        neologismo = self._combinar(raiz, sufijo)
        
        # Verificar colisión
        if self._existe_colision(neologismo):
            # Fallback a transliteración
            return neologismo + "-alt", False
        
        return neologismo, True
    
    def _obtener_sufijo(self, categoria: CategoriaGramatical,
                        subtipo: str = None) -> str:
        """Obtener sufijo para derivación"""
        # Para GAP_DERIVATION, preferir sufijos participiales
        if categoria == CategoriaGramatical.ADJETIVO:
            return "-ado"
        elif categoria == CategoriaGramatical.SUSTANTIVO:
            return "-ación" if subtipo == "abstracto" else "-ado"
        elif categoria == CategoriaGramatical.VERBO:
            return "-ar"
        return "-ado"
    
    def _combinar(self, raiz: str, sufijo: str) -> str:
        """Combinar raíz con sufijo"""
        raiz = raiz.rstrip("-")
        sufijo = sufijo.lstrip("-")
        
        # Ajustes ortográficos
        if raiz.endswith("c") and sufijo.startswith("a"):
            # intelectar → no cambio
            pass
        elif raiz.endswith("g") and sufijo.startswith("a"):
            # Mantener g
            pass
        
        return raiz + sufijo
    
    def _existe_colision(self, palabra: str) -> bool:
        """Verificar si palabra ya existe con otro sentido"""
        return palabra.lower() in self._PALABRAS_EXISTENTES


# ══════════════════════════════════════════════════════════════
# SECCIÓN D: LOCUCIONES
# ══════════════════════════════════════════════════════════════

class GeneradorLocuciones:
    """
    P9.D: Formación de Locuciones
    
    TRIGGER: P6 → Reason: "IDIOM" | P8.A (detección)
    CONTEXTO: Secuencia fija con sentido no composicional.
    
    FORMATO: ETYM(A)-ETYM(B)-ETYM(C)-... (sin límite de componentes)
    """
    
    # Traducciones etimológicas de componentes comunes
    _TRADUCCIONES_ETYM = {
        # Preposiciones
        "bi": "por", "li": "para", "fi": "en", "min": "de",
        "ʿan": "sobre", "ʿalā": "sobre", "ilā": "hacia",
        "maʿa": "con", "bayna": "entre", "fawqa": "sobre",
        "taḥta": "bajo", "ʿinda": "junto-a", "ladā": "ante",
        
        # Sustantivos corporales
        "ʿayn": "ojo", "yad": "mano", "qalb": "corazón",
        "nafs": "alma", "rūḥ": "espíritu", "wajh": "rostro",
        "lisān": "lengua", "raʾs": "cabeza", "qādam": "pie",
        "ẓahr": "espalda", "baṭn": "vientre", "ṣadr": "pecho",
        
        # Sustantivos abstractos
        "ḥaqq": "verdad", "ʿaql": "intelecto", "fikr": "pensamiento",
        "ʿilm": "ciencia", "ḥikma": "sabiduría", "kalām": "discurso",
        
        # Sufijos pronominales
        "hā": "suyo-f", "hu": "suyo-m", "humā": "suyos-dual",
        "hum": "suyos-m", "hunna": "suyas-f",
        "ka": "tuyo-m", "ki": "tuya-f", "kumā": "vuestro-dual",
        "kum": "vuestro-m", "kunna": "vuestra-f",
        "ī": "mío", "nā": "nuestro",
        
        # Numerales
        "wāḥid": "uno", "wāḥida": "una", "ithnān": "dos",
        
        # Demostrativos
        "hādhā": "este", "hādhihi": "esta", "dhālika": "aquel",
        
        # Partículas
        "lā": "no", "mā": "lo-que", "man": "quien",
    }
    
    def __init__(self, transliterador: SistemaTransliteracion = None):
        self.transliterador = transliterador or obtener_transliterador()
    
    def generar_traduccion(self, componentes: List[str]) -> str:
        """
        Generar traducción de locución
        
        Formato: ETYM(A)-ETYM(B)-ETYM(C)-...
        
        Args:
            componentes: Lista de componentes de la locución
        
        Returns:
            Traducción en formato A-B-C-...
        """
        partes = []
        
        for comp in componentes:
            etym = self._obtener_etym(comp)
            partes.append(etym)
        
        return "-".join(partes)
    
    def _obtener_etym(self, componente: str) -> str:
        """Obtener traducción etimológica de un componente"""
        # Limpiar componente
        comp_limpio = componente.lower().strip("-").strip()
        
        # Buscar en diccionario
        if comp_limpio in self._TRADUCCIONES_ETYM:
            return self._TRADUCCIONES_ETYM[comp_limpio]
        
        # Transliterar si no está
        translit = self.transliterador.transliterar(componente)
        return translit.strip("-")
    
    def agregar_traduccion_etym(self, componente: str, traduccion: str) -> None:
        """Agregar traducción etimológica personalizada"""
        self._TRADUCCIONES_ETYM[componente.lower()] = traduccion
    
    def obtener_todas_traducciones(self) -> Dict[str, str]:
        """Obtener todas las traducciones etimológicas"""
        return self._TRADUCCIONES_ETYM.copy()


# ══════════════════════════════════════════════════════════════
# CONTROLADOR DE FORMACIÓN LÉXICA
# ══════════════════════════════════════════════════════════════

@dataclass
class ResultadoFormacion:
    """Resultado de formación léxica"""
    termino: str
    metodo: str  # RADICAL, DERIVATIVO, LOCUCION, TRANSLITERACION
    reason: Reason
    exito: bool = True
    mensaje: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "termino": self.termino,
            "metodo": self.metodo,
            "reason": self.reason.name,
            "exito": self.exito,
            "mensaje": self.mensaje
        }


class ControladorFormacionLexica:
    """
    Controlador principal de formación léxica (P9)
    
    Integra:
      - Transliteración
      - Neologismos radicales
      - Neologismos derivativos
      - Locuciones
    """
    
    def __init__(self):
        self.transliterador = obtener_transliterador()
        self.gen_radical = GeneradorNeologismosRadicales(self.transliterador)
        self.gen_derivativo = GeneradorNeologismosDerivativos()
        self.gen_locucion = GeneradorLocuciones(self.transliterador)
    
    def formar(self, token_src: str, reason: Reason,
               categoria: CategoriaGramatical = None,
               raiz_es: str = None,
               componentes: List[str] = None) -> ResultadoFormacion:
        """
        Formar término según razón
        
        Args:
            token_src: Token fuente
            reason: Razón del caso difícil
            categoria: Categoría gramatical (para neologismos)
            raiz_es: Raíz española (para GAP_DERIVATION)
            componentes: Componentes (para IDIOM)
        """
        if reason == Reason.NO_ROOT:
            return self._formar_radical(token_src, categoria)
        
        elif reason == Reason.GAP_DERIVATION:
            return self._formar_derivativo(token_src, raiz_es, categoria)
        
        elif reason == Reason.IDIOM:
            return self._formar_locucion(token_src, componentes)
        
        elif reason == Reason.COLLISION:
            # Para COLLISION, usar transliteración para distinguir
            return self._formar_transliteracion(token_src)
        
        # Default
        return self._formar_transliteracion(token_src)
    
    def _formar_radical(self, token_src: str,
                        categoria: CategoriaGramatical) -> ResultadoFormacion:
        """Formar neologismo radical"""
        categoria = categoria or CategoriaGramatical.SUSTANTIVO
        termino = self.gen_radical.generar(token_src, categoria)
        
        return ResultadoFormacion(
            termino=termino,
            metodo="RADICAL",
            reason=Reason.NO_ROOT,
            mensaje=f"Neologismo radical: {token_src} → {termino}"
        )
    
    def _formar_derivativo(self, token_src: str, raiz_es: str,
                           categoria: CategoriaGramatical) -> ResultadoFormacion:
        """Formar neologismo derivativo"""
        if not raiz_es:
            # Sin raíz española, usar radical
            return self._formar_radical(token_src, categoria)
        
        categoria = categoria or CategoriaGramatical.ADJETIVO
        termino, exito = self.gen_derivativo.generar(raiz_es, categoria)
        
        if not exito:
            # Colisión, usar radical
            return self._formar_radical(token_src, categoria)
        
        return ResultadoFormacion(
            termino=termino,
            metodo="DERIVATIVO",
            reason=Reason.GAP_DERIVATION,
            mensaje=f"Neologismo derivativo: {raiz_es} → {termino}"
        )
    
    def _formar_locucion(self, token_src: str,
                         componentes: List[str]) -> ResultadoFormacion:
        """Formar traducción de locución"""
        if not componentes:
            # Sin componentes, separar por guiones o espacios
            componentes = token_src.replace("-", " ").split()
        
        termino = self.gen_locucion.generar_traduccion(componentes)
        
        return ResultadoFormacion(
            termino=termino,
            metodo="LOCUCION",
            reason=Reason.IDIOM,
            mensaje=f"Locución: {token_src} → {termino}"
        )
    
    def _formar_transliteracion(self, token_src: str) -> ResultadoFormacion:
        """Formar transliteración simple"""
        termino = self.transliterador.transliterar(token_src)
        
        return ResultadoFormacion(
            termino=termino,
            metodo="TRANSLITERACION",
            reason=Reason.COLLISION,
            mensaje=f"Transliteración: {token_src} → {termino}"
        )
    
    # ══════════════════════════════════════════════════════════
    # MODO DE APLICACIÓN EN TEXTO
    # ══════════════════════════════════════════════════════════
    
    def aplicar_inline(self, traduccion: str, transliteracion: str,
                       modo: ModoTransliteracion = None,
                       es_alfa: bool = False) -> str:
        """
        Aplicar transliteración inline según modo
        
        Modos:
          DESACTIVADO: Solo traducción
          SELECTIVO: traducción (transliteración) - solo si es_alfa
          COMPLETO: traducción (transliteración) - siempre
        """
        config = obtener_config()
        modo = modo or config.modo_transliteracion
        
        if modo == ModoTransliteracion.DESACTIVADO:
            return traduccion
        
        elif modo == ModoTransliteracion.SELECTIVO:
            if es_alfa:
                return f"{traduccion} ({transliteracion})"
            return traduccion
        
        elif modo == ModoTransliteracion.COMPLETO:
            return f"{traduccion} ({transliteracion})"
        
        return traduccion


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════

# Instancia global
_controlador_formacion = ControladorFormacionLexica()


def obtener_controlador_formacion() -> ControladorFormacionLexica:
    """Obtener controlador de formación"""
    return _controlador_formacion


def formar_neologismo_radical(token_src: str,
                              categoria: CategoriaGramatical) -> str:
    """Formar neologismo radical"""
    resultado = _controlador_formacion.formar(
        token_src, Reason.NO_ROOT, categoria=categoria
    )
    return resultado.termino


def formar_neologismo_derivativo(raiz_es: str,
                                 categoria: CategoriaGramatical) -> str:
    """Formar neologismo derivativo"""
    resultado = _controlador_formacion.formar(
        "", Reason.GAP_DERIVATION, categoria=categoria, raiz_es=raiz_es
    )
    return resultado.termino


def formar_locucion(componentes: List[str]) -> str:
    """Formar traducción de locución"""
    resultado = _controlador_formacion.formar(
        "-".join(componentes), Reason.IDIOM, componentes=componentes
    )
    return resultado.termino


def cambiar_modo_transliteracion(modo: ModoTransliteracion) -> None:
    """Cambiar modo de transliteración"""
    config = obtener_config()
    config.modo_transliteracion = modo


def cambiar_norma_transliteracion(norma: NormaTransliteracion) -> None:
    """Cambiar norma de transliteración"""
    config = obtener_config()
    config.norma_transliteracion = norma
    _controlador_formacion.transliterador.cambiar_norma(norma)
