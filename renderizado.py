"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 10/13: Renderizado - Pre y Post Procesamiento (P10)
════════════════════════════════════════════════════════════════

PROPÓSITO:
  Fase A: Preparar texto fuente para traducción (limpieza).
  Fase B: Preparar texto traducido para presentación (pulido).

ALCANCE:
  Solo aspectos formales y visuales.
  PROHIBIDO modificar contenido semántico.
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto

from constants import ModoTransliteracion, ModoSalida
from models import MatrizTarget, CeldaMatriz
from config import obtener_config


# ══════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════

class TipoElemento(Enum):
    """Tipos de elementos en el texto"""
    TITULO = auto()
    SUBTITULO = auto()
    CITA = auto()
    PARRAFO = auto()
    NORMAL = auto()


@dataclass
class ElementoTexto:
    """Elemento de texto con su tipo"""
    contenido: str
    tipo: TipoElemento
    posicion: int = 0


@dataclass
class ResultadoLimpieza:
    """Resultado de limpieza de texto"""
    texto_limpio: str
    elementos: List[ElementoTexto]
    ruido_eliminado: List[str]
    correcciones: List[Tuple[str, str]]
    exito: bool = True
    mensaje: str = ""


@dataclass
class ResultadoRenderizado:
    """Resultado de renderizado final"""
    texto_final: str
    operadores_aplicados: Dict[str, int]
    exito: bool = True
    mensaje: str = ""


# ══════════════════════════════════════════════════════════════
# FASE A: PRE-PROCESAMIENTO
# ══════════════════════════════════════════════════════════════

class PreProcesador:
    """
    P10.A: Pre-procesamiento (Limpieza del texto fuente)
    
    TRIGGER: Recepción de texto fuente, ANTES de P8
    INPUT:   Texto fuente crudo
    OUTPUT:  Texto fuente limpio → P8.A
    """
    
    # Patrones de ruido
    _PATRONES_RUIDO = [
        r'\[\d+\]',           # Referencias [1], [2], etc.
        r'\(\d+\)',           # Referencias (1), (2), etc.
        r'^\s*\d+\s*$',       # Números de página solos
        r'[-=]{3,}',          # Líneas de separación
        r'\[sic\]',           # Marcas editoriales
        r'\[N\.\s*del\s*E\.\]',  # Notas del editor
        r'^\s*[\*\•\-]\s*$',  # Bullets solos
    ]
    
    # Patrones OCR comunes
    _CORRECCIONES_OCR = [
        (r'\b1a\b', 'la'),
        (r'\b0\b(?=[a-záéíóú])', 'o'),
        (r'\brn\b', 'm'),      # rn → m
        (r'\bii\b', 'ü'),      # ii → ü (a veces)
        (r'\s{2,}', ' '),      # Múltiples espacios
        (r'\n{3,}', '\n\n'),   # Múltiples saltos
    ]
    
    def __init__(self):
        self._ruido_eliminado: List[str] = []
        self._correcciones: List[Tuple[str, str]] = []
    
    def procesar(self, texto_crudo: str) -> ResultadoLimpieza:
        """
        Procesar texto fuente
        
        Args:
            texto_crudo: Texto fuente sin procesar
        
        Returns:
            ResultadoLimpieza con texto limpio y metadata
        """
        self._ruido_eliminado = []
        self._correcciones = []
        
        # A1. Filtro de ruido
        texto = self._a1_filtrar_ruido(texto_crudo)
        
        # A2. Corrección de errores no-semánticos
        texto = self._a2_corregir_errores(texto)
        
        # A3. Normalización
        texto = self._a3_normalizar(texto)
        
        # A4. Identificar elementos estructurales
        elementos = self._a4_identificar_elementos(texto)
        
        return ResultadoLimpieza(
            texto_limpio=texto,
            elementos=elementos,
            ruido_eliminado=self._ruido_eliminado,
            correcciones=self._correcciones,
            mensaje="Limpieza completada"
        )
    
    def _a1_filtrar_ruido(self, texto: str) -> str:
        """A1. Filtro de ruido"""
        for patron in self._PATRONES_RUIDO:
            matches = re.findall(patron, texto, re.MULTILINE)
            for match in matches:
                self._ruido_eliminado.append(match)
            texto = re.sub(patron, '', texto, flags=re.MULTILINE)
        
        return texto
    
    def _a2_corregir_errores(self, texto: str) -> str:
        """A2. Corrección de errores no-semánticos (OCR)"""
        for patron, reemplazo in self._CORRECCIONES_OCR:
            matches = re.findall(patron, texto)
            if matches:
                self._correcciones.append((patron, reemplazo))
            texto = re.sub(patron, reemplazo, texto)
        
        return texto
    
    def _a3_normalizar(self, texto: str) -> str:
        """A3. Normalización"""
        # UTF-8 (Python ya maneja esto)
        
        # Un espacio entre palabras
        texto = re.sub(r' +', ' ', texto)
        
        # Normalizar saltos de línea
        texto = re.sub(r'\r\n', '\n', texto)
        texto = re.sub(r'\r', '\n', texto)
        
        # Preservar párrafos (doble salto)
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        
        # Limpiar espacios al inicio/final de líneas
        lineas = texto.split('\n')
        lineas = [linea.strip() for linea in lineas]
        texto = '\n'.join(lineas)
        
        return texto
    
    def _a4_identificar_elementos(self, texto: str) -> List[ElementoTexto]:
        """A4. Identificar elementos estructurales"""
        elementos = []
        parrafos = texto.split('\n\n')
        
        for i, parrafo in enumerate(parrafos):
            parrafo = parrafo.strip()
            if not parrafo:
                continue
            
            tipo = self._clasificar_elemento(parrafo)
            elementos.append(ElementoTexto(
                contenido=parrafo,
                tipo=tipo,
                posicion=i
            ))
        
        return elementos
    
    def _clasificar_elemento(self, texto: str) -> TipoElemento:
        """Clasificar tipo de elemento"""
        # Título: línea corta, sin punto final, posiblemente mayúsculas
        if len(texto) < 100 and not texto.endswith('.'):
            if texto.isupper() or texto.istitle():
                return TipoElemento.TITULO
        
        # Subtítulo: similar pero más largo
        if len(texto) < 150 and not texto.endswith('.'):
            return TipoElemento.SUBTITULO
        
        # Cita: comienza con comillas o guiones
        if texto.startswith(('"', '«', '—', '-')):
            return TipoElemento.CITA
        
        return TipoElemento.PARRAFO


