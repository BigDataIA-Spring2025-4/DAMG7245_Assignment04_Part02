import requests
import boto3
import os
from prototypes.s3 import S3FileManager

def upload_pdf_from_url_to_s3(pdf_url, bucket_name, s3_key):
    """
    Uploads a PDF from a URL directly to an S3 bucket.

    :param pdf_url: URL of the PDF file.
    :param bucket_name: Name of the S3 bucket.
    :param s3_key: S3 key (path) where the PDF will be stored.
    """

    try:
        # Fetch the PDF content from the URL
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes

        # Upload the PDF content to S3
        s3.upload_file(bucket_name, s3_key, response.content)
        print(f"Uploaded {s3_key} to S3 bucket {bucket_name}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch PDF from URL: {e}")
    except Exception as e:
        print(f"Failed to upload PDF to S3: {e}")



if __name__ == "__main__":
    # Example usage
    pdf_url = "https://s201.q4cdn.com/141608511/files/doc_financials/2025/q3/ed2a395c-5e9b-4411-8b4a-a718d192155a.pdf"
    
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    base_path = "pdf/NVIDIA/"
    s3 = S3FileManager(AWS_BUCKET_NAME, base_path)
    s3_key = base_path + "/".join(pdf_url.split('/')[-3:])

    upload_pdf_from_url_to_s3(pdf_url, AWS_BUCKET_NAME, s3_key)