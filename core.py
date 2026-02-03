"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 4/13: Core - Control de Flujo (P3)
════════════════════════════════════════════════════════════════

INPUT:  Oración Fuente → Mtx_S (matriz de slots fuente)
OUTPUT: Mtx_T (matriz target renderizada)

ESTRUCTURAS:
  Slot_N[i] = {token_src, cat_src, morph_src, pos_index, status}
  Slot_P[i] = {token_src, cat_src, func_role, pos_index, status}
"""

from typing import List, Optional, Tuple, Any
from dataclasses import dataclass

from constants import TokenStatus, TokenCategoria, FalloCritico
from models import (
    SlotN, SlotP, MatrizFuente, MatrizTarget, 
    Locucion, ErrorCritico, CeldaMatriz
)
from glossary import Glosario, TokenNoRegistradoError


# ══════════════════════════════════════════════════════════════
# EXCEPCIONES
# ══════════════════════════════════════════════════════════════

class CoreError(Exception):
    """Error base del Core"""
    pass


class CohesionFailError(CoreError):
    """Fallo de cohesión"""
    pass


class IsomorfismoError(CoreError):
    """Error de isomorfismo"""
    pass


# ══════════════════════════════════════════════════════════════
# RESULTADO DE CORE
# ══════════════════════════════════════════════════════════════

@dataclass
class CoreResult:
    """Resultado del procesamiento Core"""
    exito: bool
    mtx_t: Optional[MatrizTarget] = None
    errores: List[ErrorCritico] = None
    mensaje: str = ""
    
    def __post_init__(self):
        if self.errores is None:
            self.errores = []


# ══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: CORE
# ══════════════════════════════════════════════════════════════

class Core:
    """
    P3: Control de Flujo Principal
    
    Orquesta todo el proceso de traducción:
      F1. Inicialización
      F2. Procesamiento de núcleos
      F3. Mapeo matricial
      F4. Procesamiento de partículas
      F5. Ajuste
      F6. Verificación de cohesión
      F7. Auditoría de isomorfismo
    """
    
    def __init__(self, glosario: Glosario):
        self.glosario = glosario
        self.mtx_s: Optional[MatrizFuente] = None
        self.mtx_t: Optional[MatrizTarget] = None
        
        # Procesadores externos (se inyectan)
        self._procesador_nucleos = None  # P4
        self._procesador_particulas = None  # P5
        self._reparador = None  # P7
        
        # Estado
        self._errores: List[ErrorCritico] = []
        self._fase_actual: str = "INICIO"
    
    def set_procesador_nucleos(self, procesador) -> None:
        """Inyectar procesador de núcleos (P4)"""
        self._procesador_nucleos = procesador
    
    def set_procesador_particulas(self, procesador) -> None:
        """Inyectar procesador de partículas (P5)"""
        self._procesador_particulas = procesador
    
    def set_reparador(self, reparador) -> None:
        """Inyectar reparador sintáctico (P7)"""
        self._reparador = reparador
    
    # ══════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL
    # ══════════════════════════════════════════════════════════
    
    def procesar_oracion(self, mtx_s: MatrizFuente) -> CoreResult:
        """
        Procesar una oración completa
        
        Args:
            mtx_s: Matriz fuente con la oración tokenizada
        
        Returns:
            CoreResult con matriz target o errores
        """
        self.mtx_s = mtx_s
        self._errores = []
        
        try:
            # F1. Inicialización
            self._fase_actual = "F1_INICIALIZACION"
            if not self._f1_inicializacion():
                return CoreResult(
                    exito=False,
                    errores=self._errores,
                    mensaje="Fallo en inicialización"
                )
            
            # F2. Procesamiento de núcleos
            self._fase_actual = "F2_NUCLEOS"
            if not self._f2_procesar_nucleos():
                return CoreResult(
                    exito=False,
                    mtx_t=self.mtx_t,
                    errores=self._errores,
                    mensaje="Fallo en procesamiento de núcleos"
                )
            
            # F3. Mapeo matricial
            self._fase_actual = "F3_MAPEO"
            self._f3_mapeo_matricial()
            
            # F4-F7. Procesar partículas con ciclo de cohesión
            self._fase_actual = "F4_F7_PARTICULAS"
            if not self._f4_f7_procesar_particulas():
                return CoreResult(
                    exito=False,
                    mtx_t=self.mtx_t,
                    errores=self._errores,
                    mensaje="Fallo en procesamiento de partículas"
                )
            
            # Éxito
            self._fase_actual = "CORE_OK"
            return CoreResult(
                exito=True,
                mtx_t=self.mtx_t,
                mensaje="[CORE-OK]"
            )
            
        except TokenNoRegistradoError as e:
            error = ErrorCritico(
                tipo=FalloCritico.TOKEN_NO_REGISTRADO,
                mensaje=str(e),
                contexto={"token": e.token, "posicion": e.posicion}
            )
            self._errores.append(error)
            return CoreResult(
                exito=False,
                mtx_t=self.mtx_t,
                errores=self._errores,
                mensaje="FALLO CRÍTICO: Token no registrado"
            )
        
        except Exception as e:
            return CoreResult(
                exito=False,
                mtx_t=self.mtx_t,
                errores=self._errores,
                mensaje=f"Error inesperado: {str(e)}"
            )
    
    # ══════════════════════════════════════════════════════════
    # F1. INICIALIZACIÓN
    # ══════════════════════════════════════════════════════════
    
    def _f1_inicializacion(self) -> bool:
        """
        F1. Inicialización (P3.F1)
        
        1.1. Generar Mtx_S desde oración fuente (ya viene generada)
        1.2. Clasificar tokens (ya clasificados en slots_n y slots_p)
        1.3. Constraint: Size(Mtx_T) == Size(Mtx_S) - INMUTABLE
        1.4. Verificar todos los tokens en glosario
        """
        # 1.3. Crear matriz target con mismo tamaño
        self.mtx_t = MatrizTarget(self.mtx_s.size())
        
        # 1.4. Verificar todos los tokens en glosario
        for celda in self.mtx_s.celdas:
            try:
                self.glosario.fase_b_verificar_existencia(
                    celda.token_src, 
                    celda.pos
                )
            except TokenNoRegistradoError:
                raise
        
        return True
    
    # ══════════════════════════════════════════════════════════
    # F2. PROCESAMIENTO DE NÚCLEOS
    # ══════════════════════════════════════════════════════════
    
    def _f2_procesar_nucleos(self) -> bool:
        """
        F2. Procesamiento de núcleos (P3.F2)
        
        Para cada Slot_N[i]:
          - Si BLOQUEADO → marcar para usar traducción de locución
          - Sino → ejecutar P4
        """
        if not self._procesador_nucleos:
            raise CoreError("Procesador de núcleos no configurado (P4)")
        
        for slot_n in self.mtx_s.slots_n:
            if slot_n.es_bloqueado():
                # Token pertenece a locución
                self.mtx_t.celdas[slot_n.pos_index].tipo = "parte_locucion"
                continue
            
            # Ejecutar P4
            resultado = self._procesador_nucleos.procesar(slot_n, self.glosario)
            
            if resultado.get("restart"):
                # P4 gestionó vía P6, usar valor registrado
                slot_n.token_tgt = self.glosario.obtener_traduccion(slot_n.token_src)
            elif resultado.get("bloqueado"):
                # Era parte de locución
                self.mtx_t.celdas[slot_n.pos_index].tipo = "parte_locucion"
            else:
                # Asignación normal
                slot_n.token_tgt = resultado.get("token_tgt")
                slot_n.morph_tgt = resultado.get("morph_tgt")
        
        return True
    
    # ══════════════════════════════════════════════════════════
    # F3. MAPEO MATRICIAL
    # ══════════════════════════════════════════════════════════
    
    def _f3_mapeo_matricial(self) -> None:
        """
        F3. Mapeo matricial (P3.F3)
        
        Para cada pos_index i:
          - Mtx_T[i].pos ← Mtx_S[i].pos (isomorfismo)
          - Si núcleo normal → asignar traducción
          - Si BLOQUEADO → insertar locución completa o marcar absorbido
          - Si partícula → [PENDIENTE]
        """
        for i, celda_s in enumerate(self.mtx_s.celdas):
            celda_t = self.mtx_t.celdas[i]
            celda_t.token_src = celda_s.token_src
            
            slot = celda_s.slot
            
            if slot is None:
                continue
            
            # Verificar si es parte de locución
            if slot.status == TokenStatus.BLOQUEADO:
                loc = self.mtx_s.obtener_locucion_en_pos(i)
                if loc:
                    if i == loc.primera_posicion():
                        # Primera posición: insertar traducción completa
                        celda_t.token_tgt = loc.tgt
                        celda_t.tipo = "locucion"
                    else:
                        # Posiciones siguientes: marcar absorbido
                        self.mtx_t.marcar_absorbido(i)
                continue
            
            # Token normal
            if isinstance(slot, SlotN):
                celda_t.token_tgt = slot.token_tgt
                celda_t.tipo = "normal"
            else:
                # Partícula - pendiente
                celda_t.tipo = "pendiente"
    
    # ══════════════════════════════════════════════════════════
    # F4-F7. PROCESAMIENTO DE PARTÍCULAS CON COHESIÓN
    # ══════════════════════════════════════════════════════════
    
    def _f4_f7_procesar_particulas(self) -> bool:
        """
        F4-F7. Procesar partículas con ciclo de cohesión
        
        Para cada partícula no bloqueada:
          F4. Obtener candidatos de P5
          F5. Ajustar con P7
          F6. Verificar cohesión
          F7. Auditar isomorfismo
        """
        if not self._procesador_particulas:
            raise CoreError("Procesador de partículas no configurado (P5)")
        
        for slot_p in self.mtx_s.slots_p:
            if slot_p.es_bloqueado():
                # Ya procesado como parte de locución
                continue
            
            # F4. Obtener candidatos
            candidatos = self._f4_obtener_candidatos(slot_p)
            
            if not candidatos:
                # Sin candidatos - marcar como problema
                self.mtx_t.celdas[slot_p.pos_index].token_tgt = slot_p.token_src
                self.mtx_t.celdas[slot_p.pos_index].tipo = "sin_traduccion"
                continue
            
            # Ciclo de cohesión
            exito = False
            for try_idx, candidato in enumerate(candidatos):
                # Asignar candidato
                self.mtx_t.celdas[slot_p.pos_index].token_tgt = candidato
                
                # F5. Ajuste (P7)
                if self._reparador:
                    self._f5_ajuste(slot_p.pos_index)
                
                # F6. Verificar cohesión
                if self._f6_verificar_cohesion(slot_p.pos_index):
                    # Registrar en glosario
                    self.glosario.fase_b_asignar(
                        slot_p.token_src,
                        candidato,
                        func_role=slot_p.func_role
                    )
                    exito = True
                    break
            
            if not exito:
                # FAIL CRÍTICO - usar primer candidato y marcar nulo
                self.mtx_t.celdas[slot_p.pos_index].token_tgt = candidatos[0]
                self.mtx_t.marcar_nulo(slot_p.pos_index)
            
            # F7. Auditoría de isomorfismo
            if not self._f7_auditoria_isomorfismo():
                # Corregir desplazamiento si es posible
                pass
        
        return True
    
    def _f4_obtener_candidatos(self, slot_p: SlotP) -> List[str]:
        """F4. Obtener candidatos de P5"""
        resultado = self._procesador_particulas.procesar(
            slot_p, 
            self.mtx_s,
            self.glosario
        )
        
        if resultado.get("bloqueado"):
            return []
        
        return resultado.get("candidatos", [])
    
    def _f5_ajuste(self, pos_index: int) -> None:
        """F5. Ajuste con P7"""
        if self._reparador:
            self._reparador.reparar(self.mtx_t, pos_index)
    
    def _f6_verificar_cohesion(self, pos_index: int) -> bool:
        """
        F6. Verificación de cohesión
        
        Verifica que la asignación actual produce una estructura coherente.
        Implementación simplificada.
        """
        # Verificación básica: token asignado existe
        token = self.mtx_t.obtener_token(pos_index)
        if not token:
            return False
        
        # Aquí iría lógica más compleja de cohesión gramatical
        # Por ahora, aceptamos si hay token
        return True
    
    def _f7_auditoria_isomorfismo(self) -> bool:
        """
        F7. Auditoría de isomorfismo
        
        Verificar: Mtx_T[i].pos == Mtx_S[i].pos (ignorando inyecciones)
        """
        return self.mtx_t.verificar_isomorfismo(self.mtx_s)
    
    # ══════════════════════════════════════════════════════════
    # UTILIDADES
    # ══════════════════════════════════════════════════════════
    
    def obtener_fase_actual(self) -> str:
        """Obtener fase actual del procesamiento"""
        return self._fase_actual
    
    def obtener_errores(self) -> List[ErrorCritico]:
        """Obtener errores acumulados"""
        return self._errores.copy()
    
    def serializar_resultado(self) -> str:
        """Serializar matriz target a texto"""
        if not self.mtx_t:
            return ""
        
        tokens = []
        for celda in self.mtx_t.celdas:
            if celda.es_absorbido():
                continue  # No renderizar
            
            if celda.token_tgt:
                if celda.es_inyeccion():
                    tokens.append(f"[{celda.token_tgt}]")
                elif celda.es_nulo():
                    tokens.append(f"{{{celda.token_tgt}}}")
                else:
                    tokens.append(celda.token_tgt)
        
        # Agregar inyecciones
        for iny in self.mtx_t.inyecciones:
            tokens.append(f"[{iny.token_tgt}]")
        
        return " ".join(tokens)


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA
# ══════════════════════════════════════════════════════════════

def crear_matriz_fuente(tokens: List[Tuple[str, Any]]) -> MatrizFuente:
    """
    Crear matriz fuente desde lista de tokens
    
    Args:
        tokens: Lista de (token_str, slot_object)
    """
    mtx = MatrizFuente()
    
    for i, (token, slot) in enumerate(tokens):
        celda = mtx.agregar_celda(token, i)
        
        if isinstance(slot, SlotN):
            mtx.agregar_slot_n(slot)
        elif isinstance(slot, SlotP):
            mtx.agregar_slot_p(slot)
    
    return mtx