# ══════════════════════════════════════════════════════════════
# FASE B: POST-PROCESAMIENTO
# ══════════════════════════════════════════════════════════════

class PostProcesador:
    """
    P10.B: Post-procesamiento (Presentación del texto traducido)
    
    TRIGGER: P3 completa con [CORE-OK]
    INPUT:   Mtx_T (matriz traducida y verificada)
    OUTPUT:  Texto final → Usuario
    """
    
    def __init__(self):
        self._operadores_aplicados: Dict[str, int] = {
            "inyeccion": 0,
            "nulo": 0,
            "cita": 0,
            "titulo": 0,
            "locucion": 0,
            "polivalencia": 0
        }
    
    def procesar(self, mtx_t: MatrizTarget,
                 elementos: List[ElementoTexto] = None) -> ResultadoRenderizado:
        """
        Procesar matriz target para presentación
        
        Args:
            mtx_t: Matriz target traducida
            elementos: Elementos estructurales (opcional)
        
        Returns:
            ResultadoRenderizado con texto final
        """
        self._operadores_aplicados = {k: 0 for k in self._operadores_aplicados}
        
        # B1. Serialización
        tokens = self._b1_serializar(mtx_t)
        
        # B2. Aplicación de operadores
        tokens = self._b2_aplicar_operadores(tokens, mtx_t)
        
        # B3. Transliteración inline
        tokens = self._b3_transliteracion_inline(tokens)
        
        # B4. Mayúsculas
        texto = self._b4_aplicar_mayusculas(tokens)
        
        # B5. Corrección ortográfica
        texto = self._b5_correccion_ortografica(texto)
        
        # B6. Formato de estructura
        if elementos:
            texto = self._b6_formato_estructura(texto, elementos)
        
        # B7. Verificación final
        texto = self._b7_verificacion_final(texto)
        
        return ResultadoRenderizado(
            texto_final=texto,
            operadores_aplicados=self._operadores_aplicados,
            mensaje="Renderizado completado"
        )
    
    def _b1_serializar(self, mtx_t: MatrizTarget) -> List[str]:
        """B1. Serialización de matriz a tokens"""
        tokens = []
        
        for celda in mtx_t.celdas:
            # Saltar tokens absorbidos
            if celda.es_absorbido():
                continue
            
            if celda.token_tgt:
                tokens.append(celda.token_tgt)
        
        # Agregar inyecciones
        for iny in mtx_t.inyecciones:
            if iny.token_tgt:
                tokens.append(f"[{iny.token_tgt}]")
        
        return tokens
    
    def _b2_aplicar_operadores(self, tokens: List[str],
                                mtx_t: MatrizTarget) -> List[str]:
        """B2. Aplicación de operadores tipográficos"""
        resultado = []
        
        for i, token in enumerate(tokens):
            # Ya tiene formato de inyección
            if token.startswith('[') and token.endswith(']'):
                self._operadores_aplicados["inyeccion"] += 1
                resultado.append(token)
                continue
            
            # Verificar tipo de celda
            celda = mtx_t.celdas[i] if i < len(mtx_t.celdas) else None
            
            if celda:
                if celda.es_nulo():
                    self._operadores_aplicados["nulo"] += 1
                    resultado.append(f"{{{token}}}")
                elif celda.tipo == "locucion":
                    self._operadores_aplicados["locucion"] += 1
                    resultado.append(token)  # Ya viene con guiones
                elif celda.tipo == "cita":
                    self._operadores_aplicados["cita"] += 1
                    resultado.append(f"«{token}»")
                elif celda.tipo == "titulo":
                    self._operadores_aplicados["titulo"] += 1
                    resultado.append(f"**{token}**")
                else:
                    resultado.append(token)
            else:
                resultado.append(token)
        
        return resultado
    
    def _b3_transliteracion_inline(self, tokens: List[str]) -> List[str]:
        """B3. Transliteración inline según modo"""
        config = obtener_config()
        
        # Solo aplicar si modo es SELECTIVO o COMPLETO
        if config.modo_transliteracion == ModoTransliteracion.DESACTIVADO:
            return tokens
        
        # La transliteración inline ya se maneja en formacion.py
        return tokens
    
    def _b4_aplicar_mayusculas(self, tokens: List[str]) -> str:
        """B4. Lógica de mayúsculas"""
        if not tokens:
            return ""
        
        # Unir tokens
        texto = ' '.join(tokens)
        
        # Dividir en oraciones
        oraciones = re.split(r'([.!?]+\s*)', texto)
        resultado = []
        
        for i, parte in enumerate(oraciones):
            if not parte:
                continue
            
            # Si es puntuación, agregar directamente
            if re.match(r'^[.!?]+\s*$', parte):
                resultado.append(parte)
                continue
            
            # Capitalizar primera palabra de oración
            parte = parte.strip()
            if parte and resultado:
                # No es primera oración
                if resultado[-1].rstrip().endswith(('.', '!', '?')):
                    parte = parte[0].upper() + parte[1:] if len(parte) > 1 else parte.upper()
            elif parte:
                # Primera oración
                parte = parte[0].upper() + parte[1:] if len(parte) > 1 else parte.upper()
            
            resultado.append(parte)
        
        texto = ''.join(resultado)
        
        # PROHIBIDO: mayúsculas en sustantivos comunes y conceptos abstractos
        # (No aplicamos cambios adicionales - se asume que el texto viene bien)
        
        return texto
    
    def _b5_correccion_ortografica(self, texto: str) -> str:
        """B5. Corrección ortográfica básica"""
        # Espacios antes de puntuación
        texto = re.sub(r'\s+([.,;:!?])', r'\1', texto)
        
        # Espacio después de puntuación
        texto = re.sub(r'([.,;:!?])(?=[^\s\d])', r'\1 ', texto)
        
        # Dobles espacios
        texto = re.sub(r'  +', ' ', texto)
        
        # PROHIBIDO corregir: neologismos, agramaticalidades del isomorfismo
        
        return texto
    
    def _b6_formato_estructura(self, texto: str,
                                elementos: List[ElementoTexto]) -> str:
        """B6. Formato de estructura"""
        # Aplicar formato según elementos
        lineas = texto.split('\n')
        resultado = []
        
        for linea in lineas:
            linea_limpia = linea.strip()
            
            # Buscar si corresponde a título/subtítulo
            for elem in elementos:
                if elem.tipo == TipoElemento.TITULO:
                    if linea_limpia and not linea_limpia.startswith('**'):
                        # Podría ser título
                        pass
                elif elem.tipo == TipoElemento.CITA:
                    if not linea_limpia.startswith('«'):
                        pass
            
            resultado.append(linea)
        
        return '\n'.join(resultado)
    
    def _b7_verificacion_final(self, texto: str) -> str:
        """B7. Verificación final"""
        # Verificar corchetes y llaves cerrados
        if texto.count('[') != texto.count(']'):
            # Intentar corregir
            pass
        
        if texto.count('{') != texto.count('}'):
            pass
        
        # Verificar UTF-8 (Python maneja esto automáticamente)
        
        # Limpiar espacios finales
        texto = texto.strip()
        
        return texto
    
    def serializar_modo_borrador(self, mtx_t: MatrizTarget) -> str:
        """Serializar en modo borrador (con marcas de debug)"""
        lineas = []
        
        for i, celda in enumerate(mtx_t.celdas):
            marca = ""
            if celda.es_absorbido():
                marca = "[ABS]"
            elif celda.es_nulo():
                marca = "[NUL]"
            elif celda.es_inyeccion():
                marca = "[INY]"
            
            lineas.append(f"{i}: {celda.token_src} → {celda.token_tgt} {marca}")
        
        return '\n'.join(lineas)


