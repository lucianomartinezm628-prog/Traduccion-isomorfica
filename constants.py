from enum import Enum, auto
from typing import List, Set

class TokenStatus(Enum):
    """Estados posibles de un token (P1.A.6)"""
    PENDIENTE = auto()   # Registrado, sin traducción
    ASIGNADO = auto()    # Traducción fijada, INMUTABLE
    BLOQUEADO = auto()   # Parte de locución, no traducir individualmente


class TokenCategoria(Enum):
    """Categorías de tokens (P1.A.4)"""
    NUCLEO = auto()      # Sustantivos, adjetivos, adverbios, verbos
    PARTICULA = auto()   # Preposiciones, conjunciones, pronombres
    LOCUCION = auto()    # Unidad compleja


class CategoriaGramatical(Enum):
    """Categorías gramaticales específicas"""
    # Núcleos
    SUSTANTIVO = auto()
    ADJETIVO = auto()
    ADVERBIO = auto()
    VERBO = auto()
    # Partículas
    PREPOSICION = auto()
    CONJUNCION = auto()
    PRONOMBRE = auto()
    ARTICULO = auto()
    DEMOSTRATIVO = auto()


class FuncRole(Enum):
    """Funciones sintácticas de partículas (P1.B.4)"""
    COPULA = auto()
    REGIMEN = auto()
    DETERMINACION = auto()
    NEXO_LOGICO = auto()
    MARCA_CASUAL = auto()
    ADVERBIAL = auto()
    RELATIVO = auto()


class ConsultaCodigo(Enum):
    """Códigos de consulta al usuario (P0.4)"""
    C1_CONFLICTO_PROTOCOLAR = auto()
    C2_COLLISION_DUDA = auto()
    C3_POSIBLE_LOCUCION = auto()
    C4_SINONIMIA = auto()
    C5_TOKEN_NO_REGISTRADO = auto()
    C6_ELEMENTO_DUDOSO = auto()
    C7_REGISTRO_INCOMPLETO = auto()


class FalloCritico(Enum):
    """Tipos de fallo crítico (P0.5)"""
    REGISTRO_INCOMPLETO = auto()
    SINONIMIA_NUCLEO = auto()
    TOKEN_NO_REGISTRADO = auto()


class Reason(Enum):
    """Razones para casos difíciles P6"""
    NO_ROOT = auto()
    GAP_DERIVATION = auto()
    COLLISION = auto()
    IDIOM = auto()


class ModoTransliteracion(Enum):
    """Modos de transliteración (P9.A.3)"""
    DESACTIVADO = auto()
    SELECTIVO = auto()
    COMPLETO = auto()


class NormaTransliteracion(Enum):
    """Normas de transliteración (P9.A.1)"""
    DIN_31635 = auto()  # Default
    ISO_233 = auto()
    SIMPLIFICADA = auto()


class ModoSalida(Enum):
    """Modos de salida (P0.13)"""
    BORRADOR = auto()
    FINAL = auto()


class DecisionOrigen(Enum):
    """Origen de una decisión (P0.12)"""
    USUARIO = auto()
    AUTOMATICA = auto()
    INFERIDA = auto()


class Operador(Enum):
    """Operadores tipográficos (P1.B.3)"""
    INYECCION = "[]"      # [texto]
    NULIDAD = "{}"        # {texto}
    TRANSLITERACION = "()"  # (texto)
    CITA = "«»"           # «texto»
    TITULO = "**"         # **texto**
    LOCUCION_GUION = "-"  # A-B-C


# Jerarquía etimológica (P4)
JERARQUIA_ETIMOLOGICA: List[str] = [
    "LENGUA_FUENTE",
    "LATINA", 
    "GRIEGA",
    "ARABE",
    "TECNICA"
]

# Whitelist de inyección (P7)
WHITELIST_INYECCION: Set[str] = {"hecho", "cosa", "algo", "que"}

# Blacklist de inyección (P7)
BLACKLIST_INYECCION: Set[str] = {
    "yo", "tú", "él", "ella", "nosotros", "vosotros", "ellos", "ellas",
    "me", "te", "se", "nos", "os"
}

# Sufijos por categoría (P9.B.2)
SUFIJOS = {
    CategoriaGramatical.SUSTANTIVO: {
        "abstracto": ["-idad", "-ción", "-miento"],
        "concreto": ["-a", "-o", "-e"],
        "agente": ["-dor", "-nte"]
    },
    CategoriaGramatical.ADJETIVO: {
        "cualidad": ["-al", "-ico", "-oso"],
        "participial": ["-ado", "-ido"]
    },
    CategoriaGramatical.VERBO: {
        "primera": ["-ar"],
        "derivado": ["-ificar", "-izar"]
    },
    CategoriaGramatical.ADVERBIO: {
        "modal": ["-mente"]
    }
}

# Jerarquía de autoridad (P2.1)
JERARQUIA_AUTORIDAD = ["P0", "P2", "P8", "P3", "P4", "P5", "P6", "P7", "P9", "P10"]

# Margen de decisión (P1.B.5)
MARGEN_VALORES = {
    "IDIOM": 6,
    "COLLISION": 5,
    "NO_ROOT": 4,
    "GAP_DERIVATION": 4,
    "TRANSLITERACION": 3,
    "MAPEO_1_1_ALT": 2,
    "MAPEO_1_1_DIRECTO": 1
}
