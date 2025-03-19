import os
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from chromadb.config import Settings

import tempfile
import shutil
from dotenv import load_dotenv

from chunk_strategy import markdown_chunking, semantic_chunking  # make changes
from s3 import S3FileManager  # make changes

load_dotenv()
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def read_markdown_file(file, s3_obj):
    content = s3_obj.load_s3_file_content(file)
    return content

def get_embeddings(texts):
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
    return openai_ef(texts)



def create_chromadb_vector_store(chroma_client, file, chunks, chunk_strategy):
    # Create collections
    collection_doc_sem = chroma_client.get_or_create_collection(name="docling_semantic")
    collection_mist_sem = chroma_client.get_or_create_collection(name="mistral_semantic")
    collection_doc_mark = chroma_client.get_or_create_collection(name="docling_markdown")
    collection_mist_mark = chroma_client.get_or_create_collection(name="mistral_markdown")

    file = file.split('/')
    parser = file[1]
    identifier = file[2]
    year = identifier[2:6]
    quarter = identifier[6:]

    base_metadata = {
            "year": year,
            "quarter": quarter
        }
    metadata = [base_metadata for _ in range(len(chunks))]
    
    embeddings = get_embeddings(chunks)
    ids = [f"{parser}_{chunk_strategy}_{identifier}_{i}" for i in range(len(chunks))]
    if parser == 'docling' and chunk_strategy == 'semantic':
        print(f"adding to collection - {parser} - {chunk_strategy}")
        collection_doc_sem.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadata,
                documents=chunks
            )
        print(f"Items in docling_semantic: {collection_doc_sem.count()}")
    elif parser == 'docling' and chunk_strategy == 'markdown':
        print(f"adding to collection - {parser} - {chunk_strategy}")
        collection_doc_mark.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadata,
                documents=chunks
            )
        print(f"Items in docling_markdown: {collection_doc_mark.count()}")
    elif parser == 'mistral' and chunk_strategy == 'semantic':
        print(f"adding to collection - {parser} - {chunk_strategy}")
        collection_mist_sem.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadata,
                documents=chunks
            )
        print(f"Items in mistral semantic: {collection_mist_sem.count()}")

    elif parser == 'mistral' and chunk_strategy == 'markdown':
        print(f"adding to collection - {parser} - {chunk_strategy}")
        collection_mist_mark.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadata,
                documents=chunks
            )
        print(f"Items in mistral markdown: {collection_mist_mark.count()}")

def upload_directory_to_s3(local_dir, s3_obj, s3_prefix):
    """Upload a directory and its contents to S3"""
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            # Create the S3 key by replacing the local directory path with the S3 prefix
            relative_path = os.path.relpath(local_path, local_dir)
            s3_key = os.path.join(s3_prefix, relative_path).replace("\\", "/")
            
            with open(local_path, "rb") as f:
                s3_obj.upload_file(AWS_BUCKET_NAME, s3_key, f.read())

# def main():
    # with tempfile.TemporaryDirectory() as temp_dir:
    #     chroma_client = chromadb.PersistentClient(path=temp_dir)
    #     base_path = "nvdia/"
    #     s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)

    #     files = list({file for file in s3_obj.list_files() if file.endswith('.md')})
    #     files = files[:2]  #make change here
    #     for file in files:
    #         content = read_markdown_file(file, s3_obj)

    #         # For markdown chunking strategy
    #         chunks_mark = markdown_chunking(content, heading_level=2)
    #         print(f"Chunk size markdown: {len(chunks_mark)}")
    #         create_chromadb_vector_store(chroma_client, file, chunks_mark, "markdown")

    #         # For semantic chunking strategy
    #         chunks_sem = semantic_chunking(content, max_sentences=10)
    #         print(f"Chunk size semantic: {len(chunks_sem)}")
    #         create_chromadb_vector_store(chroma_client, file, chunks_sem, "semantic")

    #     print(files)

    #     # Upload the entire ChromaDB directory to S3
    #     upload_directory_to_s3(temp_dir, s3_obj, "chroma_db")
        
    #     print("ChromaDB has been uploaded to S3.")
    #     # Explicitly close the ChromaDB client
def main():
    temp_dir = tempfile.mkdtemp()
    chroma_client = chromadb.PersistentClient(path=temp_dir)
    base_path = "nvdia/"
    s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)

    files = list({file for file in s3_obj.list_files() if file.endswith('.md')})
    # files = files[:2]  # process only first two files
    for file in files:
        content = read_markdown_file(file, s3_obj)

        # For markdown chunking strategy
        chunks_mark = markdown_chunking(content, heading_level=2)
        print(f"Chunk size markdown: {len(chunks_mark)}")
        create_chromadb_vector_store(chroma_client, file, chunks_mark, "markdown")

        # For semantic chunking strategy
        chunks_sem = semantic_chunking(content, max_sentences=10)
        print(f"Chunk size semantic: {len(chunks_sem)}")
        create_chromadb_vector_store(chroma_client, file, chunks_sem, "semantic")

    print(files)

    # Upload the entire ChromaDB directory to S3
    upload_directory_to_s3(temp_dir, s3_obj, "chroma_db")
    print("ChromaDB has been uploaded to S3.")

if __name__ == "__main__":
    main()