# ══════════════════════════════════════════════════════════════
# CONTROLADOR DE RENDERIZADO
# ══════════════════════════════════════════════════════════════

class ControladorRenderizado:
    """
    Controlador principal de renderizado (P10)
    
    Integra pre y post procesamiento
    """
    
    def __init__(self):
        self.pre_procesador = PreProcesador()
        self.post_procesador = PostProcesador()
        self._elementos: List[ElementoTexto] = []
    
    def limpiar_texto(self, texto_crudo: str) -> ResultadoLimpieza:
        """Fase A: Limpiar texto fuente"""
        resultado = self.pre_procesador.procesar(texto_crudo)
        self._elementos = resultado.elementos
        return resultado
    
    def renderizar(self, mtx_t: MatrizTarget) -> ResultadoRenderizado:
        """Fase B: Renderizar texto traducido"""
        return self.post_procesador.procesar(mtx_t, self._elementos)
    
    def renderizar_borrador(self, mtx_t: MatrizTarget) -> str:
        """Renderizar en modo borrador"""
        return self.post_procesador.serializar_modo_borrador(mtx_t)
    
    def obtener_texto_final(self, mtx_t: MatrizTarget) -> str:
        """Obtener texto final según modo configurado"""
        config = obtener_config()
        
        if config.modo_salida == ModoSalida.BORRADOR:
            return self.renderizar_borrador(mtx_t)
        else:
            resultado = self.renderizar(mtx_t)
            return resultado.texto_final


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════

# Instancia global
_controlador_renderizado = ControladorRenderizado()


def obtener_controlador_renderizado() -> ControladorRenderizado:
    """Obtener controlador de renderizado"""
    return _controlador_renderizado


def limpiar_texto(texto: str) -> str:
    """Función de conveniencia para limpiar texto"""
    resultado = _controlador_renderizado.limpiar_texto(texto)
    return resultado.texto_limpio


def renderizar_matriz(mtx_t: MatrizTarget) -> str:
    """Función de conveniencia para renderizar matriz"""
    return _controlador_renderizado.obtener_texto_final(mtx_t)
