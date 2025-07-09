from typing import Optional
import streamlit as st
import os
import json

@st.cache_data
def _load_pinecone_index_configs() -> dict:
    '''
    Load pinecone index configurations from JSON file
    '''
    _FILE_PATH = os.path.join(os.path.dirname(__file__), "pinecone_indexes.json")
    with open(_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    
    
@st.cache_data
def _get_secret(key: str) -> Optional[str]:
    """
    Safely retrieve API keys from Streamlit secrets.
    
    Args:
        key: The secret key to retrieve
        
    Returns:
        The secret value or None if not found
        
    Raises:
        ValueError: If the secret is required but not found
    """
    try:
        return st.secrets[key]
    except (AttributeError, KeyError):
        # For critical API keys, we should raise an error
        if key in ["PINECONE_API_KEY", "OPENAI_API_KEY", "ENTER_KEY"]:
            raise ValueError(f"Required API key not found: {key}. Please check your Streamlit secrets configuration.")
        return None

# API KEYS
PINECONE_API_KEY = _get_secret("PINECONE_API_KEY")
OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
ENTER_KEY = _get_secret("ENTER_KEY")

# PINECONE INDEX CONFIGURATIONS - Raw data from JSON file
PINECONE_INDEX_CONFIGS = _load_pinecone_index_configs()

# RETRIEVER TOOL CONFIGURATIONS - Configuration for creating retriever tools
class RetrieverToolConfig:
    """Configuration class for creating retriever tools from Pinecone indexes"""
    def __init__(self, index_name, tool_description, human_description):
        self.pinecone_index_name = index_name      # Name of Pinecone index 
        self.tool_name = index_name                # Name for the retriever tool
        self.tool_description = tool_description   # Description for LLM tool selection
        self.human_description = human_description # Human-readable description

RETRIEVER_TOOL_CONFIGS = [
    RetrieverToolConfig(
        index_name=index_config["name"],
        tool_description=index_config["description"],
        human_description=index_config["description_for_human"]
    )
    for index_config in PINECONE_INDEX_CONFIGS
]

# AGENT CONFIGURATION
MAX_QUESTION_REWRITES = 1
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
PINECONE_EMBEDDING_DIMENSION = 1536 # 1536 là embedding dimension của text-embedding-3-small
OPENAI_LLM_MODEL = "gpt-4o-mini"




