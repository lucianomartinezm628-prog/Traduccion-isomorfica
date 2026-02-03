"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 8/13: Reparación Sintáctica (P7)
════════════════════════════════════════════════════════════════

TRIGGER: P3.F5 (Ajuste)
INPUT:   Mtx_T, pos_index (slot actual)
OUTPUT:  REPAIR-OK → P3.F6

AXIOMA DE INMUNIDAD:
  T ∈ Source ⇒ T ∈ Target
  La presencia en fuente valida permanencia en target, incluso si agramatical.

OPERADORES:
  OP_INSERT(T)       → [T]  (inyección)
  OP_INSERT_PUNCT(P) → , ;  (puntuación)
  OP_ADJUST_MORPH(T) → género/número/persona
  OP_NULL(T)         → {T}  (nulidad)
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass
from enum import Enum, auto

from constants import WHITELIST_INYECCION, BLACKLIST_INYECCION
from models import MatrizTarget, CeldaMatriz


# ══════════════════════════════════════════════════════════════
# ENUMS Y CONSTANTES
# ══════════════════════════════════════════════════════════════

class TipoReparacion(Enum):
    """Tipos de reparación aplicada"""
    BYPASS = auto()
    INYECCION = auto()
    PUNTUACION = auto()
    MORFOLOGIA = auto()
    NULIDAD_LOCAL = auto()
    NULIDAD_REGIMEN = auto()


class ResultadoReparacion(Enum):
    """Resultado de intento de reparación"""
    OK = auto()
    FAIL = auto()
    FORZADO = auto()


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════

@dataclass
class AccionReparacion:
    """Acción de reparación realizada"""
    tipo: TipoReparacion
    posicion: int
    token_afectado: str
    token_nuevo: Optional[str] = None
    descripcion: str = ""


@dataclass
class ResultadoReparador:
    """Resultado del proceso de reparación"""
    exito: bool
    acciones: List[AccionReparacion]
    mensaje: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exito": self.exito,
            "acciones": [
                {
                    "tipo": a.tipo.name,
                    "posicion": a.posicion,
                    "token_afectado": a.token_afectado,
                    "token_nuevo": a.token_nuevo,
                    "descripcion": a.descripcion
                }
                for a in self.acciones
            ],
            "mensaje": self.mensaje
        }


# ══════════════════════════════════════════════════════════════
# OPERADORES DE REPARACIÓN
# ══════════════════════════════════════════════════════════════

class Operadores:
    """
    Operadores de reparación (P7)
    """
    
    @staticmethod
    def op_insert(mtx_t: MatrizTarget, token: str, pos_referencia: int) -> bool:
        """
        OP_INSERT: Insertar soporte léxico [T]
        
        Solo tokens de WHITELIST, nunca de BLACKLIST
        """
        if token not in WHITELIST_INYECCION:
            return False
        if token in BLACKLIST_INYECCION:
            return False
        
        mtx_t.insertar_inyeccion(token, pos_referencia)
        return True
    
    @staticmethod
    def op_insert_punct(mtx_t: MatrizTarget, puntuacion: str, pos: int) -> bool:
        """
        OP_INSERT_PUNCT: Insertar puntuación
        
        Solo , o ;
        """
        if puntuacion not in [",", ";"]:
            return False
        
        celda = mtx_t.celdas[pos] if pos < len(mtx_t.celdas) else None
        if celda and celda.token_tgt:
            celda.token_tgt = celda.token_tgt + puntuacion
        
        return True
    
    @staticmethod
    def op_adjust_morph(celda: CeldaMatriz, ajuste: Dict[str, str]) -> bool:
        """
        OP_ADJUST_MORPH: Ajustar flexión
        
        Ajustes posibles: género, número, persona
        """
        if not celda.token_tgt:
            return False
        
        token = celda.token_tgt
        
        # Ajuste de género
        if "genero" in ajuste:
            token = Operadores._ajustar_genero(token, ajuste["genero"])
        
        # Ajuste de número
        if "numero" in ajuste:
            token = Operadores._ajustar_numero(token, ajuste["numero"])
        
        # Ajuste de persona
        if "persona" in ajuste:
            token = Operadores._ajustar_persona(token, ajuste["persona"])
        
        celda.token_tgt = token
        return True
    
    @staticmethod
    def op_null(mtx_t: MatrizTarget, pos: int) -> bool:
        """
        OP_NULL: Marcar como nulo {T}
        """
        if pos >= len(mtx_t.celdas):
            return False
        
        mtx_t.marcar_nulo(pos)
        return True
    
    @staticmethod
    def _ajustar_genero(token: str, genero: str) -> str:
        """Ajustar género del token"""
        if genero == "femenino":
            if token.endswith("o"):
                return token[:-1] + "a"
            elif token.endswith("or"):
                return token + "a"
        elif genero == "masculino":
            if token.endswith("a") and not token.endswith(("ma", "ta", "ía")):
                return token[:-1] + "o"
        return token
    
    @staticmethod
    def _ajustar_numero(token: str, numero: str) -> str:
        """Ajustar número del token"""
        if numero == "plural":
            if token.endswith(("a", "e", "i", "o", "u")):
                return token + "s"
            elif token.endswith("z"):
                return token[:-1] + "ces"
            else:
                return token + "es"
        elif numero == "singular":
            if token.endswith("es") and len(token) > 3:
                return token[:-2]
            elif token.endswith("s") and len(token) > 2:
                return token[:-1]
        return token
    
    @staticmethod
    def _ajustar_persona(token: str, persona: str) -> str:
        """Ajustar persona del token (verbos)"""
        # Implementación simplificada
        return token


