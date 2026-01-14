"""
Módulo de Gestión RAG (Retrieval-Augmented Generation)
Maneja la carga, procesamiento y consulta de documentos PDF
"""

import os
from typing import Optional, List
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# =========================================================================
# CONFIGURACIÓN
# =========================================================================

class RAGConfig:
    """Configuración del sistema RAG"""
    PDF_DIRECTORY = "./documentos_financieros"
    CHROMA_DB_PATH = "./chroma_db"
    EMBEDDING_MODEL = "text-embedding-3-small"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    RETRIEVER_K = 4  # Número de documentos a recuperar


# =========================================================================
# FUNCIÓN PRINCIPAL PARA APP.PY
# =========================================================================

def initialize_vector_store():
    """
    Función principal para inicializar el vector store.
    Compatible con app.py existente.
    
    Carga PDFs, los divide en chunks y crea/carga el vector store.
    Solo procesa PDFs si el vector store no existe.
    
    Returns:
        Retriever configurado o None si no hay documentos
    """
    config = RAGConfig()
    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    
    # Si ya existe la base de datos, la cargamos
    if os.path.exists(config.CHROMA_DB_PATH):
        print("📚 Cargando base de conocimiento existente...")
        vectorstore = Chroma(
            persist_directory=config.CHROMA_DB_PATH,
            embedding_function=embeddings
        )
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": config.RETRIEVER_K}
        )
    
    # Si no existe, procesamos los PDFs
    print("🔄 Procesando documentos PDF...")
    
    # Verificar que exista la carpeta de PDFs
    if not os.path.exists(config.PDF_DIRECTORY):
        os.makedirs(config.PDF_DIRECTORY)
        print(f"⚠️  Carpeta '{config.PDF_DIRECTORY}' creada. Por favor, agrega tus PDFs ahí.")
        return None
    
    # Cargar PDFs
    loader = PyPDFDirectoryLoader(config.PDF_DIRECTORY)
    documents = loader.load()
    
    if not documents:
        print(f"⚠️  No se encontraron PDFs en '{config.PDF_DIRECTORY}'")
        return None
    
    print(f"✅ {len(documents)} páginas cargadas")
    
    # Dividir en chunks optimizados para contenido financiero
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    splits = text_splitter.split_documents(documents)
    print(f"📄 {len(splits)} fragmentos creados")
    
    # Crear vector store
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=config.CHROMA_DB_PATH
    )
    
    print("💾 Base de conocimiento guardada exitosamente")
    
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": config.RETRIEVER_K}
    )


# Alias para compatibilidad
rag_manager = initialize_vector_store


# =========================================================================
# CLASE PRINCIPAL RAG MANAGER (Alternativa avanzada)
# =========================================================================

