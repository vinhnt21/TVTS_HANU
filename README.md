# 🎓 Chatbot Tư Vấn Tuyển Sinh HANU

Ứng dụng chatbot tư vấn tuyển sinh cho Đại học Hà Nội (HANU) sử dụng RAG (Retrieval-Augmented Generation) và Streamlit.

## 🚀 Tính Năng

- **Chat Interface**: Giao diện chat thân thiện với người dùng
- **RAG System**: Tìm kiếm thông tin từ multiple databases
- **Document Management**: Upload và quản lý tài liệu .txt
- **Multiple Databases**: 4 cơ sở dữ liệu chuyên biệt:
  - Thông tin giới thiệu về HANU
  - Thông tin tuyển sinh năm 2025
  - Lịch sử trường HANU
  - Thông tin học phí và hỗ trợ học bổng

## 📋 Yêu Cầu Hệ Thống

- Python 3.8+
- OpenAI API Key
- Pinecone API Key

## 🛠️ Cài Đặt

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd TVTS_HANU
   ```

2. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình API Keys:**
   - Copy file `.streamlit/secrets.toml` 
   - Điền các API key thật của bạn:
   ```toml
   OPENAI_API_KEY = "your_actual_openai_api_key"
   PINECONE_API_KEY = "your_actual_pinecone_api_key"
   ENTER_KEY = "your_enter_key"
   ```

4. **Chạy ứng dụng:**
   ```bash
   streamlit run streamlit_app.py
   ```

## 💻 Cách Sử Dụng

### Chat với Bot
1. Mở ứng dụng trong browser (thường là http://localhost:8501)
2. Nhập câu hỏi vào ô chat
3. Bot sẽ tìm kiếm thông tin và trả lời

### Thêm Tài Liệu Mới
1. Ở sidebar, chọn cơ sở dữ liệu phù hợp
2. Upload file .txt
3. Nhấn "Thêm Tài Liệu"
4. Tài liệu sẽ được tự động xử lý và thêm vào database

### Các Loại Câu Hỏi Mẫu
- "Thông tin tuyển sinh HANU 2025 như thế nào?"
- "Học phí của HANU là bao nhiêu?"
- "Trường HANU có những ngành nào?"
- "Lịch sử hình thành và phát triển của HANU?"
- "Có những hình thức hỗ trợ học bổng nào?"

## 🏗️ Kiến Trúc Hệ Thống

```
├── agent/
│   ├── graph.py          # RAG workflow logic
│   ├── prompts.py        # LLM prompts
│   └── vectorstore.py    # Pinecone vector store setup
├── config/
│   ├── CONFIG.py         # Configuration settings
│   └── pinecone_indexes.json  # Database configurations
├── utils/
│   └── log.py           # Logging utilities
├── streamlit_app.py     # Main Streamlit application
└── requirements.txt     # Python dependencies
```

## ⚙️ Cấu Hình

Hệ thống sử dụng 4 Pinecone indexes chuyên biệt:

1. **retrieve-thong-tin-chung**: Thông tin giới thiệu về HANU
2. **retrieve-thong-tin-tuyen-sinh**: Thông tin tuyển sinh năm 2025  
3. **retrieve-thong-tin-lich-su**: Lịch sử của HANU
4. **retrieve-thong-tin-tai-chinh**: Học phí và hỗ trợ học bổng

## 🔧 Tùy Chỉnh

Để thêm database mới:
1. Cập nhật `config/pinecone_indexes.json`
2. Thêm cấu hình mới với format:
   ```json
   {
     "name": "your-index-name",
     "description": "Tool description for LLM",
     "description_for_human": "Human readable description"
   }
   ```

## 🐛 Xử Lý Lỗi

- Kiểm tra API keys trong `.streamlit/secrets.toml`
- Đảm bảo có kết nối internet
- Kiểm tra format file upload (chỉ .txt)
- Xem logs trong terminal để debug

## 📞 Hỗ Trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. API keys có đúng không
2. Dependencies đã được cài đặt đầy đủ
3. Kết nối mạng ổn định
4. Format file upload đúng (.txt only)

---

Made with ❤️ for HANU Admissions 