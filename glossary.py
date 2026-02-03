"""
════════════════════════════════════════════════════════════════
SISTEMA DE TRADUCCIÓN ISOMÓRFICA — VERSIÓN PYTHON
Bloque 3/13: Glosario (P8)
════════════════════════════════════════════════════════════════

PROPÓSITO:
  1. Registrar exhaustivamente todos los elementos léxicos ANTES de traducir
  2. Custodiar el registro durante la traducción
  3. Alertar y prohibir sinonimia en núcleos

PRINCIPIOS:
  - Núcleos: INVARIABLES (una traducción, siempre)
  - Partículas: POLIVALENTES (varían por función)
  - Locuciones: UNIDADES COMPLETAS (componentes BLOQUEADOS)
  - Registro completo: OBLIGATORIO (FALLO CRÍTICO si incompleto)
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime

from constants import (
    TokenStatus, TokenCategoria, CategoriaGramatical,
    FuncRole, ConsultaCodigo, FalloCritico, Reason,
    MARGEN_VALORES
)
from models import (
    EntradaGlosario, Locucion, SlotN, SlotP,
    MatrizFuente, ErrorCritico, Consulta, Opcion
)
from config import obtener_config


# ══════════════════════════════════════════════════════════════
# EXCEPCIONES ESPECÍFICAS
# ══════════════════════════════════════════════════════════════

class GlosarioError(Exception):
    """Error base del glosario"""
    pass


class RegistroIncompletoError(GlosarioError):
    """FALLO CRÍTICO: Registro incompleto (P8.A4)"""
    def __init__(self, faltantes: List[str], sobrantes: List[str]):
        self.faltantes = faltantes
        self.sobrantes = sobrantes
        super().__init__(f"Tokens faltantes: {faltantes}, sobrantes: {sobrantes}")


class SinonimiaError(GlosarioError):
    """FALLO CRÍTICO: Sinonimia en núcleo (P8.B3)"""
    def __init__(self, token: str, existente: str, propuesta: str):
        self.token = token
        self.existente = existente
        self.propuesta = propuesta
        super().__init__(
            f"Sinonimia detectada en '{token}': existente='{existente}', propuesta='{propuesta}'"
        )


class TokenNoRegistradoError(GlosarioError):
    """FALLO CRÍTICO: Token no registrado (P8.B1)"""
    def __init__(self, token: str, posicion: int):
        self.token = token
        self.posicion = posicion
        super().__init__(f"Token no registrado: '{token}' en posición {posicion}")


# ══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: GLOSARIO
# ══════════════════════════════════════════════════════════════

class Glosario:
    """
    Glosario del sistema de traducción isomórfica (P8)
    
    Fases:
      A. Pre-traducción: Detección, tokenización, registro, verificación
      B. Durante traducción: Custodia, verificación, asignación
      C. Inmutabilidad: Solo usuario puede modificar
    """
    
    def __init__(self):
        # Entradas principales
        self._entradas: Dict[str, EntradaGlosario] = {}
        
        # Locuciones detectadas
        self._locuciones: Dict[str, Locucion] = {}
        
        # Contador de locuciones
        self._locucion_counter: int = 0
        
        # Estado
        self._sellado: bool = False
        
        # Historial de cambios
        self._historial: List[Dict[str, Any]] = []
        
        # Consultas pendientes
        self._consultas_pendientes: List[Consulta] = []
    
    # ══════════════════════════════════════════════════════════
    # FASE A: PRE-TRADUCCIÓN
    # ══════════════════════════════════════════════════════════
    
    def fase_a_procesar(self, texto: str, tokens_clasificados: List[Tuple[str, TokenCategoria, CategoriaGramatical]]) -> bool:
        """
        Ejecutar Fase A completa (P8.A)
        
        Args:
            texto: Texto fuente limpio
            tokens_clasificados: Lista de (token, categoria, cat_gramatical)
        
        Returns:
            True si glosario sellado correctamente
        
        Raises:
            RegistroIncompletoError: Si faltan tokens
        """
        # A1. Detección de locuciones
        self._a1_detectar_locuciones(texto)
        
        # A2. Tokenización (ya viene clasificado)
        # A3. Registro inicial
        self._a3_registrar_tokens(tokens_clasificados)
        
        # A4. Verificación de completitud
        return self._a4_verificar_completitud(texto)
    
    def _a1_detectar_locuciones(self, texto: str) -> List[Locucion]:
        """
        A1. Detección de locuciones (P8.A1)
        
        Método económico:
          1. Lista predefinida (si existe)
          2. Heurística simple: PREP + SUST + SUFIJO_PRONOMINAL
        """
        locuciones_detectadas = []
        config = obtener_config()
        
        # Método 1: Lista predefinida
        for loc_predefinida in config.locuciones_predefinidas:
            if loc_predefinida in texto:
                loc = self._crear_locucion_desde_patron(loc_predefinida, texto)
                if loc:
                    locuciones_detectadas.append(loc)
        
        # Método 2: Heurística básica (bajo consumo)
        # Patrón: partícula + palabra + sufijo pronominal árabe
        # Ejemplo simplificado para demostración
        patrones_heuristicos = [
            r'\b(bi|li|fi|min|ʿan|ʿalā)-?(\w+)-?(hā|hu|humā|hum|hunna|ka|ki|kumā|kum|kunna|ī|nā)\b',
        ]
        
        for patron in patrones_heuristicos:
            matches = re.finditer(patron, texto, re.IGNORECASE)
            for match in matches:
                # Crear consulta C3 para confirmar
                posible_loc = match.group(0)
                if posible_loc not in [l.src for l in locuciones_detectadas]:
                    consulta = self._crear_consulta_locucion(posible_loc, match.start())
                    self._consultas_pendientes.append(consulta)
        
        return locuciones_detectadas
    
    def _crear_locucion_desde_patron(self, patron: str, texto: str) -> Optional[Locucion]:
        """Crear locución desde patrón conocido"""
        pos = texto.find(patron)
        if pos == -1:
            return None
        
        self._locucion_counter += 1
        loc_id = f"LOC_{self._locucion_counter:04d}"
        
        # Separar componentes (simplificado)
        componentes = patron.replace("-", " ").split()
        
        # Calcular posiciones (aproximado - se ajusta en tokenización real)
        posiciones = list(range(pos, pos + len(componentes)))
        
        locucion = Locucion(
            id=loc_id,
            src=patron,
            componentes=componentes,
            posiciones=posiciones
        )
        
        self._locuciones[loc_id] = locucion
        return locucion
    
    def _crear_consulta_locucion(self, posible_loc: str, posicion: int) -> Consulta:
        """Crear consulta C3 para confirmar locución"""
        return Consulta(
            numero=len(self._consultas_pendientes) + 1,
            codigo=ConsultaCodigo.C3_POSIBLE_LOCUCION,
            contexto=f"Patrón detectado en posición {posicion}",
            token_o_frase=posible_loc,
            opciones=[
                Opcion("A", "Sí, es locución fija", "Traducir como unidad"),
                Opcion("B", "No, traducir componentes individualmente")
            ],
            recomendacion="A"
        )
    
    def confirmar_locucion(self, src: str, es_locucion: bool, 
                           traduccion_etym: Optional[Dict[str, str]] = None) -> Optional[Locucion]:
        """
        Confirmar o rechazar una posible locución detectada
        
        Args:
            src: Secuencia fuente
            es_locucion: True si usuario confirma que es locución
            traduccion_etym: Dict de traducciones etimológicas por componente
        """
        if not es_locucion:
            return None
        
        self._locucion_counter += 1
        loc_id = f"LOC_{self._locucion_counter:04d}"
        
        componentes = src.replace("-", " ").split()
        
        locucion = Locucion(
            id=loc_id,
            src=src,
            componentes=componentes,
            posiciones=[]  # Se establecen en tokenización
        )
        
        if traduccion_etym:
            locucion.generar_traduccion(traduccion_etym)
        
        self._locuciones[loc_id] = locucion
        return locucion
    
    def _a3_registrar_tokens(self, tokens_clasificados: List[Tuple[str, TokenCategoria, CategoriaGramatical]]) -> None:
        """
        A3. Registro inicial (P8.A3)
        
        Registrar todos los tokens con status PENDIENTE
        """
        for idx, (token, categoria, cat_gram) in enumerate(tokens_clasificados):
            # Verificar si token está bloqueado por locución
            locucion_id = self._token_en_locucion(token, idx)
            
            if token not in self._entradas:
                entrada = EntradaGlosario(
                    token_src=token,
                    categoria=categoria,
                    status=TokenStatus.BLOQUEADO if locucion_id else TokenStatus.PENDIENTE,
                    ocurrencias=[idx]
                )
                self._entradas[token] = entrada
            else:
                # Token ya existe, agregar ocurrencia
                self._entradas[token].ocurrencias.append(idx)
    
    def _token_en_locucion(self, token: str, posicion: int) -> Optional[str]:
        """Verificar si token pertenece a locución en esta posición"""
        for loc_id, loc in self._locuciones.items():
            if token in loc.componentes and posicion in loc.posiciones:
                return loc_id
        return None
    
    def _a4_verificar_completitud(self, texto: str) -> bool:
        """
        A4. Verificación de completitud (P8.A4)
        
        OBLIGATORIA - FALLO CRÍTICO si incompleto
        """
        # Contar tokens en texto (simplificado)
        tokens_texto = set(re.findall(r'\b\w+\b', texto))
        tokens_registrados = set(self._entradas.keys())
        
        # Agregar componentes de locuciones
        for loc in self._locuciones.values():
            tokens_registrados.update(loc.componentes)
        
        faltantes = list(tokens_texto - tokens_registrados)
        sobrantes = list(tokens_registrados - tokens_texto)
        
        if faltantes:
            raise RegistroIncompletoError(faltantes, sobrantes)
        
        # Sellar glosario
        self._sellado = True
        self._registrar_historial("GLOSARIO_SELLADO", {
            "total_entradas": len(self._entradas),
            "total_locuciones": len(self._locuciones)
        })
        
        return True
    
    def esta_sellado(self) -> bool:
        """Verificar si glosario está sellado"""
        return self._sellado
    
    # ══════════════════════════════════════════════════════════
    # FASE B: DURANTE TRADUCCIÓN
    # ══════════════════════════════════════════════════════════
    
    def fase_b_verificar_existencia(self, token: str, posicion: int) -> bool:
        """
        B1. Verificación de existencia (P8.B1)
        
        Raises:
            TokenNoRegistradoError: Si token no existe
        """
        if token not in self._entradas:
            raise TokenNoRegistradoError(token, posicion)
        return True
    
    def fase_b_verificar_bloqueo(self, token: str, posicion: int) -> Optional[str]:
        """
        B2. Verificación de bloqueo (P8.B2)
        
        Returns:
            ID de locución si está bloqueado, None si no
        """
        locucion_id = self._token_en_locucion(token, posicion)
        if locucion_id:
            return locucion_id
        
        entrada = self._entradas.get(token)
        if entrada and entrada.status == TokenStatus.BLOQUEADO:
            # Buscar a qué locución pertenece
            for loc_id, loc in self._locuciones.items():
                if token in loc.componentes:
                    return loc_id
        
        return None
    
    def fase_b_verificar_sinonimia(self, token: str, tgt_propuesto: str) -> bool:
        """
        B3. Verificación de sinonimia - Solo núcleos (P8.B3)
        
        Raises:
            SinonimiaError: Si intenta asignar traducción diferente a núcleo
        """
        entrada = self._entradas.get(token)
        if not entrada:
            return True  # Se manejará en B1
        
        # Solo verificar sinonimia en NÚCLEOS
        if entrada.categoria != TokenCategoria.NUCLEO:
            return True  # Partículas son polivalentes
        
        if entrada.token_tgt is not None and entrada.token_tgt != "":
            if tgt_propuesto != entrada.token_tgt:
                raise SinonimiaError(token, entrada.token_tgt, tgt_propuesto)
        
        return True
    
    def fase_b_asignar(self, token: str, tgt: str, margen: int = 1,
                       etiqueta: Optional[str] = None,
                       func_role: Optional[FuncRole] = None) -> bool:
        """
        B4. Asignación - Primera vez (P8.B4)
        
        Args:
            token: Token fuente
            tgt: Traducción asignada
            margen: Nivel de complejidad
            etiqueta: NO_ROOT, COLLISION, etc.
            func_role: Función sintáctica (solo partículas)
        """
        entrada = self._entradas.get(token)
        if not entrada:
            return False
        
        # Si es núcleo y ya tiene traducción, verificar sinonimia
        if entrada.es_nucleo() and entrada.token_tgt:
            self.fase_b_verificar_sinonimia(token, tgt)
            return True  # Ya asignado correctamente
        
        # Asignar
        if entrada.es_particula() and func_role:
            # Partículas pueden tener traducciones por función
            entrada.traducciones_por_funcion[func_role] = tgt
        
        entrada.token_tgt = tgt
        entrada.status = TokenStatus.ASIGNADO
        entrada.margen = margen
        entrada.etiqueta = etiqueta
        
        self._registrar_historial("ASIGNACION", {
            "token": token,
            "traduccion": tgt,
            "margen": margen,
            "etiqueta": etiqueta
        })
        
        return True
    
    def obtener_traduccion(self, token: str, func_role: Optional[FuncRole] = None) -> Optional[str]:
        """
        Obtener traducción de un token
        
        Args:
            token: Token fuente
            func_role: Función sintáctica (para partículas polivalentes)
        """
        entrada = self._entradas.get(token)
        if not entrada:
            return None
        
        # Si es partícula con función específica
        if func_role and func_role in entrada.traducciones_por_funcion:
            return entrada.traducciones_por_funcion[func_role]
        
        return entrada.token_tgt
    
    def obtener_traduccion_locucion(self, locucion_id: str) -> Optional[str]:
        """Obtener traducción de una locución"""
        loc = self._locuciones.get(locucion_id)
        return loc.tgt if loc else None
    
    # ══════════════════════════════════════════════════════════
    # FASE C: INMUTABILIDAD - MODIFICACIONES POR USUARIO
    # ══════════════════════════════════════════════════════════
    
    def actualizar_entrada(self, token: str, nueva_tgt: str) -> Tuple[bool, int]:
        """
        Actualizar traducción de entrada (solo usuario)
        
        Returns:
            (éxito, ocurrencias_afectadas)
        """
        entrada = self._entradas.get(token)
        if not entrada:
            return False, 0
        
        antigua_tgt = entrada.token_tgt
        entrada.token_tgt = nueva_tgt
        
        self._registrar_historial("ACTUALIZACION_USUARIO", {
            "token": token,
            "anterior": antigua_tgt,
            "nuevo": nueva_tgt
        })
        
        return True, len(entrada.ocurrencias)
    
    def agregar_entrada(self, token: str, categoria: TokenCategoria, 
                        tgt: Optional[str] = None) -> bool:
        """Agregar entrada manual (solo usuario)"""
        if token in self._entradas:
            return False
        
        entrada = EntradaGlosario(
            token_src=token,
            categoria=categoria,
            token_tgt=tgt,
            status=TokenStatus.ASIGNADO if tgt else TokenStatus.PENDIENTE
        )
        self._entradas[token] = entrada
        
        self._registrar_historial("ENTRADA_AGREGADA_USUARIO", {
            "token": token,
            "categoria": categoria.name,
            "traduccion": tgt
        })
        
        return True
    
    def agregar_locucion(self, src: str, componentes: List[str],
                         posiciones: List[int], tgt: str) -> Locucion:
        """
        Agregar locución manual (solo usuario)
        """
        self._locucion_counter += 1
        loc_id = f"LOC_{self._locucion_counter:04d}"
        
        locucion = Locucion(
            id=loc_id,
            src=src,
            componentes=componentes,
            posiciones=posiciones,
            tgt=tgt
        )
        
        self._locuciones[loc_id] = locucion
        
        # Bloquear componentes
        for comp in componentes:
            if comp in self._entradas:
                self._entradas[comp].status = TokenStatus.BLOQUEADO
        
        self._registrar_historial("LOCUCION_AGREGADA_USUARIO", {
            "id": loc_id,
            "src": src,
            "tgt": tgt
        })
        
        return locucion
    
    def eliminar_entrada(self, token: str) -> Tuple[bool, int]:
        """
        Eliminar entrada (solo usuario)
        
        Returns:
            (éxito, ocurrencias_afectadas)
        """
        entrada = self._entradas.get(token)
        if not entrada:
            return False, 0
        
        ocurrencias = len(entrada.ocurrencias)
        del self._entradas[token]
        
        self._registrar_historial("ENTRADA_ELIMINADA_USUARIO", {
            "token": token,
            "ocurrencias_afectadas": ocurrencias
        })
        
        return True, ocurrencias
    
    # ══════════════════════════════════════════════════════════
    # CONSULTAS Y UTILIDADES
    # ══════════════════════════════════════════════════════════
    
    def obtener_entrada(self, token: str) -> Optional[EntradaGlosario]:
        """Obtener entrada por token"""
        return self._entradas.get(token)
    
    def obtener_locucion(self, loc_id: str) -> Optional[Locucion]:
        """Obtener locución por ID"""
        return self._locuciones.get(loc_id)
    
    def obtener_locuciones(self) -> Dict[str, Locucion]:
        """Obtener todas las locuciones"""
        return self._locuciones.copy()
    
    def obtener_entradas_por_margen(self) -> List[EntradaGlosario]:
        """Obtener entradas ordenadas por margen (mayor a menor)"""
        return sorted(
            self._entradas.values(),
            key=lambda e: e.margen,
            reverse=True
        )
    
    def obtener_alternativas(self) -> List[EntradaGlosario]:
        """Obtener entradas de alto margen (para comando [ALTERNATIVAS])"""
        return [e for e in self._entradas.values() if e.margen >= 3]
    
    def obtener_estadisticas(self) -> Dict[str, int]:
        """Obtener estadísticas del glosario"""
        total = len(self._entradas)
        asignadas = sum(1 for e in self._entradas.values() 
                        if e.status == TokenStatus.ASIGNADO)
        pendientes = sum(1 for e in self._entradas.values() 
                         if e.status == TokenStatus.PENDIENTE)
        bloqueadas = sum(1 for e in self._entradas.values() 
                         if e.status == TokenStatus.BLOQUEADO)
        
        return {
            "total": total,
            "asignadas": asignadas,
            "pendientes": pendientes,
            "bloqueadas": bloqueadas,
            "locuciones": len(self._locuciones)
        }
    
    def obtener_consultas_pendientes(self) -> List[Consulta]:
        """Obtener consultas pendientes"""
        return self._consultas_pendientes.copy()
    
    def limpiar_consultas_pendientes(self) -> None:
        """Limpiar consultas pendientes"""
        self._consultas_pendientes.clear()
    
    # ══════════════════════════════════════════════════════════
    # HISTORIAL
    # ══════════════════════════════════════════════════════════
    
    def _registrar_historial(self, accion: str, datos: Dict[str, Any]) -> None:
        """Registrar acción en historial"""
        self._historial.append({
            "accion": accion,
            "datos": datos,
            "timestamp": datetime.now().isoformat()
        })
    
    def obtener_historial(self) -> List[Dict[str, Any]]:
        """Obtener historial de cambios"""
        return self._historial.copy()
    
    # ══════════════════════════════════════════════════════════
    # EXPORTACIÓN E IMPORTACIÓN
    # ══════════════════════════════════════════════════════════
    
    def exportar_json(self) -> str:
        """Exportar glosario a JSON"""
        data = {
            "entradas": {
                token: {
                    "categoria": e.categoria.name,
                    "token_tgt": e.token_tgt,
                    "status": e.status.name,
                    "margen": e.margen,
                    "ocurrencias": e.ocurrencias,
                    "etiqueta": e.etiqueta
                }
                for token, e in self._entradas.items()
            },
            "locuciones": {
                loc_id: {
                    "src": loc.src,
                    "tgt": loc.tgt,
                    "componentes": loc.componentes,
                    "posiciones": loc.posiciones
                }
                for loc_id, loc in self._locuciones.items()
            },
            "sellado": self._sellado,
            "exportado": datetime.now().isoformat()
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def exportar_txt(self) -> str:
        """Exportar glosario a texto plano"""
        lineas = ["GLOSARIO", "=" * 40, ""]
        
        for entrada in self.obtener_entradas_por_margen():
            tgt = entrada.token_tgt or "[PENDIENTE]"
            linea = f"{tgt} ({entrada.token_src}) [{entrada.categoria.name}]"
            if entrada.etiqueta:
                linea += f" [{entrada.etiqueta}]"
            lineas.append(linea)
        
        if self._locuciones:
            lineas.extend(["", "LOCUCIONES", "-" * 40, ""])
            for loc in self._locuciones.values():
                lineas.append(f"{loc.tgt or '[PENDIENTE]'} ← {loc.src}")
        
        return "\n".join(lineas)
    
    def exportar_csv(self) -> str:
        """Exportar glosario a CSV"""
        lineas = ["token_src,token_tgt,categoria,status,margen,etiqueta"]
        
        for token, entrada in self._entradas.items():
            linea = f'"{token}","{entrada.token_tgt or ""}",{entrada.categoria.name},{entrada.status.name},{entrada.margen},"{entrada.etiqueta or ""}"'
            lineas.append(linea)
        
        return "\n".join(lineas)
    
    @classmethod
    def importar_json(cls, json_str: str) -> 'Glosario':
        """Importar glosario desde JSON"""
        data = json.loads(json_str)
        glosario = cls()
        
        for token, e_data in data.get("entradas", {}).items():
            entrada = EntradaGlosario(
                token_src=token,
                categoria=TokenCategoria[e_data["categoria"]],
                token_tgt=e_data.get("token_tgt"),
                status=TokenStatus[e_data["status"]],
                margen=e_data.get("margen", 0),
                ocurrencias=e_data.get("ocurrencias", []),
                etiqueta=e_data.get("etiqueta")
            )
            glosario._entradas[token] = entrada
        
        for loc_id, l_data in data.get("locuciones", {}).items():
            locucion = Locucion(
                id=loc_id,
                src=l_data["src"],
                tgt=l_data.get("tgt"),
                componentes=l_data["componentes"],
                posiciones=l_data["posiciones"]
            )
            glosario._locuciones[loc_id] = locucion
        
        glosario._sellado = data.get("sellado", False)
        
        return glosario
    
    # ══════════════════════════════════════════════════════════
    # FORMATEO PARA PRESENTACIÓN
    # ══════════════════════════════════════════════════════════
    
    def formatear_glosario(self, limite: int = 50, pagina: int = 1) -> str:
        """Formatear glosario para presentación"""
        entradas = self.obtener_entradas_por_margen()
        total = len(entradas)
        total_paginas = (total + limite - 1) // limite
        
        inicio = (pagina - 1) * limite
        fin = min(inicio + limite, total)
        
        lineas = [
            "═" * 50,
            f"GLOSARIO [{inicio+1}-{fin} de {total}]",
            "═" * 50,
            ""
        ]
        
        for entrada in entradas[inicio:fin]:
            tgt = entrada.token_tgt or "[PENDIENTE]"
            linea = f"  {tgt} ({entrada.token_src}) [{entrada.categoria.name}]"
            if entrada.etiqueta:
                linea += f" [{entrada.etiqueta}]"
            lineas.append(linea)
        
        lineas.append("")
        if total_paginas > 1:
            lineas.append(f"[Página {pagina}/{total_paginas}] — 'más' para continuar")
        lineas.append("═" * 50)
        
        return "\n".join(lineas)
    
    def formatear_locuciones(self) -> str:
        """Formatear locuciones para presentación"""
        if not self._locuciones:
            return "No hay locuciones registradas."
        
        lineas = [
            "═" * 50,
            "LOCUCIONES DETECTADAS",
            "═" * 50,
            ""
        ]
        
        for loc in self._locuciones.values():
            lineas.extend([
                f"  ID: {loc.id}",
                f"  Fuente: {loc.src}",
                f"  Traducción: {loc.tgt or '[PENDIENTE]'}",
                f"  Componentes: {', '.join(loc.componentes)} [BLOQUEADOS]",
                f"  Posiciones: {loc.posiciones}",
                ""
            ])
        
        lineas.append("═" * 50)
        return "\n".join(lineas)
    
    def formatear_alternativas(self) -> str:
        """Formatear alternativas para presentación"""
        alternativas = self.obtener_alternativas()
        
        if not alternativas:
            return "No hay términos de alto margen."
        
        lineas = [
            "═" * 50,
            "ALTERNATIVAS (Alto margen de decisión)",
            "═" * 50,
            ""
        ]
        
        for entrada in alternativas:
            lineas.extend([
                f"TÉRMINO: {entrada.token_src}",
                f"TRADUCCIÓN ACTUAL: {entrada.token_tgt or '[PENDIENTE]'}",
                f"MARGEN: {entrada.margen}",
                f"ETIQUETA: {entrada.etiqueta or 'N/A'}",
                "",
                "Para cambiar: [ACTUALIZA {} = nueva_traducción]".format(entrada.token_src),
                "-" * 40,
                ""
            ])
        
        lineas.append("═" * 50)
        return "\n".join(lineas)


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE AYUDA
# ══════════════════════════════════════════════════════════════

def crear_error_registro_incompleto(faltantes: List[str], sobrantes: List[str]) -> ErrorCritico:
    """Crear error crítico de registro incompleto"""
    return ErrorCritico(
        tipo=FalloCritico.REGISTRO_INCOMPLETO,
        mensaje="El glosario no contiene todos los tokens del texto.",
        contexto={
            "tokens_faltantes": faltantes,
            "tokens_sobrantes": sobrantes
        }
    )


def crear_error_sinonimia(token: str, existente: str, propuesta: str) -> ErrorCritico:
    """Crear error crítico de sinonimia"""
    return ErrorCritico(
        tipo=FalloCritico.SINONIMIA_NUCLEO,
        mensaje="Intento de asignar traducción diferente a núcleo ya asignado.",
        contexto={
            "token": token,
            "traduccion_existente": existente,
            "traduccion_propuesta": propuesta,
            "regla": "Núcleos son INVARIABLES"
        }
    )


def crear_error_token_no_registrado(token: str, posicion: int) -> ErrorCritico:
    """Crear error crítico de token no registrado"""
    return ErrorCritico(
        tipo=FalloCritico.TOKEN_NO_REGISTRADO,
        mensaje="Token encontrado durante traducción sin entrada en glosario.",
        contexto={
            "token": token,
            "posicion": posicion,
            "accion": "Registrar token antes de continuar"
        }
    )
