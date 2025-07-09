import streamlit as st
import tempfile
import os
from typing import List
from langchain_core.documents import Document

# Import our modules
from agent.graph import get_answer
from agent.vectorstore import LANGCHAIN_VECTOR_STORES, load_document_and_chunk
from config import CONFIG
from utils import log

def add_documents_to_vectorstore(documents: List[Document], index_name: str) -> bool:
    """
    Add documents to the specified Pinecone vectorstore.
    
    Args:
        documents: List of Document objects to add
        index_name: Name of the Pinecone index to add documents to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if index_name not in LANGCHAIN_VECTOR_STORES:
            log.error(f"Vectorstore for index '{index_name}' not found")
            return False
            
        vectorstore = LANGCHAIN_VECTOR_STORES[index_name]
        
        # Extract texts and metadatas from documents
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Add documents to vectorstore
        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        
        log.success(f"Successfully added {len(documents)} documents to index '{index_name}'")
        return True
        
    except Exception as e:
        log.error(f"Error adding documents to vectorstore '{index_name}': {e}")
        return False

def main():
    st.set_page_config(
        page_title="Chatbot Tư Vấn Tuyển Sinh HANU",
        page_icon="static/logo.png",
        layout="centered",  # Changed from wide to centered for better mobile experience
        initial_sidebar_state="collapsed"  # Start with sidebar collapsed on mobile
    )
    
    # Enhanced responsive CSS for mobile-first design
    st.markdown("""
    <style>
    /* Mobile-first responsive design */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Header styling */
    .header-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
        padding: 0.75rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .header-logo {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid white;
    }
    
    .header-text h1 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: bold;
    }
    
    .header-text p {
        margin: 0;
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Chat message styling */
    .stChatMessage {
        margin-bottom: 1rem !important;
        border-radius: 10px !important;
        padding: 0.75rem !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    
    .stChatMessage[data-testid="chat-message-user"] {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%) !important;
        color: white !important;
        margin-left: 2rem !important;
    }
    
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: white !important;
        border: 1px solid #e0e0e0 !important;
        margin-right: 2rem !important;
    }
    
    /* Chat input styling - NOT fixed position for mobile compatibility */
    .stChatInput {
        position: relative !important;
        margin-top: 1rem !important;
        padding: 0.5rem !important;
        border-radius: 25px !important;
        box-shadow: 0 4px 15px rgba(0,123,255,0.2) !important;
    }
    
    .stChatInput > div {
        max-width: 100% !important;
        margin: 0 !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Sidebar improvements */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .header-container {
            padding: 0.5rem;
            gap: 0.75rem;
        }
        
        .header-text h1 {
            font-size: 1.2rem;
        }
        
        .header-text p {
            font-size: 0.9rem;
        }
        
        .stChatMessage[data-testid="chat-message-user"] {
            margin-left: 1rem !important;
        }
        
        .stChatMessage[data-testid="chat-message-assistant"] {
            margin-right: 1rem !important;
        }
        
        .stChatMessage {
            margin-bottom: 0.75rem !important;
            padding: 0.5rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .header-logo {
            width: 50px;
            height: 50px;
        }
        
        .header-text h1 {
            font-size: 1.1rem;
        }
        
        .header-text p {
            font-size: 0.85rem;
        }
        
        .header-container {
            padding: 0.4rem;
        }
        
        .stChatMessage[data-testid="chat-message-user"] {
            margin-left: 0.5rem !important;
        }
        
        .stChatMessage[data-testid="chat-message-assistant"] {
            margin-right: 0.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with improved responsive design
    st.markdown("""
    <div class="header-container">
        <img src="static/logo.png" class="header-logo" alt="HANU Logo">
        <div class="header-text">
            <h1>🎓 Đại Học Hà Nội (HANU)</h1>
            <p>💬 Chatbot Tư Vấn Tuyển Sinh</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick action buttons for common questions
    st.markdown("### 🚀 Câu Hỏi Thường Gặp")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Thông tin tuyển sinh 2025", use_container_width=True):
            st.session_state.quick_question = "Cho tôi biết thông tin tuyển sinh HANU năm 2025?"
        
        if st.button("🏫 Lịch sử trường", use_container_width=True):
            st.session_state.quick_question = "Hãy kể cho tôi về lịch sử hình thành của HANU"
    
    with col2:
        if st.button("💰 Học phí HANU", use_container_width=True):
            st.session_state.quick_question = "Học phí của HANU là bao nhiêu?"
        
        if st.button("🎓 Học bổng", use_container_width=True):
            st.session_state.quick_question = "HANU có những hỗ trợ học bổng nào?"
    
    st.divider()
    
    # Sidebar for document management - improved for mobile
    with st.sidebar:
        st.markdown("### 📄 Quản Lý Tài Liệu")
        
        # Database selection
        st.markdown("**📊 Chọn Cơ Sở Dữ Liệu**")
        database_options = {config.human_description: config.pinecone_index_name 
                          for config in CONFIG.RETRIEVER_TOOL_CONFIGS}
        
        selected_db_description = st.selectbox(
            "Cơ sở dữ liệu:",
            options=list(database_options.keys()),
            label_visibility="collapsed"
        )
        selected_db_name = database_options[selected_db_description]
        
        st.success(f"✅ {selected_db_description}")
        
        # File upload
        st.markdown("**📤 Tải Tệp Lên**")
        uploaded_file = st.file_uploader(
            "Chọn file .txt:",
            type=['txt'],
            help="Chỉ hỗ trợ file .txt",
            label_visibility="collapsed"
        )
        
        # Add document button
        if st.button("➕ Thêm Tài Liệu", disabled=not uploaded_file, use_container_width=True, type="primary"):
            if uploaded_file is not None:
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue().decode("utf-8"))
                        tmp_file_path = tmp_file.name
                    
                    # Load and chunk the document
                    with st.spinner("⏳ Đang xử lý..."):
                        documents = load_document_and_chunk(tmp_file_path)
                        
                        # Add to vectorstore
                        success = add_documents_to_vectorstore(documents, selected_db_name)
                        
                        if success:
                            st.success(f"✅ Đã thêm {len(documents)} đoạn văn bản!")
                        else:
                            st.error("❌ Có lỗi xảy ra!")
                    
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        
        st.divider()
        
        # Database info - collapsed by default for mobile
        with st.expander("ℹ️ Thông Tin CSDL"):
            for config in CONFIG.RETRIEVER_TOOL_CONFIGS:
                st.markdown(f"**📚 {config.human_description}**")
                st.caption(f"Index: {config.pinecone_index_name}")
                st.caption(config.tool_description)
                st.divider()
        
        # Usage instructions
        with st.expander("📖 Hướng Dẫn"):
            st.markdown("""
            **💬 Chat:**
            - Nhập câu hỏi hoặc dùng nút nhanh
            - Bot tự động tìm kiếm và trả lời
            
            **📤 Thêm tài liệu:**
            - Chọn cơ sở dữ liệu
            - Tải file .txt
            - Nhấn "Thêm Tài Liệu"
            """)
        
        # Clear chat button
        if st.button("🗑️ Xóa Chat", type="secondary", use_container_width=True):
            st.session_state.messages = []
            if 'quick_question' in st.session_state:
                del st.session_state.quick_question
            st.rerun()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        welcome_msg = """
        👋 **Xin chào! Chào mừng bạn đến với HANU!**
        
        Tôi là trợ lý AI của Đại học Hà Nội, sẵn sàng hỗ trợ bạn:
        
        🏫 **Thông tin về trường**  
        📋 **Tuyển sinh 2025**  
        📚 **Lịch sử và truyền thống**  
        💰 **Học phí & học bổng**  
        
        Hãy đặt câu hỏi hoặc sử dụng các nút gợi ý phía trên! 🚀
        """
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

    # Chat interface with improved design
    st.markdown("### 💬 Trò Chuyện")
    
    # Create a container for chat messages
    chat_container = st.container()
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Handle quick questions
    if "quick_question" in st.session_state:
        prompt = st.session_state.quick_question
        del st.session_state.quick_question
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get bot response
        with st.spinner("🤔 Đang suy nghĩ..."):
            try:
                response = get_answer(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"😔 Xin lỗi, tôi gặp lỗi: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()

    # Chat input - now properly positioned for mobile
    if prompt := st.chat_input("💭 Nhập câu hỏi của bạn..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get bot response
        with st.spinner("🤔 Đang suy nghĩ..."):
            try:
                response = get_answer(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"😔 Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()

if __name__ == "__main__":
    main() 