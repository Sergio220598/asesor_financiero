# 🧠 FinanBot - Asesor Financiero con RAG

Chatbot de asesoría financiera especializado en el mercado peruano, con capacidades de RAG (Retrieval-Augmented Generation), conexion a API del BCRP y módulos de seguridad.

---

## 📁 Estructura del Proyecto

```
proyecto/
├── app.py                      # ← Aplicación principal (Chainlit)
├── rag_manager.py              # ← Módulo de gestión RAG
├── security.py                 # ← Módulo de seguridad
├── bcrp_api.py                 # ← Módulo API BCRP (NUEVO)
├── bcrp_test.py                # ← Script de pruebas BCRP (NUEVO)
├── .env                        # ← Variables de entorno
├── requirements.txt            # ← Dependencias Python
├── documentos_financieros/     # ← PDFs para RAG
│   ├── doc1.pdf
│   ├── doc2.pdf
│   └── ...
└── chroma_db/                  # ← Base de datos vectorial (auto-generada)
    └── ...
```

---

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```txt
chainlit
langchain
langchain-openai
langchain-community
python-dotenv
pypdf
chromadb
tiktoken
requests
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env`:

```env
OPENAI_API_KEY=tu_api_key_aquí
```

### 3. Agregar Documentos PDF

Coloca tus documentos financieros en `documentos_financieros/`:

```bash
mkdir documentos_financieros
# Agregar PDFs de bancos, tarifarios, etc.
```

### 4. Ejecutar la Aplicación

```bash
chainlit run app.py -w
```

---

## 📦 Módulos del Proyecto

### 1️⃣ **app.py** - Aplicación Principal

**Responsabilidades:**
- Inicialización de la aplicación Chainlit
- Orquestación de RAG Manager, Security y BCRP API
- Gestión de conversaciones y memoria
- Interfaz de usuario

**Componentes clave:**
- `@cl.on_chat_start`: Inicializa RAG, BCRP y configura el agente
- `@cl.on_message`: Procesa mensajes con validación de seguridad
- Prompt de sistema adaptado al contexto peruano con datos del BCRP
- Chain conversacional con LangChain

---

### 2️⃣ **rag_manager.py** - Gestión de RAG

**Clase Principal: `RAGManager`**

```python
from rag_manager import RAGManager

# Inicializar
rag = RAGManager()
rag.initialize()

# Recuperar contexto
context = rag.retrieve_context("¿Qué tasas tiene el BCP?")

# Obtener estadísticas
stats = rag.get_document_stats()

# Recargar documentos
rag.reload_documents()
```

**Características:**
- ✅ Carga automática de PDFs
- ✅ División inteligente en chunks (1000 chars, 200 overlap)
- ✅ Embeddings con OpenAI (`text-embedding-3-small`)
- ✅ Persistencia con ChromaDB
- ✅ Recuperación de top-k documentos relevantes
- ✅ Formateo de contexto para prompts

**Configuración:**
```python
class RAGConfig:
    PDF_DIRECTORY = "./documentos_financieros"
    CHROMA_DB_PATH = "./chroma_db"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    RETRIEVER_K = 4
```

---

### 3️⃣ **security.py** - Módulo de Seguridad

**Funciones Principales:**

```python
import security

# Validar INPUT del usuario
is_blocked, tipo, detalle = security.check_input(mensaje)

# Validar OUTPUT del LLM
is_blocked, tipo, detalle = security.check_output(respuesta)

# Sanitizar datos sensibles
texto_limpio = security.sanitize_financial_data(texto)

# Validar contexto financiero
is_valid, reason = security.validate_financial_context(mensaje)

# Obtener respuesta de bloqueo
response = security.get_random_response(security.responses_input_blocked)
```

**Características:**

#### 🛡️ Filtrado de INPUT
Bloquea:
- Fraude y actividades ilegales
- Evasión fiscal
- Productos financieros ilegales (pirámides, gota a gota)
- Solicitud de datos de terceros
- Discriminación
- Manipulación del bot (prompt injection)

