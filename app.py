import os
from dotenv import load_dotenv
import chainlit as cl

# Importa librerías de LangChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough

# Librerías para RAG
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnableParallel

# Módulos personalizados
from rag_manager import initialize_vector_store
import security
from bcrp_api import get_economic_context, BCRPClient


# --- 1. CONFIGURACIÓN ---
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Por favor configura tu OPENAI_API_KEY en el archivo .env")

# --- 2. DEFINICIÓN DEL MODELO Y PROMPT ---
llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)

system_prompt_with_rag = """
Eres "FinanBot", un Asesor Financiero experto y empático especializado en el mercado bancario de Perú. Tu misión es democratizar la asesoría financiera, ayudando a los usuarios a mejorar su salud económica y recomendando productos bancarios adecuados a su perfil.

**IMPORTANTE**: Tienes acceso a:
1. Documentos actualizados sobre productos financieros (si están disponibles)
2. Datos económicos en tiempo real del BCRP (Banco Central de Reserva del Perú)

INSTRUCCIONES DE COMPORTAMIENTO:

1.  **Uso de Información Contextual**:
    * Cuando recibas contexto de documentos (sección CONTEXTO), úsalo prioritariamente para responder.
    * Si el contexto contiene datos del BCRP (tipo de cambio, tasas, inflación), cítalos explícitamente con la fuente.
    * Si el contexto contiene tasas específicas, montos o condiciones de productos bancarios, cítalos con precisión.
    * Si el contexto no es suficiente, complementa con tu conocimiento general pero SIEMPRE indica cuándo estás especulando.

2.  **Datos Económicos del BCRP**:
    * Cuando el contexto incluya datos del BCRP, úsalos para dar recomendaciones más precisas.
    * Ejemplo: "Según el BCRP, el tipo de cambio actual es S/ 3.75, por lo que si buscas ahorrar en dólares..."
    * Los datos del BCRP son ACTUALES y confiables - úsalos con prioridad sobre estimaciones.

3.  **Perfilamiento Activo**:
    * No des consejos genéricos. Antes de recomendar, indaga sutilmente sobre: Edad, nivel de ingresos (rango), deudas actuales (montos), carga familiar y meta financiera (ahorro, inversión, compra de deuda, vivienda).
    * Si el usuario es conservador, prioriza Depósitos a Plazo Fijo o Cuentas de Ahorro de alto rendimiento.
    * Si el usuario busca liquidez, sugiere Cuentas de Ahorro transaccionales o Fondos Mutuos de corto plazo.

4.  **Contexto Local (Perú) y Educación**:
    * Habla en Soles (PEN) y Dólares (USD).
    * **CRÍTICO**: Al hablar de ahorros/inversiones, explica y menciona la **TREA** (Tasa de Rendimiento Efectivo Anual).
    * **CRÍTICO**: Al hablar de préstamos/créditos, explica y menciona la **TCEA** (Tasa de Costo Efectivo Anual).
    * Explica términos locales si es necesario: CTS, Gratificación, AFP, ITF, Plin/Yape.
    * Usa datos actualizados del BCRP cuando sea relevante (tipo de cambio, inflación, tasas).

5.  **Tono y Estilo**:
    * Profesional, cercano y alentador. Usa "Tú" o "Usted" según la formalidad del usuario, pero mantén el respeto.
    * Evita la jerga bancaria compleja sin explicarla. Ejemplo: "Tu score crediticio" -> "Tu puntaje en el sistema financiero (como Infocorp)".

6.  **Recomendación de Productos**:
    * Utiliza la información del perfilamiento activo Y del contexto documental Y de los datos del BCRP.
    * Conecta la necesidad con el producto.
    * Puedes recomendar productos bancarios conocidos del mercado peruano (BCP, Interbank, BBVA, Scotiabank).
    * SIEMPRE aclara que las tasas y condiciones están sujetas a evaluación crediticia y que debe verificar en los bancos.

7.  **Restricciones de Seguridad**:
    * Si inventas tasas, di claramente "tasas referenciales estimadas" o "sujetas a evaluación".
    * Aclara siempre que eres una IA de orientación y que la aprobación final depende de la entidad financiera.
    * Si detectas estrés financiero grave (deudas impagables), sugiere consolidación de deuda o asesoría legal con empatía.

--- CONTEXTO DE DOCUMENTOS Y DATOS ECONÓMICOS ---
{context}
--- FIN DEL CONTEXTO ---

TU OBJETIVO FINAL:
Que el usuario termine la conversación sintiéndose más inteligente financieramente y con una hoja de ruta clara sobre qué producto contratar. Antes de responder, DEBES pensar paso a paso.
"""

