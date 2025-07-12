import config.CONFIG as CONFIG
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from utils import log
from pinecone import Pinecone, ServerlessSpec
from langchain_core.documents import Document
from langchain_unstructured import UnstructuredLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from unstructured.cleaners.core import clean_extra_whitespace
from typing import List, Dict

# Initialize OpenAI embeddings
try:
    openai_embeddings = OpenAIEmbeddings(
        model=CONFIG.OPENAI_EMBEDDING_MODEL,
        api_key=CONFIG.OPENAI_API_KEY
    )
    log.success("OpenAI embeddings initialized successfully")
except Exception as e:
    log.error(f"Error initializing OpenAI embeddings: {e}")
    raise e

# Initialize Pinecone client
try:
    pinecone_client = Pinecone(api_key=CONFIG.PINECONE_API_KEY)
    log.success("Pinecone client initialized successfully")
except Exception as e:
    log.error(f"Error initializing Pinecone client: {e}")
    raise e

def _create_langchain_vector_stores() -> Dict[str, PineconeVectorStore]:
    """
    Create LangChain PineconeVectorStore instances for each configured index.
    
    Returns:
        Dictionary mapping index names to PineconeVectorStore instances
    """
    langchain_vector_stores = {}
    
    for config in CONFIG.RETRIEVER_TOOL_CONFIGS:
        index_name = config.pinecone_index_name
        try:
            # Check if index exists, create if it doesn't
            if not pinecone_client.has_index(index_name):
                pinecone_client.create_index(
                    name=index_name,
                    dimension=CONFIG.PINECONE_EMBEDDING_DIMENSION,
                    metric='cosine',
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                log.success(f"Pinecone index '{index_name}' created successfully")
            else:
                log.success(f"Pinecone index '{index_name}' already exists")
            
            # Create LangChain vector store
            vector_store = PineconeVectorStore(
                index=pinecone_client.Index(index_name),
                embedding=openai_embeddings,
                text_key="text"
            )
            langchain_vector_stores[index_name] = vector_store
            log.success(f"LangChain vector store created for index '{index_name}'")
            
        except Exception as e:
            log.error(f"Error creating vector store for index '{index_name}': {e}")
            raise e
    
    return langchain_vector_stores

# Global dictionary of LangChain vector stores
LANGCHAIN_VECTOR_STORES = _create_langchain_vector_stores()

def load_document_and_chunk(file_path: str) -> List[Document]:
    """
    Load a text file and chunk it for processing.
    
    Args:
        file_path: Path to the text file to load
        
    Returns:
        List of Document objects containing the chunked content
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: If there's an error loading or processing the file
    """
    try:
        if not file_path.endswith('.txt'):
            log.warning(f"File {file_path} is not a .txt file, proceeding anyway")
        
        log.information(f"Loading document from: {file_path}")
        
        document_loader = UnstructuredLoader(
            file_path, 
            post_processors=[clean_extra_whitespace],   
        )
        
        documents = document_loader.load()
        
        full_text = " ".join([doc.page_content for doc in documents])
        documents = [Document(page_content=full_text, metadata={"source": file_path})]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG.CHUNK_SIZE,      # Kích thước tối đa của mỗi chunk (tính bằng ký tự)
            chunk_overlap=CONFIG.CHUNK_OVERLAP,    # Số ký tự chồng lấn giữa các chunk liên tiếp
            length_function=len,
            is_separator_regex=False,
        )
        document_chunks = text_splitter.split_documents(documents)
        
        log.success(f"Successfully loaded {len(document_chunks)} document chunks from {file_path}")
        return document_chunks
        
    except FileNotFoundError:
        log.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        log.error(f"Error loading document from {file_path}", e)
        raise




