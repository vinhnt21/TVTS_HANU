import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pinecone import Pinecone
import config.CONFIG as CONFIG
import utils.log as log 

pinecone_client = Pinecone(api_key=CONFIG.PINECONE_API_KEY)

# pinecone_client.delete_index("retrieve-thong-tin-tuyen-sinh-hanu")
# xóa hết record trong index
index = pinecone_client.Index("retrieve-thong-tin-tuyen-sinh-hanu")
index.delete(delete_all=True)

log.success("Đã xóa hết record trong index")

# # thêm lại tài liệu
# from agent.vectorstore import load_document_and_chunk

# file_path = os.path.join(os.path.dirname(__file__), "..", "data", "De an web 2025.txt")

# documents = load_document_and_chunk(file_path)

# # thêm tài liệu vào index

# index.upsert(documents)
# log.success("Đã load tài liệu")



