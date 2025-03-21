from datetime import datetime
from airflow.models import Variable
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.task_group import TaskGroup

from nvidia_raw_pdf_handler.links_to_s3_push import upload_pdf_to_s3
from nvidia_raw_pdf_handler.website_scraper import scrape_from_nvidia_website
from nvidia_raw_pdf_processing.docling_pdf_extractor_caller import pdf_docling_converter
from nvidia_raw_pdf_processing.mistralocr_pdf_extractor_caller import pdf_mistralocr_converter

# Fetch Airflow variables
AWS_BUCKET_NAME = Variable.get("AWS_BUCKET_NAME")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    dag_id='nvidia_financial_docs_scraper_and_loader_v3',
    default_args=default_args,
    tags=['nvidia'],
    description='Extract NVIDIA financial documents for one year and all 4-Qs, transform using Docling or Mistral, and load into S3',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_tasks=4,
) as dag:

    # Task 1: Scrape from NVIDIA website
    scrape = PythonOperator(
        task_id='scrape_from_nvidia_website',
        python_callable=scrape_from_nvidia_website,
    )

    # Upload tasks dictionary
    upload_tasks = {}
    for i in range(4, 0, -1):  
        upload_tasks[i] = PythonOperator(
            task_id=f'Upload_to_S3_Q{i}',
            python_callable=upload_pdf_to_s3,
            provide_context=True,
            op_kwargs={'task_id': f'Upload_to_S3_Q{i}'},
        )

    # Processing TaskGroups (Docling & Mistral)
    docling_tasks = {}
    mistral_tasks = {}

    with TaskGroup("Docling_Processing") as docling_cluster:
        for i in range(4, 0, -1):
            docling_tasks[i] = PythonOperator(
                task_id=f'Parse_via_Docling_Q{i}',
                python_callable=pdf_docling_converter,
                provide_context=True,
                op_kwargs={'quarter': i, 'source_task_id': f'Upload_to_S3_Q{i}'},
            )

    with TaskGroup("Mistral_Processing") as mistral_cluster:
        for i in range(4, 0, -1):
            mistral_tasks[i] = PythonOperator(
                task_id=f'Parse_via_Mistral_Q{i}',
                python_callable=pdf_mistralocr_converter,
                provide_context=True,
                op_kwargs={'quarter': i, 'source_task_id': f'Upload_to_S3_Q{i}'},
            )

    # Task to trigger another DAG after all processing tasks are complete
    trigger_next_dag = TriggerDagRunOperator(
        task_id="trigger_next_dag",
        trigger_dag_id="next_dag_id",  # Replace with actual DAG ID of the next DAG
        wait_for_completion=False,  # Set to True if you need to wait for the next DAG's completion
    )

    # **Correctly linking tasks**
    scrape >> list(upload_tasks.values())  # Scraping triggers all upload tasks

    for i in range(4, 0, -1):  
        upload_tasks[i] >> docling_tasks[i]  # Each upload task triggers its Docling task
        upload_tasks[i] >> mistral_tasks[i]  # Each upload task triggers its Mistral task

    # Ensure the next DAG is triggered only after all processing tasks are completed
    list(docling_tasks.values()) + list(mistral_tasks.values()) >> trigger_next_dag
