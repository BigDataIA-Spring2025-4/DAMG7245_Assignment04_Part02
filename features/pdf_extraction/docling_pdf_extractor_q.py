from pathlib import Path
import io
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode, PictureItem
from docling.document_converter import PdfFormatOption
from tempfile import NamedTemporaryFile
from docling.datamodel.pipeline_options import PdfPipelineOptions
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from datetime import datetime
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

def pdf_docling_converter(quarter, source_task_id, **context):
    """
    Airflow-compatible Docling PDF converter function.

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
    base_path = f"nvidia/Q{quarter}/docling"
    
    # Configure Docling pipeline options
    pipeline_options = PdfPipelineOptions(
        do_ocr=True,
        do_table_structure=True,
        images_scale=2.0,
        generate_page_images=True,
        generate_picture_images=True,
    )

    # Initialize Docling DocumentConverter
    doc_converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        },
    )

    pdf_stream.seek(0)
    
    with NamedTemporaryFile(suffix=".pdf", delete=True) as temp_pdf:
        temp_pdf.write(pdf_stream.read())
        temp_pdf.flush()

        # Convert PDF using Docling
        conv_result = doc_converter.convert(temp_pdf.name)
        
        # Generate markdown content and upload images to S3
        final_md_content = document_convert(conv_result, base_path, s3_hook)

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

def document_convert(conv_result, base_path, s3_hook):
    """
    Helper function to convert Docling result into markdown and upload images.

    Args:
        conv_result: Result object from Docling conversion.
        base_path (str): Base path for storing images in S3.
        s3_hook (S3Hook): Airflow S3Hook instance for uploading images.

    Returns:
        str: Final markdown content with image links.
    """
    final_md_content = conv_result.document.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)
    doc_filename = conv_result.input.file.stem

    picture_counter = 0

    for element, _level in conv_result.document.iterate_items():
        if isinstance(element, PictureItem):
            picture_counter += 1

            element_image_filename = f"{base_path}/images/{doc_filename}_image_{picture_counter}.png"

            with NamedTemporaryFile(suffix=".png", delete=True) as image_file:
                element.get_image(conv_result.document).save(image_file, "PNG")
                image_file.flush()

                with open(image_file.name, "rb") as fp:
                    s3_hook.load_bytes(
                        bytes_data=fp.read(),
                        key=element_image_filename,
                        bucket_name=AWS_BUCKET_NAME,
                        replace=True,
                    )

                element_image_link = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{element_image_filename}"
                logger.info(f"Uploaded image to: {element_image_link}")

            final_md_content = final_md_content.replace(
                "<!-- image -->",
                f"![Image]({element_image_link})",
                1,
            )

    return final_md_content