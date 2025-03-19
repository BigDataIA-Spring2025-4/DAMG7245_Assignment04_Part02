import os
import re
import boto3
import spacy
import chromadb
from typing import List, Dict
from openai import OpenAI

from s3 import S3FileManager
# Configuration
AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
S3_PREFIX = "documents/"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"

# Initialize clients
base_path = base_path = f"pdf/docling/"
s3 = S3FileManager(AWS_BUCKET, base_path)

nlp = spacy.load("en_core_web_sm")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
chroma_client = chromadb.Client()

# --------------------------
# 1. S3 Document Processing
# --------------------------
def get_s3_documents() -> List[Dict]:
    """Retrieve MD files from S3 with year/quarter metadata"""
    documents = []
    
    response = s3.list_files()
    # Process objects in the current response
    for obj in response:
        if obj['Key'].endswith('.md'):
            # Extract year/quarter from path format: documents/YYYY/QN/filename.md
            path_parts = obj['Key'].split('/')
            year = path_parts[1]
            quarter = path_parts[2]
            
            response = s3.get_object(Bucket=AWS_BUCKET, Key=obj['Key'])
            content = response['Body'].read().decode('utf-8')
            
            documents.append({
                "key": obj['Key'],
                "content": content,
                "year": year,
                "quarter": quarter
            })
    return documents

# --------------------------
# 2. Chunking Strategies
# --------------------------
def semantic_chunking(text: str, max_sentences: int = 5) -> List[Dict]:
    """Chunk text using spaCy sentence parsing with semantic boundaries"""
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    
    chunks = []
    current_chunk = []
    for i, sent in enumerate(sentences):
        current_chunk.append(sent)
        if (i + 1) % max_sentences == 0:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def markdown_header_chunking(text: str) -> List[Dict]:
    """Chunk Markdown by headers while preserving hierarchy"""
    chunks = []
    current_header = None
    current_content = []
    
    # Split lines and process
    for line in text.split('\n'):
        header_match = re.match(r'^(#+)\s+(.+)$', line)
        if header_match:
            if current_header:
                chunks.append({
                    "header": current_header,
                    "content": "\n".join(current_content)
                })
            current_header = {
                "level": len(header_match.group(1)),
                "text": header_match.group(2)
            }
            current_content = []
        else:
            current_content.append(line)
    
    if current_header:
        chunks.append({
            "header": current_header,
            "content": "\n".join(current_content)
        })
    
    return chunks

# --------------------------
# 3. Embedding Generation
# --------------------------
def generate_embeddings(texts):
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
    return openai_ef(texts)

# --------------------------
# 4. ChromaDB Integration
# --------------------------
def store_in_chroma(chunks: List[Dict], metadata: Dict):
    """Store chunks in ChromaDB with metadata"""
    collection = chroma_client.get_or_create_collection("document_chunks")
    
    texts = [chunk['text'] for chunk in chunks]
    embeddings = generate_embeddings(texts)
    metadatas = [chunk['metadata'] for chunk in chunks]
    ids = [f"{metadata['source']}_{i}" for i in range(len(chunks))]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=texts
    )

# --------------------------
# Main Processing Pipeline
# --------------------------
def process_documents():
    documents = get_s3_documents()
    
    for doc in documents:
        # Base metadata
        base_metadata = {
            "source": doc['key'],
            "year": doc['year'],
            "quarter": doc['quarter'],
            "file_size": len(doc['content'])
        }
        
        # Process with both chunking strategies
        all_chunks = []
        
        # Strategy 1: Semantic chunking
        semantic_chunks = semantic_chunking(doc['content'])
        for i, chunk in enumerate(semantic_chunks):
            all_chunks.append({
                "text": chunk,
                "metadata": {
                    **base_metadata,
                    "chunk_strategy": "semantic",
                    "chunk_num": i+1
                }
            })
        
        # Strategy 2: Markdown header chunking
        header_chunks = markdown_header_chunking(doc['content'])
        for i, chunk in enumerate(header_chunks):
            all_chunks.append({
                "text": chunk['content'],
                "metadata": {
                    **base_metadata,
                    "chunk_strategy": "markdown_header",
                    "header_level": chunk['header']['level'],
                    "header_text": chunk['header']['text'],
                    "chunk_num": i+1
                }
            })
        
        # Store in ChromaDB
        store_in_chroma(all_chunks, base_metadata)


if __name__ == "__main__":
    process_documents()