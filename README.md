# DAMG7245_Assignment04_Part02

## Project Overview

This project focuses on designing an AI-powered information retrieval system that automates the extraction, processing, and analysis of financial reports. Using **Apache Airflow**, the system orchestrates the retrieval of NVIDIA’s quarterly financial statements, processes them with advanced text extraction methods, and stores the data efficiently for querying. The project incorporates **multiple chunking techniques** to optimize data segmentation and **embeddings** to enhance retrieval performance. A **Streamlit-based UI** enables users to explore the dataset and upload their own documents for analysis, ensuring an interactive and customizable experience.

## Key Features

### **1. Automated Data Collection & Storage**

- **Scraping NVIDIA Reports**: Develops an automated workflow to extract the last five years of financial reports from NVIDIA’s official source.
- **Cloud Storage Integration**: Saves raw documents securely in **AWS S3** for scalable data management.

### **2. Intelligent Document Processing**

- **Advanced PDF Extraction**: Utilizes cutting-edge tools for parsing:
    - **Docling**: Extracts structured data efficiently.
    - **Mistral OCR**: Converts scanned PDFs into machine-readable text with high accuracy.
- **Data Segmentation Strategies**: Implements diverse methods to break down large text blocks:
    - **Logical Sectioning**: Divides text based on structured headers.
    - **Contextual Grouping**: Segments related content to maintain semantic meaning.
    - **Sliding Window Approach**: Ensures overlapping sections for better context retention.

### **3. Embeddings & Vector Storage for Efficient Retrieval**

- **Transforming Text into Embeddings**: Converts processed text into **OpenAI vector representations** for improved search accuracy.
- **Flexible Storage Options**:
    - **Pinecone**: Cloud-based vector database for rapid information retrieval.
    - **ChromaDB**: Local vector store optimized for AI-driven searches.
    - **Pickle Storage in S3**: Alternative manual storage for embedding representations.

### **4. Enhanced Search & Retrieval System**

- **Hybrid Query Processing**: Users can refine searches based on specific time periods to get precise insights.
- **Multiple Search Approaches**:
    - **Manual Vector Similarity Matching**: Computes similarity without external databases.
    - **Optimized Retrieval via Pinecone & ChromaDB**: Uses precomputed embeddings for real-time document querying.

### **5. Interactive Streamlit-Based User Interface**

- **Custom Document Uploads**: Users can analyze their own files using the same pipeline.
- **Flexible Processing Options**: Allows selection of:
    - Preferred **PDF extraction method** (Docling, Mistral OCR).
    - **Chunking technique** for optimal segmentation.
    - **Embedding storage method** (manual, Pinecone, ChromaDB).
    - **Specific quarter selection** for refined query responses.
- **Intelligent Response Generation**: Processes user queries using an integrated **language model** for relevant insights.

### **6. Scalable Deployment & Cloud Integration**

- **Containerized Infrastructure**:
    - **Airflow Workflow Container**: Automates ingestion, processing, and embedding generation.
    - **Streamlit & FastAPI Service**: Hosts the user interface and API for seamless interaction.
- **Cloud Hosting & Accessibility**: The application and backend services are deployed to ensure **scalability and reliability**.

## Resources

Application: 

Backend FastAPI: 

Airflow Endpoint: 

Google Codelab: 

Google Docs: 

Video Walkthrough:

## Technologies Used

- **Streamlit**: Frontend Framework
- **FastAPI**: API Framework
- **Apache Airflow**: Data Pipeline Orchestration
- **Selenium**: Web Scraping
- **Docling**: PDF Document Data Extraction Tool
- **Mistral OCR**: PDF Document Data Extraction Tool
- **AWS S3**: External Cloud Storage
- **Pinecone**: Vector Database
- **ChromaDB**: Vector Database
- **OpenAI**: Retrieval-Augmented Generation
- **Google Cloud Run**: Backend Deployment
- **Google Compute Engine**: Airflow Deployment

## Application Workflow Diagram

![Image]()

### Workflow 

1. **User Interaction via Streamlit UI**
    - Users select a task from the sidebar:
        - **Trigger Airflow**: Initiates an Airflow DAG for scheduled tasks.
        - **Query Financial Reports**: Extracts insights from NVIDIA’s financial reports based on user queries.
        - **Query Document**: Parses and queries uploaded PDF documents.

2. **PDF Upload & Processing (If Querying a Document)**
    - User uploads a PDF file.
    - The file is read, converted to Base64, and sent to an API for processing.
    - The API extracts text and returns Markdown content.

3. **Query Execution**
    - User submits a query for either a financial report or an uploaded document.
    - Selected parsing method, chunking strategy, and vector store are applied.
    - The query is sent to an API endpoint for processing.

4. **Response Handling**
    - API returns the extracted response.
    - The response is displayed in the chat interface.
    - Conversation history is maintained using `st.session_state.messages`.