# Prompt con placeholders para RAG y conversación
prompt_with_rag = ChatPromptTemplate.from_messages([
    ("system", system_prompt_with_rag),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# --- 4. FUNCIONES AUXILIARES PARA EL CHAIN ---
def format_docs(docs):
    """Formatea los documentos recuperados para el prompt"""
    if not docs:
        return "No se encontró información relevante en los documentos."
    return "\n\n".join([f"Documento {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])

# --- 5. GESTIÓN DE EVENTOS CHAINLIT ---

@cl.on_chat_start
async def on_chat_start():
    """
    Se ejecuta una vez cuando un nuevo usuario abre la página.
    Inicializa RAG y memoria conversacional.
    """
    # Mostrar mensaje de carga
    loading_msg = cl.Message(content="🔧 Inicializando sistema de conocimiento...")
    await loading_msg.send()
    
    # 1. Inicializar Vector Store (RAG)
    retriever = initialize_vector_store()
    
    # Remover mensaje de carga
    await loading_msg.remove()
    
    if retriever is None:
        # Mostrar advertencia si no hay PDFs
        await cl.Message(
            content="⚠️ **Advertencia**: No se encontraron documentos PDF. "
                    "FinanBot funcionará con conocimiento base y datos del BCRP.\n\n"
                    f"💡 Para activar RAG, agrega PDFs en la carpeta `./documentos_financieros` y reinicia."
        ).send()
        
        # Chain sin RAG pero CON datos del BCRP
        def add_bcrp_only_context(inputs):
            """Agrega contexto del BCRP"""
            query = inputs.get("input", "")
            history = inputs.get("history", [])
            
            context_parts = ["No hay documentos PDF disponibles."]
            
            # Obtener datos económicos del BCRP si es relevante
            bcrp_context = get_economic_context(query)
            if bcrp_context:
                context_parts.append(bcrp_context)
            
            return {
                "context": "\n\n".join(context_parts),
                "input": query,
                "history": history
            }
        
        chain = (
            add_bcrp_only_context
            | prompt_with_rag 
            | llm 
            | StrOutputParser()
        )
        
    else:
        await cl.Message(content="✅ Sistema de conocimiento activado (RAG + BCRP)").send()
        
        # Función para agregar contexto RAG + BCRP
        def add_rag_and_bcrp_context(inputs):
            """
            Agrega contexto de RAG + BCRP al input.
            RunnableWithMessageHistory ya habrá agregado 'history'.
            """
            query = inputs.get("input", "")
            history = inputs.get("history", [])
            
            context_parts = []
            
            # 1. Recuperar documentos relevantes (RAG)
            docs = retriever.invoke(query)
            rag_context = format_docs(docs)
            context_parts.append(rag_context)
            
            # 2. Obtener datos económicos del BCRP si es relevante
            bcrp_context = get_economic_context(query)
            if bcrp_context:
                context_parts.append(bcrp_context)
            
            # Retornar todo: context, input, history
            return {
                "context": "\n\n".join(context_parts),
                "input": query,
                "history": history
            }
        
        # Chain con RAG + BCRP: primero agrega contexto, luego genera respuesta
        chain = (
            add_rag_and_bcrp_context
            | prompt_with_rag 
            | llm 
            | StrOutputParser()
        )
    
    # 2. Configurar memoria conversacional
    cl.user_session.set("memory", ChatMessageHistory())
    
    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        return cl.user_session.get("memory")
    
    # 3. Crear agente con historial
    # NOTA: RunnableWithMessageHistory inyecta automáticamente 'history'
    conversational_agent = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    
    cl.user_session.set("agent", conversational_agent)
    
    # 4. Mensaje de Bienvenida
    welcome_msg = (
        "🧠 **FinanBot**: Bienvenido, soy tu asesor financiero especializado en Perú.\n\n"
        "📊 **Capacidades activas:**\n"
        "  • Documentos actualizados sobre productos financieros\n"
        "  • Datos económicos en tiempo real del BCRP\n"
        "  • Sistema de seguridad para tu protección\n\n"
        "💡 **Puedo ayudarte con:**\n"
        "  • Tipo de cambio actual (datos en vivo del BCRP)\n"
        "  • Tasas de interés (TAMN, TAMEX, TCEA, TREA)\n"
        "  • Recomendaciones personalizadas de productos\n"
        "  • Inflación y datos macroeconómicos\n\n"
        "¿En qué puedo ayudarte hoy?"
    )
    await cl.Message(content=welcome_msg).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Se ejecuta cada vez que el usuario envía un mensaje.
    Incluye validaciones de seguridad.
    """
    # ========================================
    # PASO 1: VALIDACIÓN DE SEGURIDAD - INPUT
    # ========================================
    
    # Sanitizar datos sensibles del mensaje
    sanitized_message = security.sanitize_financial_data(message.content)
    
    # Verificar palabras/patrones prohibidos
    is_blocked, tipo, detalle = security.check_input(sanitized_message)
    
    if is_blocked:
        # Registrar evento de seguridad
        security.log_security_event(
            event_type="input_blocked",
            user_message=message.content,
            blocked_content=detalle
        )
        
        # Enviar respuesta de bloqueo
        blocked_response = security.get_random_response(security.responses_input_blocked)
        await cl.Message(content=f"⚠️ {blocked_response}").send()
        return
    
    # Validar contexto financiero (opcional - comentado para permitir más flexibilidad)
    # is_valid_context, reason = security.validate_financial_context(sanitized_message)
    # 
    # if not is_valid_context:
    #     await cl.Message(
    #         content="🤔 Parece que tu consulta no está relacionada con finanzas. "
    #                 "Soy un asesor financiero especializado. ¿Puedo ayudarte con temas de "
    #                 "ahorro, inversión, préstamos o productos bancarios?"
    #     ).send()
    #     return
    
    # ========================================
    # PASO 2: PROCESAR CON EL AGENTE
    # ========================================
    
    agent = cl.user_session.get("agent")
    msg = cl.Message(content="")
    
    # Acumular la respuesta completa para validarla
    full_response = ""
    
    async for chunk in agent.astream(
        {"input": sanitized_message},
        config={"configurable": {"session_id": "current_session"}}
    ):
        full_response += chunk
        await msg.stream_token(chunk)
    
    # ========================================
    # PASO 3: VALIDACIÓN DE SEGURIDAD - OUTPUT
    # ========================================
    
    is_blocked_out, tipo_out, detalle_out = security.check_output(full_response)
    
    if is_blocked_out:
        # Registrar evento de seguridad
        security.log_security_event(
            event_type="output_blocked",
            user_message=message.content,
            blocked_content=detalle_out
        )
        
        # Eliminar la respuesta bloqueada
        await msg.remove()
        
        # Enviar respuesta de bloqueo
        blocked_response = security.get_random_response(security.responses_output_blocked)
        await cl.Message(content=f"⚠️ {blocked_response}").send()
        return
    
    # ========================================
    # PASO 4: ENVIAR RESPUESTA VALIDADA
    # ========================================
    
    await msg.send()