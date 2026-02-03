# config.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

# --- ESTA ES LA LÍNEA QUE TE FALTA ---
from constants import ModoTransliteracion, NormaTransliteracion, ModoSalida
# -------------------------------------

@dataclass
class ReglaUsuario:
    """Regla personalizada del usuario (P0.3)"""
    tipo: str  # "siempre", "nunca", "cuando"
    condicion: Optional[str]
    accion: str
    timestamp: datetime = field(default_factory=datetime.now)
    activa: bool = True

@dataclass
class ConfiguracionSistema:
    """Configuración global del sistema"""
    
    # Modos (Aquí es donde daba el error si no importas las constantes arriba)
    modo_transliteracion: ModoTransliteracion = ModoTransliteracion.DESACTIVADO
    norma_transliteracion: NormaTransliteracion = NormaTransliteracion.DIN_31635
    modo_salida: ModoSalida = ModoSalida.BORRADOR
    
    # Reglas de usuario
    reglas_permanentes: List[ReglaUsuario] = field(default_factory=list)
    reglas_sesion: List[ReglaUsuario] = field(default_factory=list)
    
    # Lista de locuciones predefinidas (opcional)
    locuciones_predefinidas: List[str] = field(default_factory=list)
    
    # Ruta de glosario previo (para importación automática)
    ruta_glosario_previo: Optional[str] = None
    
    # Opciones de consulta
    auto_decidir_timeout: bool = True  # Decidir automáticamente si no hay respuesta
    acumular_consultas: bool = True    # Acumular consultas en bloque
    
    # Debug
    debug_mode: bool = False
    
    def agregar_regla(self, tipo: str, accion: str, condicion: Optional[str] = None, 
                      permanente: bool = False) -> None:
        """Agregar regla personalizada"""
        regla = ReglaUsuario(tipo=tipo, condicion=condicion, accion=accion)
        if permanente:
            self.reglas_permanentes.append(regla)
        else:
            self.reglas_sesion.append(regla)
    
    def eliminar_regla(self, indice: int, permanente: bool = False) -> bool:
        """Eliminar regla por índice"""
        lista = self.reglas_permanentes if permanente else self.reglas_sesion
        if 0 <= indice < len(lista):
            lista.pop(indice)
            return True
        return False
    
    def obtener_reglas_activas(self) -> List[ReglaUsuario]:
        """Obtener todas las reglas activas"""
        return [r for r in self.reglas_permanentes + self.reglas_sesion if r.activa]
    
    def aplicar_regla(self, contexto: Dict[str, Any]) -> Optional[str]:
        """
        Aplicar reglas al contexto dado.
        Retorna la acción si alguna regla aplica, None si no.
        """
        for regla in self.obtener_reglas_activas():
            if regla.tipo == "siempre":
                return regla.accion
            elif regla.tipo == "nunca":
                # Verificar si la acción está prohibida
                pass
            elif regla.tipo == "cuando":
                # Evaluar condición
                if self._evaluar_condicion(regla.condicion, contexto):
                    return regla.accion
        return None
    
    def _evaluar_condicion(self, condicion: str, contexto: Dict[str, Any]) -> bool:
        """Evaluar condición de regla (simplificado)"""
        # Implementación básica - expandir según necesidades
        if not condicion:
            return False
        
        # Verificar si el token está en el contexto
        if "token" in contexto:
            if contexto["token"] in condicion:
                return True
        
        return False
    
    def to_dict(self) -> Dict:
        """Serializar configuración"""
        return {
            "modo_transliteracion": self.modo_transliteracion.name,
            "norma_transliteracion": self.norma_transliteracion.name,
            "modo_salida": self.modo_salida.name,
            "reglas_permanentes": [
                {"tipo": r.tipo, "condicion": r.condicion, "accion": r.accion}
                for r in self.reglas_permanentes
            ],
            "reglas_sesion": [
                {"tipo": r.tipo, "condicion": r.condicion, "accion": r.accion}
                for r in self.reglas_sesion
            ],
            "locuciones_predefinidas": self.locuciones_predefinidas,
            "debug_mode": self.debug_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConfiguracionSistema':
        """Deserializar configuración"""
        config = cls()
        
        if "modo_transliteracion" in data:
            config.modo_transliteracion = ModoTransliteracion[data["modo_transliteracion"]]
        if "norma_transliteracion" in data:
            config.norma_transliteracion = NormaTransliteracion[data["norma_transliteracion"]]
        if "modo_salida" in data:
            config.modo_salida = ModoSalida[data["modo_salida"]]
        
        for r in data.get("reglas_permanentes", []):
            config.agregar_regla(r["tipo"], r["accion"], r.get("condicion"), permanente=True)
        
        for r in data.get("reglas_sesion", []):
            config.agregar_regla(r["tipo"], r["accion"], r.get("condicion"), permanente=False)
        
        config.locuciones_predefinidas = data.get("locuciones_predefinidas", [])
        config.debug_mode = data.get("debug_mode", False)
        
        return config

# Instancia global de configuración
config_global = ConfiguracionSistema()

def obtener_config() -> ConfiguracionSistema:
    """Obtener configuración global"""
    return config_global

def establecer_config(config: ConfiguracionSistema) -> None:
    """Establecer configuración global"""
    global config_global
    config_global = config
