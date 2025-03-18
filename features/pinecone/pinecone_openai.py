import openai, os, markdown, re
from pinecone import Pinecone, ServerlessSpec
from services.s3 import S3FileManager
from dotenv import load_dotenv
load_dotenv()

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def chunking(markdown_text, heading_level=2):
    pattern = rf'(?=^{"#" * heading_level} )'  # Regex to match specified heading level
    chunks = re.split(pattern, markdown_text, flags=re.MULTILINE)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def connect_to_pinecone_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    # print(pc.list_indexes())
    # if PINECONE_INDEX not in pc.list_indexes():
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
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def main():
    base_path = "nvdia/"
    
    s3_obj = S3FileManager(AWS_BUCKET_NAME, base_path)
    files = list({file for file in s3_obj.list_files() if file.endswith('.md')})
    files = files[:1]
    index = connect_to_pinecone_index()
    for file in files:
        content = read_markdown_file(file, s3_obj)
        chunks = chunking(content, heading_level=2)
        print(f"Chunk size: {len(chunks)}")
        
        vectors = []
        file = file.split('/')
        parser = file[1]
        identifier = file[2]
        year = identifier[2:6]
        quarter = identifier[6:7]
        
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            vectors.append((
                f"{identifier}_{parser}_chunk_{i}",  # Unique ID
                embedding,  # Embedding vector
                {"year": year, "quarter": quarter, "text": chunk}  # Metadata
            ))
        # Store in Pinecone under the correct namespace
        index.upsert(vectors=vectors, namespace=f"{parser}_chunk_headings")
        print(f"Inserted {len(vectors)} chunks into Pinecone.")
    print(files)
    
if __name__ == "__main__":
    # Load the OpenAI API key from the environment
    main()