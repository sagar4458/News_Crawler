import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os

def build_faiss_index(parquet_path, index_save_path):
    """Load deduped Parquet, chunk documents, embed, and save FAISS index."""
    df = pd.read_parquet(parquet_path)
    
    # Create LangChain Documents
    docs = []
    for _, row in df.iterrows():
        content = f"Title: {row['title']}\nContent: {row['body']}"
        metadata = {"source": row.get('url', ''), "date": row.get('date', '')}
        docs.append(Document(page_content=content, metadata=metadata))
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)
    chunks_file = os.path.join(index_save_path, "chunks.txt")
    with open(chunks_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            # Replace newlines with spaces to keep each chunk on one line
            f.write(chunk.page_content.replace('\n', ' ') + '\n')

    # Save chunk count for stats
    count_file = os.path.join(index_save_path, "chunk_count.txt")
    with open(count_file, 'w') as f:
        f.write(str(len(chunks)))
    
    # Embed and index
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(index_save_path)
    print(f"Index saved to {index_save_path} with {len(chunks)} chunks")