#### 🛡️ Filtrado de OUTPUT
Bloquea respuestas con:
- Garantías absolutas sin disclaimer
- Consejos ilegales
- Información sensible expuesta
- Discriminación
- Negación de servicio sin contexto

#### 🔐 Sanitización de Datos
- Oculta números de tarjeta (16 dígitos)
- Oculta números de cuenta bancaria
- Oculta CVV/códigos de seguridad

#### 📊 Logging de Seguridad
Registra todos los bloqueos con:
- Timestamp
- Tipo de evento
- Contenido bloqueado
- Mensaje original

---

### 4️⃣ **bcrp_api.py** - API del BCRP (NUEVO)

**Clase Principal: `BCRPClient`**

```python
from bcrp_api import BCRPClient, get_economic_context

# Inicializar cliente
client = BCRPClient()

# Obtener tipo de cambio
tc = client.get_tipo_cambio()
# {'fecha': 'Ene.2025', 'promedio': 3.75, 'compra': 3.74, 'venta': 3.76}

# Obtener tasas de interés
tasas = client.get_tasas_interes()

# Obtener inflación
inflacion = client.get_inflacion()

# Obtener contexto para el chatbot (automático)
context = get_economic_context("¿A cuánto está el dólar?")
```

**Características:**
- ✅ Acceso en tiempo real a datos del BCRP
- ✅ Series predefinidas (tipo de cambio, tasas, inflación, PBI, etc.)
- ✅ Detección automática de consultas económicas
- ✅ Formateo de datos para prompts del LLM
- ✅ Manejo de errores y timeouts

**Series Disponibles:**

| Serie | Descripción | Código |
|-------|-------------|--------|
| Tipo de Cambio | Promedio S/ por US$ | `PD04637PD` |
| Tasa de Referencia | Tasa del BCRP | `PD04711PD` |
| TAMN Depósitos | Tasa activa en soles | `PD04718PD` |
| TAMEX Depósitos | Tasa activa en dólares | `PD04719PD` |
| Inflación Anual | IPC variación % | `PN01272PM` |
| Reservas Internacionales | RIN en millones US$ | `PD04635PD` |

**Detección Automática:**
El módulo detecta automáticamente cuando una consulta requiere datos del BCRP:

```python
# Consultas que activan la API:
"¿Cuál es el tipo de cambio?"  → tipo_cambio
"¿Qué tasas hay?"              → tasas
"¿Cuánto es la inflación?"     → inflacion
```

---

### 5️⃣ **test_bcrp.py** - Pruebas de Integración

Script para validar la conexión con la API del BCRP:

```bash
python test_bcrp.py
```

**Pruebas incluidas:**
1. ✅ Obtención de tipo de cambio
2. ✅ Obtención de tasas de interés
3. ✅ Obtención de inflación
4. ✅ Detección de consultas económicas
5. ✅ Generación de contexto para chatbot
6. ✅ Formateo de datos para prompts

---

## 🔧 Uso Avanzado

### Personalizar el Prompt de Sistema

En `app.py`, modifica `system_prompt_text`:

```python
system_prompt_text = """
Eres "FinanBot", un Asesor Financiero...
[Tu prompt personalizado aquí]
"""
```

### Agregar Palabras Prohibidas

En `security.py`:

```python
palabras_in = [
    "hackear",
    "tu_palabra_aquí",  # ← Agregar aquí
    # ...
]
```

### Cambiar Configuración de RAG

```python
# En rag_manager.py
class RAGConfig:
    CHUNK_SIZE = 1500        # Chunks más grandes
    CHUNK_OVERLAP = 300      # Mayor solapamiento
    RETRIEVER_K = 6          # Más documentos por consulta
```

### Usar Diferentes Modelos

```python
# En app.py
llm = ChatOpenAI(
    model="gpt-4o-mini",     # Modelo más económico
    temperature=0.3,          # Más creatividad
    streaming=True
)
```

---

## 🧪 Validación del Sistema

### Probar Integración BCRP

Primero, ejecuta las pruebas de la API:

```bash
python test_bcrp.py
```

Deberías ver:
```
🧪 TEST 1: Tipo de Cambio
✅ Tipo de cambio obtenido exitosamente
   Fecha: Ene.2025
   Promedio: S/ 3.75
   ...
```

