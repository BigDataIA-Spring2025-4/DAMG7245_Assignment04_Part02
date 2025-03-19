import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
from services.s3 import S3FileManager
# from features.pinecone.chunk_strategy import markdown_chunking, semantic_chunking
from features.pinecone.pinecone_openai import connect_to_pinecone_index, get_embedding, hybrid_search
from openai import OpenAI

class QuestionRequest(BaseModel):
    year: str
    quarter: list
    parser: str
    chunk_strategy: str
    vector_store: str
    query: str

app = FastAPI()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()

@app.get("/")
def read_root():
    return {"message": "NVDIA Financial Reports Analysis: FastAPI Backend with OpenAI Integration available for user queries..."}

@app.post("/query_documents")
def query_documents(request: QuestionRequest):
    try:
        year = request.year
        quarter = request.quarter
        parser = request.parser
        chunk_strategy = request.chunk_strategy
        query = request.query
        vector_store = request.vector_store
        
        if vector_store == "pinecone":
            chunks = generate_response_from_pinecone(parser = parser, chunk_strategy = chunk_strategy, query = query, top_k=5, year = year, quarter = quarter)
            # print(chunks)
            if len(chunks) == 0:
                raise HTTPException(status_code=500, detail="No relevant data found in the document")
            else:
                message = generate_pinecone_openai_message(chunks, year, quarter, query)
                answer = generate_model_response(message)
        elif vector_store == "pinecone":
            pass
        elif vector_store == "manual":
            pass
        return {
            # "answer": year + quarter[0] + parser + chunk_strategy + vector_store + query,
            "answer": answer
        }
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")

def generate_response_from_pinecone(parser, chunk_strategy, query, top_k, year, quarter ):
    response = hybrid_search(parser = parser, chunking_strategy = chunk_strategy, query = query, top_k=top_k, year = year, quarter = quarter)
    return response

def generate_pinecone_openai_message(chunks, year, quarter, query):
    prompt = f"""
    Below are relevant excerpts from a NVDIA quarterly financial report for year {year} and quarter {quarter} that may help answer the query.

    --- User Query ---
    {query}

    --- Relevant Document Chunks ---
    {chr(10).join([f'Chunk {i+1}: {chunk}' for i, chunk in enumerate(chunks)])}

    Based on the provided document chunks, generate a comprehensive response to the query. If needed, synthesize the information and ensure clarity.
    """
    print(prompt)
    return prompt

def generate_model_response(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. You are given excerpts from NVDIA's quarterly financial report. Use them to answer the user query."},
                {"role": "user", "content": message}
            ],
            max_completion_tokens=2048
        )
        # print(response.choices[0].message)
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response from OpenAI Model: {str(e)}")
    
    