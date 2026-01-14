"""
Módulo de Integración con la API del BCRP (Banco Central de Reserva del Perú)
Permite obtener series estadísticas macroeconómicas actualizadas
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

# =========================================================================
# CONFIGURACIÓN
# =========================================================================

class BCRPConfig:
    """Configuración de la API del BCRP"""
    BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
    DEFAULT_FORMAT = "json"
    DEFAULT_LANGUAGE = "esp"  # esp o ing
    TIMEOUT = 10  # segundos


# =========================================================================
# CÓDIGOS DE SERIES ECONÓMICAS COMUNES
# =========================================================================

class SeriesCodes:
    """
    Códigos de series económicas más utilizadas del BCRP
    Fuente: https://estadisticas.bcrp.gob.pe/estadisticas/series/
    """
    
    # Tipo de Cambio
    TIPO_CAMBIO_PROMEDIO = "PD04637PD"  # Tipo de cambio - Promedio del periodo (S/ por US$)
    TIPO_CAMBIO_COMPRA = "PD04638PD"    # Tipo de cambio - Compra (S/ por US$)
    TIPO_CAMBIO_VENTA = "PD04639PD"     # Tipo de cambio - Venta (S/ por US$)
    
    # Tasas de Interés
    TASA_REFERENCIA_BCRP = "PD04711PD"  # Tasa de interés de referencia del BCRP
    TASA_INTERBANCARIA = "PD04706PD"    # Tasa de interés interbancaria
    TAMN_DEPOSITOS = "PD04718PD"        # TAMN - Depósitos hasta 360 días (%)
    TAMEX_DEPOSITOS = "PD04719PD"       # TAMEX - Depósitos hasta 360 días (%)
    TCEA_PRESTAMOS_MN = "PD04720PD"     # TCEA - Préstamos personales en MN (%)
    TCEA_PRESTAMOS_ME = "PD04721PD"     # TCEA - Préstamos personales en ME (%)
    
    # Inflación
    IPC_NACIONAL = "PN01270PM"          # IPC Nacional - Variación % mensual
    IPC_LIMA = "PN01271PM"              # IPC Lima - Variación % mensual
    INFLACION_ANUAL = "PN01272PM"       # Inflación anual (%)
    
    # PBI
    PBI_REAL = "PN01755AQ"              # PBI real - Variación % (trimestral)
    PBI_NOMINAL = "PN01758AQ"           # PBI nominal (millones S/)
    
    # Reservas Internacionales
    RIN_MILLONES_USD = "PD04635PD"      # Reservas Internacionales Netas (millones US$)
    
    # Emisión Primaria
    EMISION_PRIMARIA = "PD04641PD"      # Emisión primaria (millones S/)
    
    # Balanza Comercial
    EXPORTACIONES = "PN01306PM"         # Exportaciones (millones US$)
    IMPORTACIONES = "PN01307PM"         # Importaciones (millones US$)
    
    # Crédito
    CREDITO_TOTAL = "PD04725PD"         # Crédito total al sector privado (millones S/)
    CREDITO_HIPOTECARIO = "PD04733PD"   # Crédito hipotecario (millones S/)


# =========================================================================
# DESCRIPCIONES AMIGABLES DE SERIES
# =========================================================================

SERIES_DESCRIPTIONS = {
    # Tipo de Cambio
    SeriesCodes.TIPO_CAMBIO_PROMEDIO: "Tipo de cambio promedio (S/ por US$)",
    SeriesCodes.TIPO_CAMBIO_COMPRA: "Tipo de cambio compra (S/ por US$)",
    SeriesCodes.TIPO_CAMBIO_VENTA: "Tipo de cambio venta (S/ por US$)",
    
    # Tasas
    SeriesCodes.TASA_REFERENCIA_BCRP: "Tasa de referencia del BCRP (%)",
    SeriesCodes.TASA_INTERBANCARIA: "Tasa interbancaria (%)",
    SeriesCodes.TAMN_DEPOSITOS: "TAMN - Tasa activa de depósitos en soles (%)",
    SeriesCodes.TAMEX_DEPOSITOS: "TAMEX - Tasa activa de depósitos en dólares (%)",
    SeriesCodes.TCEA_PRESTAMOS_MN: "TCEA préstamos personales en soles (%)",
    SeriesCodes.TCEA_PRESTAMOS_ME: "TCEA préstamos personales en dólares (%)",
    
    # Inflación
    SeriesCodes.IPC_NACIONAL: "IPC Nacional - Variación mensual (%)",
    SeriesCodes.INFLACION_ANUAL: "Inflación anual (%)",
    
    # Otros
    SeriesCodes.RIN_MILLONES_USD: "Reservas Internacionales Netas (millones US$)",
    SeriesCodes.PBI_REAL: "PBI real - Variación trimestral (%)",
}


# =========================================================================
# CLASE PRINCIPAL
# =========================================================================

class BCRPClient:
    """Cliente para interactuar con la API del BCRP"""
    
    def __init__(self, config: BCRPConfig = None):
        """
        Inicializa el cliente BCRP
        
        Args:
            config: Configuración personalizada
        """
        self.config = config or BCRPConfig()
    
    def get_series(
        self,
        series_codes: List[str],
        output_format: str = "json",
        start_period: Optional[str] = None,
        end_period: Optional[str] = None,
        language: str = "esp"
    ) -> Dict[str, Any]:
        """
        Obtiene datos de una o más series del BCRP
        
        Args:
            series_codes: Lista de códigos de series (máximo 10)
            output_format: Formato de salida (json, xml, csv, etc.)
            start_period: Periodo inicial (formato: YYYY-MM para mensual, YYYY-Q para trimestral)
            end_period: Periodo final
            language: Idioma ('esp' o 'ing')
            
        Returns:
            Diccionario con los datos de la API
            
        Raises:
            ValueError: Si se proporcionan más de 10 series
            requests.RequestException: Si hay error en la petición
        """
        if len(series_codes) > 10:
            raise ValueError("Máximo 10 series por consulta")
        
        # Construir URL
        series_str = "-".join(series_codes)
        url_parts = [self.config.BASE_URL, series_str, output_format]
        
        if start_period:
            url_parts.append(start_period)
            if end_period:
                url_parts.append(end_period)
        
        if language != "esp":
            url_parts.append(language)
        
        url = "/".join(url_parts)
        
        # Hacer petición
        try:
            response = requests.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            
            if output_format == "json":
                return response.json()
            else:
                return {"raw": response.text}
                
        except requests.RequestException as e:
            print(f"Error consultando API BCRP: {e}")
            return {"error": str(e)}
    
    def get_latest_value(self, series_code: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último valor disponible de una serie
        
        Args:
            series_code: Código de la serie
            
        Returns:
            Diccionario con periodo y valor, o None si hay error
        """
        try:
            data = self.get_series([series_code])
            
            if "periods" in data and data["periods"]:
                periods = data["periods"]
                last_period = periods[-1]
                
                # Obtener el nombre de la serie
                series_name = data.get("config", {}).get("series", [{}])[0].get("name", series_code)
                
                return {
                    "serie": series_name,
                    "codigo": series_code,
                    "periodo": last_period.get("name"),
                    "valor": last_period.get("values", [None])[0],
                    "descripcion": SERIES_DESCRIPTIONS.get(series_code, "")
                }
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo último valor: {e}")
            return None
    
    def get_tipo_cambio(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el tipo de cambio actual (compra, venta, promedio)
        
        Returns:
            Diccionario con tipos de cambio o None
        """
        try:
            data = self.get_series([
                SeriesCodes.TIPO_CAMBIO_PROMEDIO,
                SeriesCodes.TIPO_CAMBIO_COMPRA,
                SeriesCodes.TIPO_CAMBIO_VENTA
            ])
            
            if "periods" in data and data["periods"]:
                last_period = data["periods"][-1]
                values = last_period.get("values", [])
                
                return {
                    "fecha": last_period.get("name"),
                    "promedio": values[0] if len(values) > 0 else None,
                    "compra": values[1] if len(values) > 1 else None,
                    "venta": values[2] if len(values) > 2 else None
                }
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo tipo de cambio: {e}")
            return None
    
    def get_tasas_interes(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene las tasas de interés principales
        
        Returns:
            Diccionario con tasas de interés
        """
        try:
            data = self.get_series([
                SeriesCodes.TASA_REFERENCIA_BCRP,
                SeriesCodes.TAMN_DEPOSITOS,
                SeriesCodes.TAMEX_DEPOSITOS
            ])
            
            if "periods" in data and data["periods"]:
                last_period = data["periods"][-1]
                values = last_period.get("values", [])
                
                return {
                    "fecha": last_period.get("name"),
                    "tasa_referencia": values[0] if len(values) > 0 else None,
                    "tamn_depositos": values[1] if len(values) > 1 else None,
                    "tamex_depositos": values[2] if len(values) > 2 else None
                }
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo tasas de interés: {e}")
            return None
    
    def get_inflacion(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de inflación
        
        Returns:
            Diccionario con datos de inflación
        """
        return self.get_latest_value(SeriesCodes.INFLACION_ANUAL)
    
    def format_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Formatea datos del BCRP para incluir en el prompt del LLM
        
        Args:
            data: Datos obtenidos de la API
            
        Returns:
            String formateado para el contexto
        """
        if not data or "error" in data:
            return "No se pudieron obtener datos del BCRP."
        
        formatted_parts = []
        
        # Formatear según el tipo de dato
        if "serie" in data:
            # Formato de get_latest_value
            formatted_parts.append(f"📊 {data['serie']}")
            formatted_parts.append(f"   Periodo: {data['periodo']}")
            formatted_parts.append(f"   Valor: {data['valor']}")
            if data.get("descripcion"):
                formatted_parts.append(f"   {data['descripcion']}")
        
        elif "promedio" in data:
            # Formato de tipo de cambio
            formatted_parts.append(f"💱 Tipo de Cambio ({data['fecha']})")
            formatted_parts.append(f"   Promedio: S/ {data['promedio']}")
            formatted_parts.append(f"   Compra: S/ {data['compra']}")
            formatted_parts.append(f"   Venta: S/ {data['venta']}")
        
        elif "tasa_referencia" in data:
            # Formato de tasas
            formatted_parts.append(f"📈 Tasas de Interés ({data['fecha']})")
            formatted_parts.append(f"   Tasa de Referencia BCRP: {data['tasa_referencia']}%")
            formatted_parts.append(f"   TAMN Depósitos: {data['tamn_depositos']}%")
            formatted_parts.append(f"   TAMEX Depósitos: {data['tamex_depositos']}%")
        
        return "\n".join(formatted_parts)


# =========================================================================
# FUNCIONES HELPER PARA INTEGRACIÓN CON CHATBOT
# =========================================================================

def detect_economic_query(message: str) -> Optional[str]:
    """
    Detecta si una consulta requiere datos del BCRP
    
    Args:
        message: Mensaje del usuario
        
    Returns:
        Tipo de consulta detectada o None
    """
    message_lower = message.lower()
    
    # Patrones de consulta
    patterns = {
        "tipo_cambio": ["tipo de cambio", "dolar", "dólar", "tc", "cambio dolar"],
        "tasas": ["tasa de interes", "tasa de interés", "tamn", "tamex", "tasa referencia"],
        "inflacion": ["inflacion", "inflación", "ipc"],
        "general": ["datos económicos", "indicadores económicos", "estadísticas bcrp"]
    }
    
    for query_type, keywords in patterns.items():
        if any(keyword in message_lower for keyword in keywords):
            return query_type
    
    return None


def get_economic_context(message: str) -> str:
    """
    Obtiene contexto económico relevante según la consulta
    
    Args:
        message: Mensaje del usuario
        
    Returns:
        Contexto económico formateado
    """
    query_type = detect_economic_query(message)
    
    if not query_type:
        return ""
    
    client = BCRPClient()
    context_parts = ["--- DATOS ECONÓMICOS ACTUALIZADOS (BCRP) ---\n"]
    
    try:
        if query_type == "tipo_cambio":
            data = client.get_tipo_cambio()
            if data:
                context_parts.append(client.format_for_prompt(data))
        
        elif query_type == "tasas":
            data = client.get_tasas_interes()
            if data:
                context_parts.append(client.format_for_prompt(data))
        
        elif query_type == "inflacion":
            data = client.get_inflacion()
            if data:
                context_parts.append(client.format_for_prompt(data))
        
        elif query_type == "general":
            # Obtener múltiples indicadores
            tc = client.get_tipo_cambio()
            tasas = client.get_tasas_interes()
            
            if tc:
                context_parts.append(client.format_for_prompt(tc))
            if tasas:
                context_parts.append("\n" + client.format_for_prompt(tasas))
        
        context_parts.append("\nFuente: Banco Central de Reserva del Perú (BCRP)")
        return "\n".join(context_parts)
    
    except Exception as e:
        print(f"Error obteniendo contexto económico: {e}")
        return ""