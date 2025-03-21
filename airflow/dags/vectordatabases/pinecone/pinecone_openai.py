import openai, os, re
from pinecone import Pinecone, ServerlessSpec
from services.s3 import S3FileManager
from vectordatabases.chunking.chunk_strategy import markdown_chunking, semantic_chunking, sliding_window_chunking
from airflow.models import Variable

# Initialize Pinecone
PINECONE_API_KEY = Variable.get("PINECONE_API_KEY")
PINECONE_INDEX = Variable.get("PINECONE_INDEX")
AWS_BUCKET_NAME = Variable.get("AWS_BUCKET_NAME")
OPENAI_API_KEY = Variable.get("OPENAI_API_KEY")

def connect_to_pinecone_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if not pc.has_index(PINECONE_INDEX):
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
            tags={
                "environment": "development"
            }
        )
    index = pc.Index(PINECONE_INDEX)
    return index
    
def read_markdown_file(file, s3_obj):
    content = s3_obj.load_s3_file_content(file)
    return content

def get_embedding(text):
    """Generates an embedding for the given text using OpenAI."""
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def create_pinecone_vector_store(file, chunks, chunk_strategy):
    index = connect_to_pinecone_index()
    vectors = []
    file = file.split('/')
    parser = file[1]
    identifier = file[2]
    year = identifier[2:6]
    quarter = identifier[6:]
    records = 0
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        vectors.append((
            f"{identifier}_{parser}_chunk_{i}",  # Unique ID
            embedding,  # Embedding vector
            {"year": year, "quarter": quarter, "text": chunk}  # Metadata
        ))
        if len(vectors) >= 20:
            records += len(vectors)
            upsert_vectors(index, vectors, parser, chunk_strategy)
            # index.upsert(vectors=vectors, namespace=f"{parser}_{chunk_strategy}")
            print(f"Inserted {len(vectors)} chunks into Pinecone.")
            vectors.clear()
    # Store in Pinecone under the correct namespace
    if len(vectors)>0:
        upsert_vectors(index, vectors, parser, chunk_strategy)
        # index.upsert(vectors=vectors, namespace=f"{parser}_{chunk_strategy}")
        print(f"Inserted {len(vectors)} chunks into Pinecone.")
        records += len(vectors)
    print(f"Inserted {records} chunks into Pinecone.")

def upsert_vectors(index, vectors, parser, chunk_strategy):
    index.upsert(vectors=vectors, namespace=f"{parser}_{chunk_strategy}")

def query_pinecone(parser, chunking_strategy, query, top_k=20, year = "2025", quarter = ["Q4"]):
    # Search the dense index and rerank the results
    index = connect_to_pinecone_index()
    dense_vector = get_embedding(query)
    results = index.query(
        namespace=f"{parser}_{chunking_strategy}",
        vector=dense_vector,  # Dense vector embedding
        filter={
            "year": {"$eq": year},
            "quarter": {"$in": quarter},
        },  # Sparse keyword match
        top_k=top_k,
        include_metadata=True,  # Include chunk text
    )
    responses = []
    for match in results["matches"]:
        print(f"ID: {match['id']}, Score: {match['score']}")
        # print(f"Chunk: {match['metadata']['text']}\n")
        responses.append(match['metadata']['text'])
        print("=================================================================================")
    return responses

def create_pinecone():
    base_path = "nvdia/"
    
    s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)
    files = list({file for file in s3_obj.list_files() if file.endswith('.md')})
    # files = files[:1]
    print(files)
    # files = []
    for i, file in enumerate(files):
        print(f"Processing File {i+1}: {file}")
        content = read_markdown_file(file, s3_obj)
        
        print("Using markdown chunking strategy...")
        chunks = markdown_chunking(content, heading_level=2)
        print(f"Chunk size: {len(chunks)}")
        create_pinecone_vector_store(file, chunks, "markdown")
        
        print("Using semantic chunking strategy...")
        chunks = semantic_chunking(content, max_sentences=10)
        print(f"Chunk size: {len(chunks)}")
        create_pinecone_vector_store(file, chunks, "semantic")
        
        print("Using sliding window chunking strategy...")
        chunks = sliding_window_chunking(content, chunk_size=1000, overlap=150)
        print(f"Chunk size: {len(chunks)}")
        create_pinecone_vector_store(file, chunks, "slidingwindow")
    # hybrid_search(parser="mistral", chunking_strategy="semantic", query="risk factors", top_k=5, year="2025", quarter=["Q1","Q4"])
    