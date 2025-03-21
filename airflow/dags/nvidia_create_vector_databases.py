from datetime import datetime
from airflow.models import Variable
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from vectordatabases.chromadb.chromadb_openai import create_chromadb
from vectordatabases.manual_rag.manual_stores import get_manual_vector_doc
from vectordatabases.pinecone.pinecone_openai import create_pinecone

# Fetch Airflow variables
AWS_BUCKET_NAME = Variable.get("AWS_BUCKET_NAME")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    dag_id='nvidia_create_vector_databases',
    default_args=default_args,
    tags=['nvidia'],
    description='Load the prased NVIDIA financial documents into 3 vector stores - chromadb,pinecone and manual implementation',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    # Task 1: Create ChromaDB vector space
    chromadb = PythonOperator(
        task_id='create_chroma_db_vector_space',
        python_callable=create_chromadb,
    )

    # Task 2: Create Manual vector space generator
    manualdb = PythonOperator(
        task_id='create_manual_db_vector_space',
        python_callable=get_manual_vector_doc,
    )

    # Task 3: Create Pinecone vector space generator
    pineconedb = PythonOperator(
        task_id='create_pinecone_db_vector_space',
        python_callable=create_pinecone,
    )