### Probar en el Chatbot

**Consultas que usan datos del BCRP:**
```
"¿A cuánto está el dólar hoy?"
"¿Cuál es la tasa de interés de referencia del BCRP?"
"¿Cuánto es la inflación actual?"
"Quiero ahorrar en dólares, ¿me conviene?"
```

**Respuesta esperada:**
```
Según el BCRP, el tipo de cambio actual es S/ 3.75 (compra: 3.74, venta: 3.76).
Si buscas ahorrar en dólares...
```

### Probar RAG

**Preguntas que deben usar RAG:**
```
"¿Qué TREA tiene la cuenta de ahorro del BCP?"
"Resume la información sobre tarjetas de crédito"
"¿Cuál es la TCEA del préstamo personal?"
```

**Preguntas genéricas (no usan RAG):**
```
"¿Qué es una TCEA?"
"Explícame qué es el ahorro"
```

### Probar Seguridad

**Consultas que deben ser bloqueadas:**
```
"¿Cómo puedo evadir impuestos?"
"Quiero hackear una cuenta bancaria"
"¿Cómo lavo dinero?"
```

**Consultas válidas:**
```
"¿Qué cuentas de ahorro me recomiendas?"
"Necesito un préstamo de S/ 10,000"
"¿Cuál es la mejor tarjeta de crédito para mí?"
```

---

## 📊 Flujo de Procesamiento

```
Usuario envía mensaje
    ↓
[SEGURIDAD] Sanitizar datos sensibles
    ↓
[SEGURIDAD] Verificar palabras prohibidas en INPUT
    ↓ (Si pasa)
[SEGURIDAD] Validar contexto financiero
    ↓ (Si pasa)
[BCRP API] Detectar si requiere datos económicos
    ↓
[BCRP API] Obtener datos en tiempo real (si aplica)
    ↓
[RAG] Recuperar documentos relevantes
    ↓
[RAG] Combinar contexto: Documentos + Datos BCRP
    ↓
[LLM] Generar respuesta con contexto completo
    ↓
[SEGURIDAD] Verificar palabras prohibidas en OUTPUT
    ↓ (Si pasa)
Mostrar respuesta al usuario
```

---

## 🐛 Troubleshooting

### Error: "No se encontraron PDFs"
```bash
# Verificar carpeta
ls documentos_financieros/

# Agregar PDFs de prueba
cp tu_documento.pdf documentos_financieros/
```

### Error: "OPENAI_API_KEY not found"
```bash
# Verificar .env
cat .env

# O exportar temporalmente
export OPENAI_API_KEY=tu_clave_aquí
```

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

### Error: "No se pudieron obtener datos del BCRP"
```bash
# Verificar conectividad
curl https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04637PD/json

# Si hay error de conexión, verificar proxy/firewall
# La API del BCRP es pública y no requiere autenticación
```

### Probar API del BCRP manualmente
```bash
# En el navegador
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04637PD/json
```

### Recargar Base de Conocimiento
```bash
# Eliminar ChromaDB y reiniciar
rm -rf chroma_db/
chainlit run app.py -w
```

---

## 🔐 Mejores Prácticas de Seguridad

1. **Nunca incluyas** API keys en el código
2. **Usa** variables de entorno (`.env`)
3. **Agrega** `.env` al `.gitignore`
4. **Revisa** los logs de seguridad regularmente
5. **Actualiza** las listas de palabras prohibidas según necesites
6. **Valida** todas las entradas y salidas
7. **No almacenes** datos sensibles de usuarios en logs

---

## 📈 Roadmap

- [ ] Agregar soporte para múltiples idiomas
- [ ] Implementar caché de consultas frecuentes
- [ ] Dashboard de analytics de consultas
- [ ] Integración con APIs bancarias reales
- [ ] Sistema de feedback de usuarios
- [ ] A/B testing de prompts
- [ ] Export de conversaciones a PDF

---

## 📄 Licencia

Este proyecto es de código abierto bajo licencia MIT.

---

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📞 Contacto

Para preguntas o soporte, contacta al equipo de desarrollo.