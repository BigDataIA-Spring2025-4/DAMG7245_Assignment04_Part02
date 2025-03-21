import os
import numpy as np
import pickle

from sklearn.metrics.pairwise import cosine_similarity
import openai

from airflow.models import Variable
from services.s3 import S3FileManager
from vectordatabases.chunking.chunk_strategy import markdown_chunking, semantic_chunking, sliding_window_chunking

AWS_BUCKET_NAME = Variable.get("AWS_BUCKET_NAME")
OPENAI_API_KEY = Variable.get("OPENAI_API_KEY")

DOCUMENTS_KEY_PKL = "manual_store.pkl"

def save_to_s3_pickle(s3_obj, vectors, key=DOCUMENTS_KEY_PKL):
    save_file_path = f"{s3_obj.base_path}/{DOCUMENTS_KEY_PKL}"
    pickle_data = pickle.dumps(vectors)
    s3_obj.upload_file(AWS_BUCKET_NAME, save_file_path, pickle_data)

def load_from_s3_pickle(s3_obj, key=DOCUMENTS_KEY_PKL):
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

#### BEGIN DOC ####

def get_manual_vector_doc(file, chunks, chunk_strategy, parser):
    vectors = []
    embeddings_data = get_embedding(chunks)
    for i, embed in enumerate(embeddings_data):
        vectors.append({
            "id": f"{file}_{parser}_{chunk_strategy}_chunk_{i}",
            "embedding": list(embed.embedding),
            "metadata": {
                "parser": parser,
                "chunk_type": chunk_strategy,
                "text": chunks[i]
            }
        })
    return vectors


def create_manual_vector_store_doc(file, chunks, chunk_strategy, parser):
    file_name = file.split('/')[2]
    base_path = "/".join(file.split('/')[:-1])
    s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)

    vector = get_manual_vector_doc(file_name, chunks, chunk_strategy, parser)
    save_to_s3_pickle(s3_obj, vector)

    return s3_obj

#### END DOC ####


def generate_response_manual(s3_obj, parser, chunking_strategy, query, top_k=5, year=None, quarter=None):
    query_embedding = get_embedding(query)
    print("Generating manual reponses")
    documents = load_from_s3_pickle(s3_obj)
    if year and quarter:
        filtered_docs = [doc for doc in documents if 
                            (doc['metadata']['year'] == year) and 
                            (doc['metadata']['quarter'] in quarter) and 
                            (doc['metadata']['chunk_type'] == chunking_strategy) and 
                            (doc['metadata']['parser'] == parser)]
    else:
        filtered_docs = [doc for doc in documents if 
                            (doc['metadata']['chunk_type'] == chunking_strategy) and 
                            (doc['metadata']['parser'] == parser)]
    if not filtered_docs:
        return []

    query_embedding = query_embedding[0].embedding
    doc_embeddings = [doc['embedding'] for doc in filtered_docs]

    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    top_docs = [filtered_docs[i] for i in top_indices]

    results = []
    for doc in top_docs:
        results.append(doc['metadata']['text'])

    return results

#### BEGIN NVDIA ####

def get_manual_vector_store(file, chunks, chunk_strategy):
    vectors = []
    file = file.split('/')
    parser = file[-2]
    year = file[-4]
    quarter = file[-3]
    identifier = f"FY{year}{quarter}"

    embeddings_data = get_embedding(chunks)
    for i, embed in enumerate(embeddings_data):
        vectors.append({
            "id": f"{identifier}_{parser}_{chunk_strategy}_chunk_{i}",
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

def create_manual_vector_store():
    base_path = "nvdia/"
    s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)
    all_vectors = load_from_s3_pickle(s3_obj)
    print(all_vectors)

    files = list({file for file in s3_obj.list_files() if file.endswith('.md')})
    print(files)
    # all_vectors = []
    for i, file in enumerate(files):
        print(f"Processing File {i+1}: {file}")
        content = read_markdown_file(file, s3_obj)

        chunks = markdown_chunking(content, heading_level=2)
        print(f"Markdown Chunk size: {len(chunks)}")
        vector = get_manual_vector_store(file, chunks, "markdown")
        all_vectors.extend(vector)

        chunks = semantic_chunking(content)
        print(f"semantic Chunk size: {len(chunks)}")
        vector = get_manual_vector_store(file, chunks, "semantic")
        all_vectors.extend(vector)

        chunks = sliding_window_chunking(content)
        print(f"sliding Chunk size: {len(chunks)}")
        vector = get_manual_vector_store(file, chunks, "sliding_window")
        all_vectors.extend(vector)

    save_to_s3_pickle(s3_obj, all_vectors)

#### END NVDIA ####