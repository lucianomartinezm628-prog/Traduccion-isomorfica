# ══════════════════════════════════════════════════════════════
# utils.py — UTILIDADES
# ══════════════════════════════════════════════════════════════

import re
import json
import os
from typing import List, Dict, Optional, Any, Tuple, Generator
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# TOKENIZADOR BÁSICO
# ──────────────────────────────────────────────────────────────

class Tokenizador:
    """
    Tokenizador básico para texto árabe y español
    """
    
    # Patrones de separación
    _PATRON_PALABRAS = re.compile(r'[\w\u0600-\u06FF\u0750-\u077F]+', re.UNICODE)
    _PATRON_PUNTUACION = re.compile(r'[.,;:!?¿¡«»"\'()\[\]{}–—]')
    
    @classmethod
    def tokenizar(cls, texto: str) -> List[str]:
        """Tokenizar texto en palabras"""
        return cls._PATRON_PALABRAS.findall(texto)
    
    @classmethod
    def tokenizar_con_posiciones(cls, texto: str) -> List[Tuple[str, int, int]]:
        """Tokenizar con posiciones (inicio, fin)"""
        resultado = []
        for match in cls._PATRON_PALABRAS.finditer(texto):
            resultado.append((match.group(), match.start(), match.end()))
        return resultado
    
    @classmethod
    def dividir_oraciones(cls, texto: str) -> List[str]:
        """Dividir texto en oraciones"""
        # Patrón simple: punto seguido de espacio y mayúscula
        oraciones = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚأإآ])', texto)
        return [o.strip() for o in oraciones if o.strip()]
    
    @classmethod
    def es_arabe(cls, texto: str) -> bool:
        """Verificar si el texto contiene caracteres árabes"""
        return bool(re.search(r'[\u0600-\u06FF]', texto))
    
    @classmethod
    def es_puntuacion(cls, token: str) -> bool:
        """Verificar si es puntuación"""
        return bool(cls._PATRON_PUNTUACION.fullmatch(token))


# ──────────────────────────────────────────────────────────────
# CLASIFICADOR GRAMATICAL BÁSICO
# ──────────────────────────────────────────────────────────────

from constants import TokenCategoria, CategoriaGramatical


class ClasificadorGramatical:
    """
    Clasificador gramatical básico
    En producción, se usaría un analizador morfológico completo
    """
    
    # Listas de partículas conocidas (árabe transliterado)
    _PREPOSICIONES = {
        "bi", "li", "fi", "min", "ʿan", "ʿalā", "ilā", "maʿa",
        "bayna", "fawqa", "taḥta", "ʿinda", "ladā", "ḥattā"
    }
    
    _CONJUNCIONES = {
        "wa", "fa", "aw", "am", "bal", "lākin", "inna", "anna",
        "li-anna", "ka-anna", "law", "in", "idhā", "lammā"
    }
    
    _PRONOMBRES = {
        "huwa", "hiya", "humā", "hum", "hunna",
        "anta", "anti", "antumā", "antum", "antunna",
        "anā", "naḥnu"
    }
    
    _ARTICULOS = {"al"}
    
    _RELATIVOS = {
        "alladhī", "allatī", "alladhīna", "allātī",
        "man", "mā", "ayy"
    }
    
    @classmethod
    def clasificar(cls, token: str) -> Tuple[TokenCategoria, CategoriaGramatical]:
        """
        Clasificar token en categoría y categoría gramatical
        
        Returns:
            Tupla (TokenCategoria, CategoriaGramatical)
        """
        token_lower = token.lower()
        
        # Partículas
        if token_lower in cls._PREPOSICIONES:
            return TokenCategoria.PARTICULA, CategoriaGramatical.PREPOSICION
        
        if token_lower in cls._CONJUNCIONES:
            return TokenCategoria.PARTICULA, CategoriaGramatical.CONJUNCION
        
        if token_lower in cls._PRONOMBRES:
            return TokenCategoria.PARTICULA, CategoriaGramatical.PRONOMBRE
        
        if token_lower in cls._ARTICULOS:
            return TokenCategoria.PARTICULA, CategoriaGramatical.ARTICULO
        
        if token_lower in cls._RELATIVOS:
            return TokenCategoria.PARTICULA, CategoriaGramatical.PRONOMBRE
        
        # Por defecto: núcleo (sustantivo)
        # En producción, se analizaría morfología
        return TokenCategoria.NUCLEO, CategoriaGramatical.SUSTANTIVO
    
    @classmethod
    def es_particula(cls, token: str) -> bool:
        """Verificar si es partícula"""
        cat, _ = cls.clasificar(token)
        return cat == TokenCategoria.PARTICULA
    
    @classmethod
    def es_nucleo(cls, token: str) -> bool:
        """Verificar si es núcleo"""
        cat, _ = cls.clasificar(token)
        return cat == TokenCategoria.NUCLEO


