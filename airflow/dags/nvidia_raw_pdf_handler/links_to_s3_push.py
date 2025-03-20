from io import BytesIO
import requests

from airflow.models import Variable
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

# AWS bucket values
AWS_BUCKET_NAME = Variable.get("AWS_BUCKET_NAME")

def upload_pdf_to_s3(ti, **kwargs):
    """
    Upload PDF from URL directly to S3 based on the task ID and extracted quarter.
    """
    task_id = kwargs['task_id']  
    quarter_label = task_id.split('_')[-1]

    if not quarter_label.startswith('Q'):
        raise ValueError(f"Unexpected task ID format: {task_id}. Expected format: 'Upload_to_S3_Qx'.")

    quarter_number = quarter_label  # Keep 'Qx' format

    scraped_data = ti.xcom_pull(task_ids='scrape_from_nvidia_website')
    if not scraped_data:
        raise ValueError("No data retrieved from upstream task 'scrape_from_nvidia_website'")

    doc_info = next((doc for doc in scraped_data if doc['quarter'] == quarter_number), None)

    if not doc_info:
        raise ValueError(f"No document found for quarter {quarter_number}")

    year = doc_info['year']
    url = doc_info['url']

    filename = f"nvidia/raw_pdf_files/FY{year}{quarter_number}.pdf"

    response = requests.get(url)
    pdf_content = BytesIO(response.content)

    s3_hook = S3Hook(aws_conn_id='aws_default')
    s3_hook.load_file_obj(file_obj=pdf_content, bucket_name=AWS_BUCKET_NAME, key=filename, replace=True)

    return f"Uploaded {filename} to S3 bucket {AWS_BUCKET_NAME}/{filename}."