# ══════════════════════════════════════════════════════════════
# VERIFICADOR DE COHESIÓN
# ══════════════════════════════════════════════════════════════

class VerificadorCohesion:
    """
    Verificador de cohesión gramatical básica
    """
    
    @staticmethod
    def verificar(mtx_t: MatrizTarget, pos: int) -> bool:
        """
        Verificar cohesión en posición dada
        
        Verifica:
        - Token existe
        - Concordancia básica con adyacentes
        """
        if pos >= len(mtx_t.celdas):
            return False
        
        celda = mtx_t.celdas[pos]
        
        # Token debe existir
        if not celda.token_tgt:
            return False
        
        # Si es absorbido, ok
        if celda.es_absorbido():
            return True
        
        # Verificar concordancia con adyacentes (simplificado)
        return VerificadorCohesion._verificar_concordancia(mtx_t, pos)
    
    @staticmethod
    def _verificar_concordancia(mtx_t: MatrizTarget, pos: int) -> bool:
        """Verificar concordancia básica"""
        # Implementación simplificada - siempre ok
        # En producción, verificaría género/número con adyacentes
        return True
    
    @staticmethod
    def identificar_problema(mtx_t: MatrizTarget, pos: int) -> Optional[str]:
        """Identificar tipo de problema de cohesión"""
        if pos >= len(mtx_t.celdas):
            return "POSICION_INVALIDA"
        
        celda = mtx_t.celdas[pos]
        
        if not celda.token_tgt:
            return "TOKEN_FALTANTE"
        
        # Aquí se implementarían más verificaciones
        return None


# ══════════════════════════════════════════════════════════════
# REPARADOR SINTÁCTICO (P7)
# ══════════════════════════════════════════════════════════════