# ──────────────────────────────────────────────────────────────
# GESTOR DE ARCHIVOS
# ──────────────────────────────────────────────────────────────

class GestorArchivos:
    """
    Gestor de archivos para importación/exportación
    """
    
    @staticmethod
    def guardar_json(datos: Any, ruta: str) -> bool:
        """Guardar datos en JSON"""
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error al guardar JSON: {e}")
            return False
    
    @staticmethod
    def cargar_json(ruta: str) -> Optional[Any]:
        """Cargar datos de JSON"""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar JSON: {e}")
            return None
    
    @staticmethod
    def guardar_texto(texto: str, ruta: str) -> bool:
        """Guardar texto plano"""
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(texto)
            return True
        except Exception as e:
            print(f"Error al guardar texto: {e}")
            return False
    
    @staticmethod
    def cargar_texto(ruta: str) -> Optional[str]:
        """Cargar texto plano"""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error al cargar texto: {e}")
            return None
    
    @staticmethod
    def existe(ruta: str) -> bool:
        """Verificar si archivo existe"""
        return Path(ruta).exists()
    
    @staticmethod
    def crear_directorio(ruta: str) -> bool:
        """Crear directorio si no existe"""
        try:
            Path(ruta).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False


# ──────────────────────────────────────────────────────────────
# LOGGER
# ──────────────────────────────────────────────────────────────

class Logger:
    """
    Logger simple para el sistema
    """
    
    _NIVELES = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3,
        "CRITICAL": 4
    }
    
    def __init__(self, nombre: str = "Sistema", nivel: str = "INFO"):
        self.nombre = nombre
        self.nivel = self._NIVELES.get(nivel.upper(), 1)
        self._mensajes: List[Dict[str, Any]] = []
    
    def _log(self, nivel: str, mensaje: str) -> None:
        """Registrar mensaje"""
        if self._NIVELES.get(nivel, 0) >= self.nivel:
            entrada = {
                "timestamp": datetime.now().isoformat(),
                "nivel": nivel,
                "mensaje": mensaje
            }
            self._mensajes.append(entrada)
            print(f"[{nivel}] {self.nombre}: {mensaje}")
    
    def debug(self, mensaje: str) -> None:
        self._log("DEBUG", mensaje)
    
    def info(self, mensaje: str) -> None:
        self._log("INFO", mensaje)
    
    def warning(self, mensaje: str) -> None:
        self._log("WARNING", mensaje)
    
    def error(self, mensaje: str) -> None:
        self._log("ERROR", mensaje)
    
    def critical(self, mensaje: str) -> None:
        self._log("CRITICAL", mensaje)
    
    def obtener_historial(self) -> List[Dict[str, Any]]:
        return self._mensajes.copy()


# ──────────────────────────────────────────────────────────────
# VALIDADORES
# ──────────────────────────────────────────────────────────────

class Validadores:
    """
    Funciones de validación
    """
    
    @staticmethod
    def validar_texto_fuente(texto: str) -> Tuple[bool, str]:
        """Validar texto fuente"""
        if not texto or not texto.strip():
            return False, "Texto vacío"
        
        if len(texto) > 1000000:  # 1MB límite
            return False, "Texto demasiado largo"
        
        return True, "OK"
    
    @staticmethod
    def validar_token(token: str) -> Tuple[bool, str]:
        """Validar token"""
        if not token or not token.strip():
            return False, "Token vacío"
        
        if len(token) > 100:
            return False, "Token demasiado largo"
        
        return True, "OK"
    
    @staticmethod
    def validar_traduccion(traduccion: str) -> Tuple[bool, str]:
        """Validar traducción"""
        if not traduccion or not traduccion.strip():
            return False, "Traducción vacía"
        
        return True, "OK"
