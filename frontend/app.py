import json, time
import streamlit as st
import requests, os, base64
from io import StringIO
from dotenv import load_dotenv
load_dotenv()

API_URL=os.getenv("API_URL")
AIRFLOW_API_URL = "http://35.209.49.151:8080"

pdfparser = {
        "Mistral": "mistral",
        "Docling": "docling"
    }

chunking = {
        "Markdown": "markdown",
        "Semantic": "semantic",
        "Sliding Window": "sliding_window"
    }

vectorstores = {
        "Pinecone": "pinecone",
        "ChromaDB": "chromadb",
        "Manual": "manual"
    }

if 'messages' not in st.session_state:
    st.session_state.messages = []
if "file_upload" not in st.session_state:
    st.session_state.file_upload = None

def trigger_airflow_dag():
    st.write("Now triggering airflow dag...")
    year = st.selectbox("Select Year", range(2024, 2020,-1))
    trigger = st.button("Trigger Airflow DAG", use_container_width=True)
    if trigger:
        # Payload for triggering the DAG
        payload = {
            "conf": {
                "year": year
            }
        }
        # Trigger the DAG via Airflow REST API
        response = requests.post(
            f"{AIRFLOW_API_URL}/api/v1/dags/nvidia_financial_docs_scraper_and_loader/dagRuns",
            json=payload,
            auth=(f"{os.getenv('AIRFLOW_USER')}", f"{os.getenv('AIRFLOW_PASSCODE')}")
        )
        if response.status_code == 200:
            st.success("DAG triggered successfully!")
        else:
            st.error(f"Failed to trigger DAG: {response.text}")
def main():
    
    st.title("NVDIA Financial Reports Analysis")
    # Set up navigation
    st.sidebar.header("Main Menu") 
    task = st.sidebar.selectbox("Select Task", ["Trigger Airflow", "Query Financial Reports", "Query Document"])
    if task == "Trigger Airflow":
        airflow = st.sidebar.button("Trigger Airflow DAG", use_container_width=True, icon = "🚀")
        if airflow:
            trigger_airflow_dag()
    elif task == "Query Document":
        # document_parser_page()
        # Set the title of the app
        st.header("📃 Select PDF for Parsing")
                    
        if "file_upload" not in st.session_state:
            st.session_state.file_upload = None

        st.session_state.file_upload = st.sidebar.file_uploader("Choose a PDF File", type="pdf", accept_multiple_files=False)    
        select_parser = st.sidebar.selectbox('Parser:', list(pdfparser.keys()))
        parser = pdfparser[select_parser]        
        select_chunk_strategy = st.sidebar.selectbox('Select Chunking Strategy:', list(chunking.keys()))
        chunk_strategy = chunking[select_chunk_strategy]
        select_vector_store = st.sidebar.selectbox('Select Vector Store:', list(vectorstores.keys()))
        vector_store = vectorstores[select_vector_store]
        st.sidebar.text("Enter query here:")
        query = st.sidebar.chat_input(placeholder = "Write your query here...")
        if query:
        # Define what happens on each page
            if st.session_state.file_upload:
                st.success(f"File '{st.session_state.file_upload.name}' uploaded successfully!")
                file_name, markdown_content = convert_PDF_to_markdown(st.session_state.file_upload, parser)
                if not markdown_content == "":
                        st.session_state.messages.append({"role": "user", "content": query})
                        with st.chat_message("user"):
                            st.markdown(query)
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                try:
                                    response = requests.post(
                                        f"{API_URL}/query_document",
                                        json={
                                            "parser": parser,
                                            "chunk_strategy": chunk_strategy,
                                            "vector_store": vector_store,
                                            "file_name": file_name,
                                            "markdown_content": markdown_content,
                                            "query": query,
                                        }
                                    )
                                    if response.status_code == 200:
                                        answer = response.json()["answer"]
                                        st.session_state.messages.append({"role": "assistant", "content": answer})
                                        st.markdown(answer)
                                    else:
                                        error_message = f"Error: {response.text}"
                                        st.error(error_message)
                                        st.session_state.messages.append({"role": "assistant", "content": error_message})
                                except Exception as e:
                                    error_message = f"Error: {str(e)}"
                                    st.session_state.messages.append({"role": "assistant", "content": error_message})
            else:
                st.info("Please upload a PDF file.")
    elif task == "Query Financial Reports":
        year = str(st.sidebar.selectbox('Year', range(2025,2020,-1)))
        quarter = st.sidebar.multiselect('Quarter:', ["Q1", "Q2", "Q3", "Q4"], default=['Q1'])
        select_parser = st.sidebar.selectbox('Parser:', list(pdfparser.keys()))
        parser = pdfparser[select_parser]
        select_chunk_strategy = st.sidebar.selectbox('Select Chunking Strategy:', list(chunking.keys()))
        chunk_strategy = chunking[select_chunk_strategy]
        select_vector_store = st.sidebar.selectbox('Select Vector Store:', list(vectorstores.keys()))
        vector_store = vectorstores[select_vector_store]
        st.sidebar.text("Enter query here:")
        query = st.sidebar.chat_input(placeholder = "Write your query here...")
        if query:
            if len(quarter) > 0:
                st.session_state.messages.clear()
                st.session_state.messages.append({"role": "user", "content": query})
                with st.chat_message("user"):
                    st.markdown(query)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            # time.sleep(2)
                            response = requests.post(
                                f"{API_URL}/query_nvdia_documents",
                                json={
                                    "year": year,
                                    "quarter": quarter,
                                    "parser": parser,
                                    "chunk_strategy": chunk_strategy,
                                    "vector_store": vector_store,
                                    "query": query,
                                }
                            )
                            if response.status_code == 200:
                                answer = response.json()["answer"]
                                st.markdown(answer)
                                st.session_state.messages.append({"role": "assistant", "content": answer})
                            else:
                                error_message = f"Error: {response.text}"
                                st.error(error_message)
                                st.session_state.messages.append({"role": "assistant", "content": error_message})
                        except Exception as e:
                            error_message = f"Error: {str(e)}"
                            # st.error(error_message)
                            st.session_state.messages.append({"role": "assistant", "content": error_message})
                # st.write(st.session_state.messages)
            else:
                st.info("Please select all the required details")
            
