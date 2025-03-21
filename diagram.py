from diagrams import Diagram, Cluster
from diagrams.custom import Custom
from diagrams.aws.storage import S3
from diagrams.gcp.compute import Run
from diagrams.onprem.client import User
from diagrams.programming.framework import FastAPI
from diagrams.digitalocean.compute import Docker
from diagrams.onprem.workflow import Airflow

# Create the diagram
with Diagram("PDF RAG Application Architecture", show=False, filename="diagram", direction="LR"):
    # Cloud Services
    cloud_run = Run("Google Cloud Run")
    
    # Backend Cluster
    with Cluster("Backend (FastAPI)"):
        # Docker Image for Backend Services
        docker_image = Docker("Docker Image") 
        backend = FastAPI("FastAPI Service")

    # User interaction
    user = User("User")
    
    # Input Mechanism Cluster
    with Cluster("User Input"):
        pdf_input = Custom("PDF File", "./src/pdf.png")  # Replace with an appropriate local or online icon for PDF upload
    
    # Streamlit Frontend Cluster (Generic Node)
    with Cluster("Frontend (Streamlit)"):
        frontend = Custom("Streamlit UI", "./src/streamlit.png")  # Use a custom icon for Streamlit
    
    # Input Mechanism Cluster
    with Cluster("User Actions"):
        airflow = Airflow("Airflow") 

    # Trigger Airflow DAGS 
    with Cluster("Data Pipelines", direction='LR'):
        
        web = Custom("NVIDIA Financial Reports", "./src/website.png")
        s3_storage = S3("Amazon S3")
        docling = Custom("Docling", "./src/docling.png")
        mistral = Custom("Mistral OCR", "./src/mistral.png")
        chunkstrategy = Custom("Document Chunking", "./src/chunks.png")
        openai_embedding = Custom("Open AI Embeddings", "./src/openai.png")
        pinecone = Custom("Pinecone", "./src/pinecone.png")
        chromadb = Custom("Chroma DB", "./src/chroma.png")
        manual = Custom("Manual Embeddings", "./src/pickle.png")

    # Connections
    user >> frontend >> pdf_input
    airflow >> web >> s3_storage >> [docling, mistral] >> chunkstrategy >> openai_embedding >> [pinecone, chromadb, manual]
    cloud_run >> docker_image >> backend >> [pinecone, chromadb, manual]
    frontend >> backend
    pdf_input >> [docling, mistral] >> chunkstrategy >> openai_embedding >> [pinecone, chromadb, manual]