class RAGManager:
    """Gestiona todo el ciclo de vida del sistema RAG"""
    
    def __init__(self, config: RAGConfig = None):
        """
        Inicializa el RAG Manager
        
        Args:
            config: Configuración personalizada (opcional)
        """
        self.config = config or RAGConfig()
        self.embeddings = OpenAIEmbeddings(model=self.config.EMBEDDING_MODEL)
        self.vectorstore = None
        self.retriever = None
    
    def initialize(self) -> bool:
        """
        Inicializa el vector store
        Carga existente o crea uno nuevo procesando PDFs
        
        Returns:
            True si se inicializó correctamente, False si no hay documentos
        """
        # Si ya existe la base de datos, cargarla
        if os.path.exists(self.config.CHROMA_DB_PATH):
            print("📚 Cargando base de conocimiento existente...")
            self.vectorstore = Chroma(
                persist_directory=self.config.CHROMA_DB_PATH,
                embedding_function=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": self.config.RETRIEVER_K}
            )
            return True
        
        # Si no existe, procesar PDFs
        return self._process_documents()
    
    def _process_documents(self) -> bool:
        """
        Procesa documentos PDF y crea el vector store
        
        Returns:
            True si se procesaron documentos exitosamente
        """
        print("🔄 Procesando documentos PDF...")
        
        # Verificar que exista la carpeta de PDFs
        if not os.path.exists(self.config.PDF_DIRECTORY):
            os.makedirs(self.config.PDF_DIRECTORY)
            print(f"⚠️  Carpeta '{self.config.PDF_DIRECTORY}' creada.")
            print("   Por favor, agrega tus PDFs ahí y reinicia.")
            return False
        
        # Cargar PDFs
        loader = PyPDFDirectoryLoader(self.config.PDF_DIRECTORY)
        documents = loader.load()
        
        if not documents:
            print(f"⚠️  No se encontraron PDFs en '{self.config.PDF_DIRECTORY}'")
            return False
        
        print(f"✅ {len(documents)} páginas cargadas")
        
        # Dividir en chunks
        splits = self._split_documents(documents)
        print(f"📄 {len(splits)} fragmentos creados")
        
        # Crear vector store
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.config.CHROMA_DB_PATH
        )
        
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.config.RETRIEVER_K}
        )
        
        print("💾 Base de conocimiento guardada exitosamente")
        return True
    
    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Divide documentos en chunks optimizados
        
        Args:
            documents: Lista de documentos a dividir
            
        Returns:
            Lista de documentos divididos en chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return text_splitter.split_documents(documents)
    
    def retrieve_context(self, query: str) -> str:
        """
        Recupera contexto relevante para una consulta
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Contexto formateado como string
        """
        if not self.retriever:
            return "No hay documentos disponibles."
        
        try:
            docs = self.retriever.invoke(query)
            return self._format_docs(docs)
        except Exception as e:
            print(f"Error recuperando contexto: {e}")
            return "Error al recuperar documentos."
    
    def _format_docs(self, docs: List[Document]) -> str:
        """
        Formatea documentos recuperados para el prompt
        
        Args:
            docs: Lista de documentos
            
        Returns:
            String formateado con el contenido de los documentos
        """
        if not docs:
            return "No se encontró información relevante en los documentos."
        
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Desconocido')
            page = doc.metadata.get('page', 'N/A')
            
            formatted.append(
                f"--- Documento {i} ---\n"
                f"Fuente: {source} (Página {page})\n"
                f"Contenido:\n{doc.page_content}\n"
            )
        
        return "\n".join(formatted)
    
    def get_retriever(self):
        """
        Obtiene el retriever configurado
        
        Returns:
            Retriever de LangChain o None si no está inicializado
        """
        return self.retriever
    
    def reload_documents(self) -> bool:
        """
        Recarga todos los documentos desde cero
        Útil cuando se agregan nuevos PDFs
        
        Returns:
            True si se recargaron exitosamente
        """
        import shutil
        
        # Eliminar base de datos existente
        if os.path.exists(self.config.CHROMA_DB_PATH):
            shutil.rmtree(self.config.CHROMA_DB_PATH)
        
        # Reinicializar
        return self._process_documents()
    
    def get_document_stats(self) -> dict:
        """
        Obtiene estadísticas sobre los documentos cargados
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.vectorstore:
            return {
                "initialized": False,
                "total_chunks": 0,
                "sources": []
            }
        
        try:
            # Obtener una muestra de documentos
            sample_docs = self.vectorstore.similarity_search("", k=100)
            
            # Extraer fuentes únicas
            sources = set()
            for doc in sample_docs:
                source = doc.metadata.get('source', 'Desconocido')
                sources.add(source)
            
            return {
                "initialized": True,
                "total_chunks": len(sample_docs),
                "sources": list(sources),
                "retriever_k": self.config.RETRIEVER_K
            }
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                "initialized": True,
                "error": str(e)
            }


# =========================================================================
# FUNCIONES DE UTILIDAD
# =========================================================================

def create_rag_chain_function(rag_manager: RAGManager):
    """
    Crea una función para integrar RAG en un chain de LangChain
    
    Args:
        rag_manager: Instancia de RAGManager
        
    Returns:
        Función que agrega contexto RAG a los inputs
    """
    def add_rag_context(inputs: dict) -> dict:
        """
        Agrega contexto de RAG al input del chain
        
        Args:
            inputs: Diccionario con 'input' y 'history'
            
        Returns:
            Diccionario con 'context', 'input' y 'history'
        """
        query = inputs.get("input", "")
        history = inputs.get("history", [])
        
        # Recuperar contexto relevante
        context = rag_manager.retrieve_context(query)
        
        return {
            "context": context,
            "input": query,
            "history": history
        }
    
    return add_rag_context


def get_empty_context_function():
    """
    Crea una función que retorna contexto vacío
    Útil cuando no hay RAG disponible
    
    Returns:
        Función que agrega contexto vacío
    """
    def add_empty_context(inputs: dict) -> dict:
        """Agrega contexto vacío"""
        return {
            "context": "No hay documentos disponibles.",
            "input": inputs.get("input", ""),
            "history": inputs.get("history", [])
        }
    
    return add_empty_context