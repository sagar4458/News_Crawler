import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from .prompt_templates import unified_prompt   # <-- import the new unified prompt
from .llm_handler import GroqLLM
import warnings
warnings.filterwarnings("ignore")

class RAGRetriever:
    def __init__(self, index_path="data/index"):
        self.index_path = index_path
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        if os.path.exists(index_path) and os.path.exists(os.path.join(index_path, "index.faiss")):
            self.vectorstore = FAISS.load_local(index_path, self.embeddings)
        else:
            self.vectorstore = None
            print("Index not found. Please run /build_index first.")

        # Initialize the real LLM (with fallback models)
        self.llm = GroqLLM()

    def answer(self, question, k=4):
        if self.vectorstore is None:
            return "Index not built. Please trigger /build_index endpoint.", []

        # 1. Retrieve relevant documents
        docs = self.vectorstore.similarity_search(question, k=k)
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = list(set([doc.metadata.get('source', 'unknown') for doc in docs]))

        # 2. Always use the unified prompt – the LLM decides whether to use context or general knowledge
        formatted_prompt = unified_prompt.format(context=context, question=question)
        answer = self.llm(formatted_prompt)

        return answer, sources