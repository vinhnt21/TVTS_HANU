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
        layout="wide"
    )
    
    # Custom CSS to make chat input sticky at bottom
    st.markdown("""
    <style>
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999 !important;
        background-color: white !important;
        padding: 10px !important;
        border-top: 1px solid #e0e0e0 !important;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1) !important;
    }
    
    .stChatInput > div {
        max-width: 800px !important;
        margin: 0 auto !important;
    }
    
    /* Add padding to bottom of chat messages to prevent overlap with fixed input */
    .main .block-container {
        padding-bottom: 100px !important;
    }
    
    /* Style for chat messages container */
    .stChatMessage {
        margin-bottom: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with logo
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image("static/logo.png", width=80)
    with col_title:
        st.title("Đại Học Hà Nội")
        st.subheader("Chatbot Tư Vấn Tuyển Sinh")
    
    st.markdown("---")
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("📄 Quản Lý Tài Liệu")
        
        # Database selection
        st.subheader("Chọn Cơ Sở Dữ Liệu")
        database_options = {config.human_description: config.pinecone_index_name 
                          for config in CONFIG.RETRIEVER_TOOL_CONFIGS}
        
        selected_db_description = st.selectbox(
            "Chọn cơ sở dữ liệu để thêm tài liệu:",
            options=list(database_options.keys())
        )
        selected_db_name = database_options[selected_db_description]
        
        st.info(f"Đã chọn: {selected_db_description}")
        
        # File upload
        st.subheader("Tải Tệp Lên")
        uploaded_file = st.file_uploader(
            "Chọn file text để thêm vào cơ sở dữ liệu:",
            type=['txt'],
            help="Chỉ hỗ trợ file .txt"
        )
        
        # Add document button
        if st.button("📤 Thêm Tài Liệu", disabled=not uploaded_file):
            if uploaded_file is not None:
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue().decode("utf-8"))
                        tmp_file_path = tmp_file.name
                    
                    # Load and chunk the document
                    with st.spinner("Đang xử lý tài liệu..."):
                        documents = load_document_and_chunk(tmp_file_path)
                        
                        # Add to vectorstore
                        success = add_documents_to_vectorstore(documents, selected_db_name)
                        
                        if success:
                            st.success(f"✅ Đã thêm thành công {len(documents)} đoạn văn bản vào cơ sở dữ liệu!")
                        else:
                            st.error("❌ Có lỗi xảy ra khi thêm tài liệu!")
                    
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        
        st.markdown("---")
        
        # Database info
        st.subheader("ℹ️ Thông Tin Cơ Sở Dữ Liệu")
        for config in CONFIG.RETRIEVER_TOOL_CONFIGS:
            with st.expander(f"📚 {config.human_description}"):
                st.write(f"**Tên index:** {config.pinecone_index_name}")
                st.write(f"**Mô tả:** {config.tool_description}")
        
        st.markdown("---")
        
        # Usage instructions moved to sidebar
        st.subheader("🛠️ Hướng Dẫn Sử Dụng")
        
        with st.expander("📖 Cách sử dụng"):
            st.markdown("""
            **Trò chuyện:**
            - Nhập câu hỏi vào ô chat
            - Bot sẽ tìm kiếm thông tin và trả lời bạn
            
            **Thêm tài liệu:**
            - Chọn cơ sở dữ liệu phù hợp
            - Tải file .txt lên
            - Nhấn "Thêm Tài Liệu"
            
            **Lưu ý:**
            - Chỉ hỗ trợ file .txt
            - Tài liệu sẽ được tự động chia nhỏ
            """)
        
        with st.expander("❓ Các câu hỏi mẫu"):
            st.markdown("""
            - Thông tin tuyển sinh HANU 2025?
            - Học phí của HANU là bao nhiêu?
            - Trường HANU có những ngành nào?
            - Lịch sử hình thành của HANU?
            - Có hỗ trợ học bổng nào?
            """)
        
        # Clear chat button
        if st.button("🗑️ Xóa Lịch Sử Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()

    # Main chat interface - now full width
    st.header("💬 Trò Chuyện")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        welcome_msg = """
        Xin chào! Tôi là chatbot tư vấn tuyển sinh của Đại học Hà Nội (HANU). 
        
        Tôi có thể giúp bạn tìm hiểu về:
        - 🏫 Thông tin giới thiệu về trường
        - 📋 Thông tin tuyển sinh năm 2025  
        - 📚 Lịch sử của trường
        - 💰 Học phí và hỗ trợ học bổng
        
        Hãy đặt câu hỏi để tôi có thể hỗ trợ bạn!
        """
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    # Create a container for chat messages with scroll
    chat_container = st.container()
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input - placed outside columns to be full width and sticky
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get bot response
        with st.spinner("Đang suy nghĩ..."):
            try:
                response = get_answer(prompt)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Rerun to show new messages
        st.rerun()

if __name__ == "__main__":
    main() 