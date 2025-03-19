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
        year = st.sidebar.selectbox('Year', range(2025,2020,-1))
        quarter = st.sidebar.multiselect('Quarter:', ["Q1", "Q2", "Q3", "Q4"], default=['Q1'])
        select_parser = st.sidebar.selectbox('Parser:', list(pdfparser.keys()))
        parser = pdfparser[select_parser]
        select_chunk_strategy = st.sidebar.selectbox('Select Chunking Strategy:', list(chunking.keys()))
        chunk_strategy = chunking[select_chunk_strategy]
        st.sidebar.text("Enter query here:")
        query = st.sidebar.chat_input(placeholder = "Write your query here...")
        if query:
            st.write(f"Year: {year}")
            st.write(f"Quarter: {quarter}")
            st.write(f"Parser: {parser}")
            st.write(f"Chunk Strategy: {chunk_strategy}")
            st.write(f"Query: {query}")
        
    

if __name__ == "__main__":
# Set page configuration
    st.set_page_config(
        page_title="NVDIA Financial Report Analysis",
        layout="wide",
        initial_sidebar_state="expanded"
    )    
    main()