def convert_PDF_to_markdown(file_upload, parser):    
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    progress_text.text("Uploading file...")
    progress_bar.progress(20)

    if file_upload is not None:
        bytes_data = file_upload.read()
        base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
        
        progress_text.text("Sending file for processing...")
        progress_bar.progress(50)

        response = requests.post(f"{API_URL}/upload_pdf", json={"file": base64_pdf, "file_name": file_upload.name, "parser": parser})
        
        progress_text.text("Processing document...")
        progress_bar.progress(75)
        
        try:
            if response.status_code == 200:
                data = response.json()
                progress_text.text("Finalizing output...")
                # st.subheader(data["message"])
                st.success("Document Processed Successfully!")
                progress_bar.progress(100)
                progress_text.empty()
                progress_bar.empty()    
                return data["file_name"], data["scraped_content"]
            else:
                st.error("Server not responding.")
        except:
            st.error("An error occurred while processing the PDF.")
    

def generate_query_response(markdown_content, query, parser, chunk_strategy, vector_store):
    # st.session_state.messages.clear()
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # time.sleep(2)
                response = requests.post(
                    f"{API_URL}/query_document",
                    json={
                        "parser": parser,
                        "chunk_strategy": chunk_strategy,
                        "vector_store": vector_store,
                        "markdown_content": markdown_content,
                        "query": query,
                    }
                )
                if response.status_code == 200:
                    answer = response.json()["answer"]
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    # st.markdown(answer)
                    return answer
                else:
                    error_message = f"Error: {response.text}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"Error: {str(e)}"
                # st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
    
if __name__ == "__main__":
# Set page configuration
    st.set_page_config(
        page_title="NVDIA Financial Report Analysis",
        layout="wide",
        initial_sidebar_state="expanded"
    )    
    main()