import os
import sys
import json
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from rag.retriever import RAGRetriever
from dedup.exact_dedup import exact_deduplicate
from dedup.minhash_lsh import near_deduplicate
import pandas as pd
import hashlib

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

rag_instance = None

def get_rag():
    global rag_instance
    if rag_instance is None:
        rag_instance = RAGRetriever()
    return rag_instance

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

import sys   # Add this at the top if missing

@app.route('/crawl', methods=['POST'])
def start_crawl():
    """Trigger the crawler using the standalone Playwright script."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "run_playwright_spider.py")
        # Use the same Python executable that is running Flask (from venv)
        python_exe = sys.executable
        result = subprocess.run(
            [python_exe, script_path],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
        return jsonify({"message": "Crawling completed", "output": result.stdout})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Crawling timed out after 120 seconds"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deduplicate', methods=['POST'])
def deduplicate():
    """Run exact + near duplicate removal and save Parquet."""
    input_file = os.path.join(BASE_DIR, "data/raw/articles.jsonl")
    output_dir = os.path.join(BASE_DIR, "data/deduped")
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    df = pd.read_json(input_file, lines=True)
    original_count = len(df)

    # Exact dedup based on title+body hash
    df['hash'] = df.apply(lambda row: hashlib.sha256(
        (row.get('title', '') + row.get('body', '')).encode()
    ).hexdigest(), axis=1)
    df_exact = df.drop_duplicates(subset=['hash'])
    after_exact = len(df_exact)

    # Near duplicate using MinHash + LSH (requires list of bodies)
    bodies = df_exact['body'].fillna('').tolist()
    keep_mask = near_deduplicate(bodies)  # returns boolean mask
    df_final = df_exact[keep_mask]
    after_near = len(df_final)

    # Save as Parquet
    output_path = os.path.join(output_dir, "final_news.parquet")
    df_final.to_parquet(output_path, index=False)

    return jsonify({
        "original": original_count,
        "after_exact": after_exact,
        "after_near": after_near,
        "saved_to": output_path
    })

@app.route('/build_index', methods=['POST'])
def build_index():
    """Build FAISS index from deduped Parquet."""
    from rag.indexer import build_faiss_index
    input_parquet = os.path.join(BASE_DIR, "data/deduped/final_news.parquet")
    index_path = os.path.join(BASE_DIR, "data/index")
    os.makedirs(index_path, exist_ok=True)
    build_faiss_index(input_parquet, index_path)
    return jsonify({"message": "Index built", "index_path": index_path})

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({"error": "No question provided"}), 400
    rag = get_rag()
    answer, sources = rag.answer(question)
    return jsonify({
        "question": question,
        "answer": answer,
        "sources": sources
    })
    
@app.route('/export_dataset', methods=['GET'])
def export_dataset():
    """Download the deduped dataset as a Parquet file."""
    file_path = os.path.join(BASE_DIR, "data/deduped/final_news.parquet")
    if not os.path.exists(file_path):
        return jsonify({"error": "Dataset not found. Please run Deduplicate first."}), 404
    return send_file(file_path, as_attachment=True, download_name="news_dataset.parquet")

@app.route('/stats', methods=['GET'])
def get_stats():
    """Return dataset statistics: number of raw articles, deduped articles, index chunks, etc."""
    import pandas as pd
    raw_file = os.path.join(BASE_DIR, "data/raw/articles.jsonl")
    deduped_file = os.path.join(BASE_DIR, "data/deduped/final_news.parquet")

    stats = {"raw_count": 0, "deduped_count": 0, "index_chunks": 0}
    
    if os.path.exists(raw_file):
        df_raw = pd.read_json(raw_file, lines=True)
        stats["raw_count"] = len(df_raw)
    if os.path.exists(deduped_file):
        df_deduped = pd.read_parquet(deduped_file)
        stats["deduped_count"] = len(df_deduped)
    
    # Read index chunk count (saved in a file during build_index)
    chunk_info = os.path.join(BASE_DIR, "data/index/chunk_count.txt")
    if os.path.exists(chunk_info):
        with open(chunk_info, 'r') as f:
            stats["index_chunks"] = int(f.read().strip())
    return jsonify(stats)

@app.route('/surprise', methods=['GET'])
def surprise():
    """Pick a random chunk from the index and generate a question about it."""
    import random
    from rag.llm_handler import GroqLLM   # <-- absolute import

    rag = get_rag()
    if not rag.vectorstore:
        return jsonify({"error": "Index not built"}), 400

    chunks_file = os.path.join(BASE_DIR, "data/index/chunks.txt")
    if not os.path.exists(chunks_file):
        return jsonify({"error": "No chunks available. Please rebuild index."}), 400

    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = [line.strip() for line in f if line.strip()]

    if not chunks:
        return jsonify({"error": "No chunks found"}), 400

    random_chunk = random.choice(chunks)
    llm = GroqLLM()
    prompt = f"""Based on the following news excerpt, generate a single, specific, natural question that a user might ask. Do not answer it.

Excerpt:
{random_chunk[:800]}

Generated question:"""
    generated_question = llm(prompt).strip()
    return jsonify({"question": generated_question})

if __name__ == '__main__':
    app.run(debug=True, port=5000)