class ReparadorSintactico:
    """
    P7: Reparación Sintáctica
    
    Fases (acumulativas):
      F1. BYPASS: Token ∈ fuente → FORCE RENDER
      F2. SOPORTE: Inyección + puntuación
      F3. MORFOLOGÍA: Ajustar flexión
      F4. NULIDAD LOCAL: {T_problemático}
      F5. NULIDAD RÉGIMEN: {régimen_completo}
      F6. LIMPIEZA
    """
    
    def __init__(self):
        self.operadores = Operadores()
        self.verificador = VerificadorCohesion()
        self._acciones: List[AccionReparacion] = []
    
    def reparar(self, mtx_t: MatrizTarget, pos: int,
                token_fuente: bool = True) -> ResultadoReparador:
        """
        Reparar posición en matriz target
        
        Args:
            mtx_t: Matriz target
            pos: Posición a reparar
            token_fuente: Si el token existe en fuente
        
        Returns:
            ResultadoReparador con acciones realizadas
        """
        self._acciones = []
        
        # F1. BYPASS
        if self._f1_bypass(mtx_t, pos, token_fuente):
            return self._resultado_ok("BYPASS")
        
        # F2. SOPORTE
        if self._f2_soporte(mtx_t, pos):
            return self._resultado_ok("SOPORTE")
        
        # F3. MORFOLOGÍA
        if self._f3_morfologia(mtx_t, pos):
            return self._resultado_ok("MORFOLOGÍA")
        
        # F4. NULIDAD LOCAL
        if self._f4_nulidad_local(mtx_t, pos):
            return self._resultado_ok("NULIDAD_LOCAL")
        
        # F5. NULIDAD RÉGIMEN
        if self._f5_nulidad_regimen(mtx_t, pos):
            return self._resultado_ok("NULIDAD_RÉGIMEN (forzado)")
        
        # F6. LIMPIEZA (siempre se ejecuta)
        self._f6_limpieza(mtx_t)
        
        return ResultadoReparador(
            exito=True,
            acciones=self._acciones,
            mensaje="REPAIR-OK"
        )
    
    # ══════════════════════════════════════════════════════════
    # F1. BYPASS
    # ══════════════════════════════════════════════════════════
    
    def _f1_bypass(self, mtx_t: MatrizTarget, pos: int, token_fuente: bool) -> bool:
        """
        F1. BYPASS (Inmunidad)
        
        Si token ∈ fuente → FORCE RENDER → OK
        Si token es [ABSORBIDO] → ya procesado → OK
        """
        celda = mtx_t.celdas[pos] if pos < len(mtx_t.celdas) else None
        
        if not celda:
            return False
        
        # Token absorbido (parte de locución)
        if celda.es_absorbido():
            self._registrar_accion(
                TipoReparacion.BYPASS, pos,
                celda.token_src, None,
                "Token absorbido por locución"
            )
            return True
        
        # Token existe en fuente → forzar renderizado
        if token_fuente and celda.token_tgt:
            self._registrar_accion(
                TipoReparacion.BYPASS, pos,
                celda.token_tgt, None,
                "Token de fuente - renderizado forzado"
            )
            return True
        
        return False
    
    # ══════════════════════════════════════════════════════════
    # F2. SOPORTE
    # ══════════════════════════════════════════════════════════
    
    def _f2_soporte(self, mtx_t: MatrizTarget, pos: int) -> bool:
        """
        F2. SOPORTE (Inyección + Puntuación)
        
        Herramientas: OP_INSERT, OP_INSERT_PUNCT
        """
        # Verificar si necesita soporte
        problema = self.verificador.identificar_problema(mtx_t, pos)
        
        if not problema:
            return True  # No hay problema
        
        # Intentar inyección de soporte
        if problema == "FALTA_SOPORTE":
            for token_soporte in WHITELIST_INYECCION:
                if self.operadores.op_insert(mtx_t, token_soporte, pos):
                    self._registrar_accion(
                        TipoReparacion.INYECCION, pos,
                        "", token_soporte,
                        f"Inyección de soporte: [{token_soporte}]"
                    )
                    if self.verificador.verificar(mtx_t, pos):
                        return True
        
        # Intentar puntuación
        celda = mtx_t.celdas[pos] if pos < len(mtx_t.celdas) else None
        if celda and celda.token_tgt:
            # Verificar si contexto requiere puntuación
            if self._requiere_puntuacion(mtx_t, pos):
                if self.operadores.op_insert_punct(mtx_t, ",", pos):
                    self._registrar_accion(
                        TipoReparacion.PUNTUACION, pos,
                        celda.token_tgt, celda.token_tgt + ",",
                        "Inyección de puntuación"
                    )
                    if self.verificador.verificar(mtx_t, pos):
                        return True
        
        return False
    
    def _requiere_puntuacion(self, mtx_t: MatrizTarget, pos: int) -> bool:
        """Verificar si la posición requiere puntuación"""
        # Heurística: antes de conjunciones o subordinantes
        if pos + 1 < len(mtx_t.celdas):
            siguiente = mtx_t.celdas[pos + 1].token_tgt
            if siguiente and siguiente.lower() in ["que", "pero", "sino", "aunque"]:
                return True
        return False
    
    # ══════════════════════════════════════════════════════════
    # F3. MORFOLOGÍA
    # ══════════════════════════════════════════════════════════
    
    def _f3_morfologia(self, mtx_t: MatrizTarget, pos: int) -> bool:
        """
        F3. MORFOLOGÍA
        
        Herramientas: OP_ADJUST_MORPH + herramientas F2
        """
        celda = mtx_t.celdas[pos] if pos < len(mtx_t.celdas) else None
        
        if not celda or not celda.token_tgt:
            return False
        
        # Detectar ajuste necesario
        ajuste = self._detectar_ajuste_necesario(mtx_t, pos)
        
        if ajuste:
            token_original = celda.token_tgt
            if self.operadores.op_adjust_morph(celda, ajuste):
                self._registrar_accion(
                    TipoReparacion.MORFOLOGIA, pos,
                    token_original, celda.token_tgt,
                    f"Ajuste morfológico: {ajuste}"
                )
                if self.verificador.verificar(mtx_t, pos):
                    return True
        
        return False
    
    def _detectar_ajuste_necesario(self, mtx_t: MatrizTarget, pos: int) -> Optional[Dict[str, str]]:
        """Detectar qué ajuste morfológico es necesario"""
        # Implementación simplificada
        # En producción, analizaría concordancia con adyacentes
        return None
    
    # ══════════════════════════════════════════════════════════
    # F4. NULIDAD LOCAL
    # ══════════════════════════════════════════════════════════
    
    def _f4_nulidad_local(self, mtx_t: MatrizTarget, pos: int) -> bool:
        """
        F4. NULIDAD LOCAL
        
        Herramientas: OP_NULL + herramientas anteriores
        Token o fragmento mínimo bloquea el régimen
        """
        celda = mtx_t.celdas[pos] if pos < len(mtx_t.celdas) else None
        
        if not celda:
            return False
        
        # Marcar como nulo
        token_original = celda.token_tgt
        if self.operadores.op_null(mtx_t, pos):
            self._registrar_accion(
                TipoReparacion.NULIDAD_LOCAL, pos,
                token_original, f"{{{token_original}}}",
                "Nulidad local - token problemático"
            )
            return True
        
        return False
    
    # ══════════════════════════════════════════════════════════
    # F5. NULIDAD RÉGIMEN
    # ══════════════════════════════════════════════════════════
    
    def _f5_nulidad_regimen(self, mtx_t: MatrizTarget, pos: int) -> bool:
        """
        F5. NULIDAD RÉGIMEN
        
        Último recurso: anular régimen completo
        """
        # Identificar régimen (simplificado: solo la posición actual)
        celda = mtx_t.celdas[pos] if pos < len(mtx_t.celdas) else None
        
        if not celda:
            return False
        
        token_original = celda.token_tgt
        if self.operadores.op_null(mtx_t, pos):
            self._registrar_accion(
                TipoReparacion.NULIDAD_REGIMEN, pos,
                token_original, f"{{{token_original}}}",
                "Nulidad de régimen - cierre forzado"
            )
            return True
        
        return False
    
    # ══════════════════════════════════════════════════════════
    # F6. LIMPIEZA
    # ══════════════════════════════════════════════════════════
    
    def _f6_limpieza(self, mtx_t: MatrizTarget) -> None:
        """
        F6. LIMPIEZA
        
        - Eliminar residuos de reparación
        - Eliminar duplicados (inyección redundante)
        - Tokens [ABSORBIDO] no se renderizan
        """
        tokens_fuente = set()
        
        # Recopilar tokens de fuente
        for celda in mtx_t.celdas:
            if celda.token_src:
                tokens_fuente.add(celda.token_src.lower())
        
        # Limpiar inyecciones duplicadas
        inyecciones_limpias = []
        for iny in mtx_t.inyecciones:
            # Si el token inyectado ya existe en fuente, eliminar
            if iny.token_tgt.lower() not in tokens_fuente:
                inyecciones_limpias.append(iny)
        
        mtx_t.inyecciones = inyecciones_limpias
    
    # ══════════════════════════════════════════════════════════
    # UTILIDADES
    # ══════════════════════════════════════════════════════════
    
    def _registrar_accion(self, tipo: TipoReparacion, pos: int,
                          token_afectado: str, token_nuevo: Optional[str],
                          descripcion: str) -> None:
        """Registrar acción de reparación"""
        self._acciones.append(AccionReparacion(
            tipo=tipo,
            posicion=pos,
            token_afectado=token_afectado,
            token_nuevo=token_nuevo,
            descripcion=descripcion
        ))
    
    def _resultado_ok(self, fase: str) -> ResultadoReparador:
        """Crear resultado exitoso"""
        return ResultadoReparador(
            exito=True,
            acciones=self._acciones,
            mensaje=f"REPAIR-OK ({fase})"
        )
    
    def obtener_acciones(self) -> List[AccionReparacion]:
        """Obtener acciones realizadas"""
        return self._acciones.copy()


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA
# ══════════════════════════════════════════════════════════════

def crear_reparador() -> ReparadorSintactico:
    """Crear instancia de reparador"""
    return ReparadorSintactico()


def reparar_posicion(mtx_t: MatrizTarget, pos: int,
                     token_fuente: bool = True) -> ResultadoReparador:
    """Función de conveniencia para reparar una posición"""
    reparador = ReparadorSintactico()
    return reparador.reparar(mtx_t, pos, token_fuente)
