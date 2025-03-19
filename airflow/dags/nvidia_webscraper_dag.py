from datetime import datetime
from io import BytesIO
from nvidia_raw_pdf_handler.links_to_s3_push import upload_pdf_to_s3
from nvidia_raw_pdf_handler.website_scraper import scrape_from_nvidia_website
from airflow.models import Variable
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

# Fetch Airflow variable
AWS_BUCKET_NAME = Variable.get("AWS_BUCKET_NAME")
AWS_ACCESS_KEY_ID = Variable.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = Variable.get("AWS_SECRET_ACCESS_KEY")
s3_path = f"s3://{AWS_BUCKET_NAME}"

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    dag_id='nvidia_financial_docs_scraper_and_loader_v1',
    default_args=default_args,
    tags=['nvidia'],
    description='Extract NVIDIA financial documents for one year and all 4-Qs, transform it using docling or mistral, and load into S3',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    scrape = PythonOperator(
        task_id='scrape_from_nvidia_website',
        python_callable=scrape_from_nvidia_website,
    )

    upload_tasks = []
    for i in range(4, 0, -1):  
        raw_upload_to_s3 = PythonOperator(
            task_id=f'Upload_to_S3_Q{i}', 
            python_callable=upload_pdf_to_s3,
            provide_context=True,
            op_kwargs={'task_id': f'Upload_to_S3_Q{i}'},
        )
        upload_tasks.append(raw_upload_to_s3)

    scrape >> upload_tasks