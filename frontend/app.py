import json, time
import streamlit as st
import requests, os, base64
from io import StringIO
from dotenv import load_dotenv
load_dotenv()

API_URL=os.getenv("API_URL")

pdfparser = {
        "Docling": "docling",
        "Mistral": "mistral"
    }

chunking = {
        "Markdown": "markdown",
        "Semantic": "semantic"
    }

vectorstores = {
        "Pinecone": "pinecone",
        "ChromaDB": "chromadb",
        "Manual": "manual"
    }

if 'messages' not in st.session_state:
    st.session_state.messages = []

def trigger_airflow_dag():
    st.write("Now triggering airflow dag...")
    
def main():
    
    st.title("NVDIA Financial Reports Analysis")
    # Set up navigation
    st.sidebar.header("Main Menu") 
    task = st.sidebar.selectbox("Select Task", ["Trigger Airflow", "Query Financial Reports"])
    if task == "Trigger Airflow":
        airflow = st.sidebar.button("Trigger Airflow DAG", use_container_width=True, icon = "🚀")
        if airflow:
            trigger_airflow_dag()
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
                st.write(f"Year: {year}")
                st.write(f"Quarter: {quarter}")
                st.write(f"Parser: {parser}")
                st.write(f"Chunk Strategy: {chunk_strategy}")
                st.write(f"Query: {query}")
                st.session_state.messages.clear()
                st.session_state.messages.append({"role": "user", "content": query})
                with st.chat_message("user"):
                    st.markdown(query)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            time.sleep(2)
                            response = requests.post(
                                f"{API_URL}/query_documents",
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
        
    

if __name__ == "__main__":
# Set page configuration
    st.set_page_config(
        page_title="NVDIA Financial Report Analysis",
        layout="wide",
        initial_sidebar_state="expanded"
    )    
    main()