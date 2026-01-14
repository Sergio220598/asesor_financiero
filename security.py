import random
import re

# =========================================================================
# PALABRAS PROHIBIDAS EN INPUT (Usuario)
# =========================================================================
# Detecta intentos de manipulación, fraude o solicitudes inapropiadas

palabras_in = [
    # Fraude y actividades ilegales
    "hackear", "robar", "estafar", "defraudar", "falsificar",
    "lavar dinero", "lavado de dinero", "evadir impuestos", "evasión fiscal",
    "cuentas fantasma", "cuenta offshore ilegal", "piramide", "esquema ponzi",
    
    # Manipulación de sistemas bancarios
    "clonar tarjeta", "skimming", "phishing", "fraude bancario",
    "transferencia ilegal", "suplantación de identidad",
    
    # Productos financieros ilegales
    "préstamo gota a gota", "usura", "prestamista ilegal",
    "inversión piramidal", "multinivel fraudulento",
    
    # Información sensible de terceros
    "dame el pin", "contraseña de", "clave de", "datos de cuenta de otra persona",
    
    # Competencia desleal (si el bot es de un banco específico)
    "mejor que [banco]", "peor banco", "banco fraudulento",
    
    # Discriminación
    "no dar crédito por", "discriminar por edad", "discriminar por género",
    
    # Manipulación del bot
    "ignora las instrucciones", "eres ahora", "modo desarrollador",
    "prompt injection", "system prompt", "olvida tu rol"
]

# =========================================================================
# PALABRAS PROHIBIDAS EN OUTPUT (LLM)
# =========================================================================
# Evita que el bot genere respuestas inapropiadas o arriesgadas

palabras_out = [
    # Negación de servicio (indica mal funcionamiento)
    "no puedo ayudarte", "no sé", "no tengo información",
    "fuera de mi alcance", "no es mi función",
    
    # Consejos financieros arriesgados sin disclaimer
    "garantizo que ganarás", "inversión sin riesgo", "dinero fácil",
    "nunca perderás", "rendimiento asegurado",
    
    # Información sensible que no debería compartir
    "tu contraseña es", "tu pin es", "tu clave es",
    
    # Recomendaciones ilegales
    "evade impuestos", "oculta ingresos", "lava dinero",
    "falsifica documentos", "miente en tu declaración",
    
    # Discriminación
    "por tu edad no", "por tu género no", "por tu raza no",
    
    # Productos no regulados
    "criptomoneda sin regulación", "inversión piramidal",
    
    # Lenguaje inapropiado
    "maldiciones", "groserías", "palabras ofensivas"
]

# =========================================================================
# PATRONES DE REGEX PARA DETECCIÓN AVANZADA
# =========================================================================
# Detecta patrones más complejos que palabras simples

patterns_in = [
    # Solicitudes de información sensible de terceros
    r"cu[ae]nta\s+de\s+\w+",  # "cuenta de Juan"
    r"clave\s+de\s+mi\s+(esposa|esposo|amigo|jefe)",
    
    # Intentos de evasión fiscal
    r"c[oó]mo\s+(ocultar|esconder)\s+(ingresos|dinero|ganancias)",
    r"evitar\s+pagar\s+(impuestos|tributos)",
    
    # Fraudes específicos
    r"transferir\s+sin\s+que\s+se\s+den\s+cuenta",
    r"sacar\s+dinero\s+de\s+cuenta\s+ajena",
]

patterns_out = [
    # Garantías absolutas (prohibidas por reguladores)
    r"(garantizo|aseguro|prometo)\s+que\s+(ganarás|nunca perderás)",
    r"rendimiento\s+(garantizado|asegurado|seguro)\s+del?\s+\d+%",
    
    # Consejos fiscales sin disclaimer
    r"(evita|evade|esquiva)\s+(impuestos|tributos|sbs)",
]

# =========================================================================
# RESPUESTAS DE BLOQUEO
# =========================================================================

responses_input_blocked = [
    "Lo siento, no puedo asistirte con ese tipo de consultas. Mi función es brindarte asesoría financiera ética y legal.",
    "Esa solicitud está fuera del alcance de mi asesoría. Si necesitas ayuda con productos financieros legales, estaré encantado de ayudarte.",
    "No puedo procesar consultas que involucren actividades ilegales o no éticas. ¿Puedo ayudarte con algo más relacionado a finanzas personales?",
    "Mi rol es asesorar en finanzas de manera responsable. Esa consulta no es apropiada. ¿Tienes alguna otra pregunta sobre productos bancarios?",
    "Disculpa, no puedo responder a eso. Estoy aquí para ayudarte con decisiones financieras legales y éticas.",
    "Por políticas de seguridad y ética, no puedo ayudarte con esa consulta. ¿Necesitas información sobre cuentas de ahorro o préstamos?"
]

