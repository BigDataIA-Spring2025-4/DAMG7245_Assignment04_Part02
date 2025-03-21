import os
import io
import base64
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from mistralai import Mistral, DocumentURLChunk
from mistralai.models import OCRResponse
from PIL import Image
from datetime import datetime
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AWS_BUCKET_NAME = Variable.get("AWS_BUCKET_NAME")
MISTRALAI_API_KEY = Variable.get("MISTRALAI_API_KEY")

def pdf_mistralocr_converter(quarter, source_task_id, **context):
    """
    Airflow-compatible Mistral OCR PDF converter function.

    Args:
        quarter (int): Quarter number (e.g., 1, 2, 3, or 4).
        source_task_id (str): Task ID of the upload task to fetch PDF location from XCom.
        context: Airflow context dictionary.
    """
    # Retrieve PDF file path from XCom pushed by upload task
    ti = context['ti']
    pdf_s3_key = ti.xcom_pull(task_ids=source_task_id)

    if not pdf_s3_key:
        raise ValueError(f"No PDF file path found in XCom from task {source_task_id}")

    s3_hook = S3Hook(aws_conn_id='aws_default')

    # Download PDF content as bytes from S3
    pdf_bytes = s3_hook.read_key(pdf_s3_key, bucket_name=AWS_BUCKET_NAME)
    pdf_stream = io.BytesIO(pdf_bytes)

    # Define base path for processed files in S3
    base_path = f"nvidia/Q{quarter}/mistral"

    # Initialize Mistral client
    client = Mistral(api_key=MISTRALAI_API_KEY)

    # Upload PDF to Mistral's OCR service
    uploaded_file = client.files.upload(
        file={
            "file_name": f"nvidia_Q{quarter}_document.pdf",
            "content": pdf_stream.getvalue(),
        },
        purpose="ocr",
    )

    # Get signed URL for uploaded file (expires in 1 hour)
    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

    # Process PDF with OCR (including embedded images)
    ocr_response = client.ocr.process(
        document=DocumentURLChunk(document_url=signed_url.url),
        model="mistral-ocr-latest",
        include_image_base64=True,
    )

    # Generate markdown content and upload images to S3
    final_md_content = get_combined_markdown(ocr_response, s3_hook, base_path)

    # Prepare markdown filename with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    md_file_name = f"{base_path}/extracted_{timestamp}.md"

    # Upload markdown content to S3
    s3_hook.load_string(
        string_data=final_md_content,
        key=md_file_name,
        bucket_name=AWS_BUCKET_NAME,
        replace=True,
    )

    logger.info(f"Markdown uploaded successfully: {md_file_name}")

def replace_images_in_markdown(markdown_str: str, images_dict: dict, s3_hook: S3Hook, base_path: str) -> str:
    """
    Replace image placeholders in markdown with actual image URLs after uploading images to S3.

    Args:
        markdown_str (str): Markdown content with placeholders.
        images_dict (dict): Dictionary of image IDs and base64 strings.
        s3_hook (S3Hook): Airflow S3Hook instance for uploading images.
        base_path (str): Base path for storing images in S3.

    Returns:
        str: Markdown content with actual image URLs.
    """
    for img_name, base64_str in images_dict.items():
        logger.info(f"Processing image {img_name}")

        base64_str_cleaned = base64_str.split(';')[1].split(',')[1]
        image_data = base64.b64decode(base64_str_cleaned)

        element_image_filename = f"{base_path}/images/{img_name.split('.')[0]}.png"

        # Convert image data to PNG format using PIL
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        # Upload PNG image to S3
        s3_hook.load_bytes(
            bytes_data=output_buffer.read(),
            key=element_image_filename,
            bucket_name=AWS_BUCKET_NAME,
            replace=True,
        )

        element_image_link = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{element_image_filename}"
        
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})", f"![{img_name}]({element_image_link})"
        )

        logger.info(f"Uploaded and replaced image link: {element_image_link}")

    return markdown_str

def get_combined_markdown(ocr_response: OCRResponse, s3_hook: S3Hook, base_path: str) -> str:
    """
    Combine OCR response pages into a single markdown string with images uploaded to S3.

    Args:
        ocr_response (OCRResponse): Response object from Mistral OCR.
        s3_hook (S3Hook): Airflow S3Hook instance for uploading images.
        base_path (str): Base path for storing images in S3.

    Returns:
        str: Combined markdown content.
    """
    markdowns = []
    
    for page in ocr_response.pages:
        image_data = {}
        
        for img in page.images:
            image_data[img.id] = img.image_base64
        
        page_markdown_with_images = replace_images_in_markdown(page.markdown, image_data, s3_hook, base_path)
        
        markdowns.append(page_markdown_with_images)

    return "\n\n".join(markdowns)
