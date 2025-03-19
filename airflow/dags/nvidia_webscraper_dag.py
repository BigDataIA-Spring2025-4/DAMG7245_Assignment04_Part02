from datetime import datetime
from io import BytesIO
from nvidia_financial_quarters_pdf_scraper.website_scraper import scrape_from_nvidia_website
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

# Define the DAG
with DAG(
    dag_id='nvidia_financial_docs_scraper_and_loader',
    default_args=default_args,
    tags=['nvidia'],
    description='Extract NVIDIA financial documents for one year and all 4-Qs, transform it using docling or mistral, and load into S3',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:
                
        scrape_task = PythonOperator(
        task_id='scrape_from_nvidia_website',
        python_callable=scrape_from_nvidia_website,
        )