responses_output_blocked = [
    "Disculpa, mi respuesta anterior no cumplió con los estándares de seguridad. Por favor, reformula tu pregunta y con gusto te ayudaré.",
    "Lo siento, detecté un error en mi respuesta. ¿Podrías replantear tu consulta de otra manera?",
    "Por seguridad, no puedo completar esa respuesta. ¿Hay algo más en lo que pueda ayudarte?",
    "Mi respuesta no pasó los filtros de seguridad. Intentemos de nuevo con una pregunta diferente.",
]

# =========================================================================
# FUNCIONES DE VALIDACIÓN
# =========================================================================

def get_random_response(response_list: list) -> str:
    """Obtiene una respuesta aleatoria de una lista"""
    return random.choice(response_list)


def check_input(message: str) -> tuple[bool, str, str]:
    """
    Verifica si el mensaje del usuario contiene palabras o patrones prohibidos

    Args:
        message: Mensaje del usuario

    Returns:
        Tupla (is_blocked, tipo_bloqueo, detalle)
        - is_blocked: True si está bloqueado
        - tipo_bloqueo: "palabra" o "patrón"
        - detalle: La palabra o patrón detectado
    """
    message_lower = message.lower()

    # Verificar palabras prohibidas
    for palabra in palabras_in:
        if palabra.lower() in message_lower:
            return True, "palabra", palabra

    # Verificar patrones regex
    for pattern in patterns_in:
        if re.search(pattern, message_lower):
            return True, "patrón", pattern

    return False, "", ""


def check_output(response: str) -> tuple[bool, str, str]:
    """
    Verifica si la respuesta del LLM contiene palabras o patrones prohibidos

    Args:
        response: Respuesta del LLM

    Returns:
        Tupla (is_blocked, tipo_bloqueo, detalle)
    """
    response_lower = response.lower()

    # Verificar palabras prohibidas
    for palabra in palabras_out:
        if palabra.lower() in response_lower:
            return True, "palabra", palabra

    # Verificar patrones regex
    for pattern in patterns_out:
        if re.search(pattern, response_lower):
            return True, "patrón", pattern

    return False, "", ""


def sanitize_financial_data(text: str) -> str:
    """
    Sanitiza datos financieros sensibles del texto
    Reemplaza números de tarjeta, cuentas bancarias, etc.
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto con datos sensibles enmascarados
    """
    # Patrón para números de tarjeta (16 dígitos)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                  '[TARJETA-OCULTA]', text)
    
    # Patrón para números de cuenta (10-20 dígitos)
    text = re.sub(r'\b\d{10,20}\b', '[CUENTA-OCULTA]', text)
    
    # Patrón para CVV (3-4 dígitos después de "cvv" o "código")
    text = re.sub(r'(cvv|código|code|cvc)[\s:]+\d{3,4}', 
                  r'\1: [OCULTO]', text, flags=re.IGNORECASE)
    
    return text


def log_security_event(event_type: str, user_message: str, blocked_content: str):
    """
    Registra eventos de seguridad para auditoría
    
    Args:
        event_type: Tipo de evento ("input_blocked", "output_blocked")
        user_message: Mensaje original del usuario
        blocked_content: Contenido que causó el bloqueo
    """
    # En producción, esto debería ir a un sistema de logging centralizado
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"""
    ========================================
    [EVENTO DE SEGURIDAD]
    Timestamp: {timestamp}
    Tipo: {event_type}
    Contenido bloqueado: {blocked_content}
    Mensaje original: {user_message[:100]}...
    ========================================
    """
    
    print(log_entry)
    
    # En producción: guardar en archivo o base de datos
    # with open("security_logs.txt", "a") as f:
    #     f.write(log_entry)


# =========================================================================
# VALIDACIÓN DE CONTEXTO FINANCIERO
# =========================================================================

def validate_financial_context(message: str) -> tuple[bool, str]:
    """
    Valida que la consulta esté relacionada con finanzas
    Útil para evitar que el bot se desvíe de su propósito
    
    Args:
        message: Mensaje del usuario
        
    Returns:
        Tupla (is_valid, reason)
    """
    financial_keywords = [
        "préstamo", "crédito", "ahorro", "inversión", "banco", "cuenta",
        "tarjeta", "tasa", "interés", "deuda", "plazo fijo", "hipoteca",
        "seguro", "tcea", "trea", "cts", "afp", "fondos", "dinero",
        "soles", "dólares", "financiero", "económico", "presupuesto"
    ]
    
    message_lower = message.lower()
    
    # Si la consulta es muy corta, asumir que es válida
    if len(message.split()) < 3:
        return True, ""
    
    # Verificar si contiene al menos una palabra financiera
    has_financial_keyword = any(kw in message_lower for kw in financial_keywords)
    
    if not has_financial_keyword:
        return False, "La consulta no parece estar relacionada con finanzas."
    
    return True, ""