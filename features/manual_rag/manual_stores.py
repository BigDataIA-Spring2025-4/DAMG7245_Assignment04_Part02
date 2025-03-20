import os
import numpy as np

# import boto3
# import json

import pickle
from sklearn.metrics.pairwise import cosine_similarity

import openai
# from pydantic import BaseModel
from dotenv import load_dotenv
# For using with OpenAI embeddings
from openai import OpenAI

from s3 import S3FileManager
from chunk_strategy import markdown_chunking, semantic_chunking


load_dotenv()
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMBEDDING_DIMENSION = 1536  # OpenAI ada-002 embedding dimension
EMBEDDINGS_KEY = "embeddings.pkl"
DOCUMENTS_KEY = "manual_store.json"
DOCUMENTS_KEY_PKL = "manual_store.pkl"


openai_client = OpenAI(api_key=OPENAI_API_KEY)
base_path = "nvdia/"
s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)


def save_to_s3_pickle(vectors, key=DOCUMENTS_KEY):
    save_file_path = f"{s3_obj.base_path}/{DOCUMENTS_KEY_PKL}"
    pickle_data = pickle.dumps(vectors)
    s3_obj.upload_file(AWS_BUCKET_NAME, save_file_path, pickle_data)

def load_from_s3_pickle(key=DOCUMENTS_KEY_PKL):
    save_file_path = f"{s3_obj.base_path}/{DOCUMENTS_KEY_PKL}"
    pickle_data = s3_obj.load_s3_pdf(save_file_path)
    return pickle.loads(pickle_data)


def read_markdown_file(file, s3_obj):
    content = s3_obj.load_s3_file_content(file)
    return content

def get_embedding(chunks):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
    )
    return response.data

def create_manual_vector_store(file, chunks, chunk_strategy):
    vectors = []
    file = file.split('/')
    parser = file[1]
    identifier = file[2]
    year = identifier[2:6]
    quarter = identifier[6:]

    embeddings_data = get_embedding(chunks)
    for i, embed in enumerate(embeddings_data):
        vectors.append({
            "id": f"{identifier}_{parser}_chunk_{i}",
            "embedding": list(embed.embedding),
            "metadata": {
                "year": year,
                "quarter": quarter,
                "parser": parser,
                "chunk_type": chunk_strategy,
                "text": chunks[i]
            }
        })
    return vectors

def query_manual(parser, chunking_strategy, query, top_k=3, year=None, quarter=None):
    query_embedding = get_embedding(query)
    documents = load_from_s3_pickle()
    filtered_docs = [doc for doc in documents if 
                     (doc['metadata']['year'] in year) and 
                     (doc['metadata']['quarter'] in quarter) and 
                     (doc['metadata']['chunk_type'] == chunking_strategy) and 
                     (doc['metadata']['parser'] == parser)]
    
    if not filtered_docs:
        return []

    query_embedding = query_embedding[0].embedding
    doc_embeddings = [doc['embedding'] for doc in filtered_docs]

    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    top_docs = [filtered_docs[i] for i in top_indices]
    top_similarities = [float(similarities[i]) for i in top_indices]

    results = []
    for doc, similarity in zip(top_docs, top_similarities):
        results.append({
            'id': doc['id'],
            'similarity': similarity,
            'metadata': doc['metadata']
        })
    return results

def manual_main():
    # base_path = "nvdia/"
    # s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)

    files = list({file for file in s3_obj.list_files() if file.endswith('.md')})
    print(files)
    files = files[:2]
    all_vectors = []
    for i, file in enumerate(files):
        print(f"Processing File {i+1}: {file}")
        content = read_markdown_file(file, s3_obj)
        
        print("Using markdown chunking strategy...")
        chunks = markdown_chunking(content, heading_level=2)
        print(f"Chunk size: {len(chunks)}")

        vector = create_manual_vector_store(file, chunks, "markdown")
        all_vectors.extend(vector)
    save_to_s3_pickle(all_vectors)