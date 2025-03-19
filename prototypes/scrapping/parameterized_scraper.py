import os
import sys
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import boto3

class S3FileManager:
    """Simple S3 file manager class to replace the missing services.s3 module"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def upload_file(self, bucket_name, key, content):
        """Upload content to S3 bucket with specified key"""
        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=content,
            ContentType='application/pdf'
        )

def quarter_to_text(quarter):
    """Convert quarter code to full text"""
    mapping = {
        "Q1": "First Quarter",
        "Q2": "Second Quarter",
        "Q3": "Third Quarter",
        "Q4": "Fourth Quarter"
    }
    return mapping.get(quarter)

def upload_pdf_from_url_to_s3(pdf_url, bucket_name, s3_key):
    """
    Uploads a PDF from a URL directly to an S3 bucket.
    """
    try:
        # Fetch the PDF content from the URL
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        # Initialize S3FileManager
        s3 = S3FileManager()
        # Upload the PDF content to S3
        s3.upload_file(bucket_name, s3_key, response.content)
        print(f"Uploaded {s3_key} to S3 bucket {bucket_name}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch PDF from URL: {e}")
    except Exception as e:
        print(f"Failed to upload PDF to S3: {e}")
    return False

def fetch_and_upload_nvidia_report(target_year, target_quarter):
    """
    Fetches and uploads a specific NVIDIA financial report based on year and quarter.
    
    Args:
        target_year (str): The fiscal year to fetch (e.g., "2025")
        target_quarter (str): The quarter to fetch (e.g., "Q1", "Q2", "Q3", "Q4")
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Validate inputs
    if target_year not in ["2025", "2024", "2023", "2022", "2021", "2020"]:
        print(f"Invalid year: {target_year}. Must be between 2020-2025.")
        return False
    
    if target_quarter not in ["Q1", "Q2", "Q3", "Q4"]:
        print(f"Invalid quarter: {target_quarter}. Must be Q1, Q2, Q3, or Q4.")
        return False
    
    # Convert quarter code to text format
    quarter_text = quarter_to_text(target_quarter)
    # Create the text to search for in the accordion title
    accordion_title_text = f"{quarter_text} {target_year}"
    
    print(f"Searching for accordion with title: '{accordion_title_text}'")
    
    # Set up Chrome options for headless mode
    options = Options()
    options.add_argument("--headless=new")  # Use the new headless mode
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Set up the WebDriver with options
    driver = webdriver.Chrome(options=options)
    driver.get("https://investor.nvidia.com/financial-info/quarterly-results/default.aspx")
    driver.implicitly_wait(10)

    print(f"Searching for NVIDIA {target_year} {target_quarter} financial report...")

    try:
        # Select the year from dropdown
        dropdown_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "_ctrl0_ctl75_selectEvergreenFinancialAccordionYear"))
        )
        dropdown = Select(dropdown_element)
        dropdown.select_by_visible_text(target_year)
        print(f"Selected year: {target_year}")
        
        # Wait for page to update after selecting year
        time.sleep(3)
        
        # Use JavaScript to ensure page is fully loaded
        driver.execute_script("return document.readyState") == "complete"
        
        # Find all accordion titles
        accordion_titles = driver.find_elements(By.CSS_SELECTOR, "span.evergreen-accordion-title")
        
        # Debug information
        print(f"Found {len(accordion_titles)} accordion titles")
        for idx, title in enumerate(accordion_titles):
            print(f"Accordion {idx+1}: '{title.text}'")
        
        # Find the specific accordion for the target quarter
        target_accordion = None
        for title in accordion_titles:
            if accordion_title_text in title.text:
                target_accordion = title
                print(f"Found matching accordion: '{title.text}'")
                break
        
        if not target_accordion:
            print(f"Could not find accordion for {quarter_text} {target_year}")
            driver.quit()
            return False
        
        # Multiple approaches to click the accordion
        success = False
        
        # Approach 1: Click the title directly
        if not success:
            try:
                target_accordion.click()
                print("Clicked accordion title directly")
                time.sleep(2)
                success = True
            except Exception as e:
                print(f"Error clicking accordion title: {e}")
        
        # Approach 2: Find parent element and click
        if not success:
            try:
                # Use JavaScript to click the parent
                driver.execute_script("arguments[0].closest('.accordion-toggle').click();", target_accordion)
                print("Clicked accordion using JavaScript")
                time.sleep(2)
                success = True
            except Exception as e:
                print(f"Error with JavaScript click: {e}")
        
        # Approach 3: Find by XPath with contains text
        if not success:
            try:
                xpath = f"//span[contains(text(), '{accordion_title_text}')]/ancestor::div[contains(@class, 'accordion-toggle') or contains(@class, 'evergreen-accordion-toggle')]"
                toggle = driver.find_element(By.XPATH, xpath)
                toggle.click()
                print("Clicked using XPath with text contains")
                time.sleep(2)
                success = True
            except Exception as e:
                print(f"Error with XPath approach: {e}")
        
        # Look for 10-K or 10-Q in the expanded accordion
        report_type = "10-K" if target_quarter == "Q4" else "10-Q"
        
        # Find all PDF links
        pdf_links = driver.find_elements(By.CSS_SELECTOR, "a.evergreen-financial-accordion-attachment-PDF")
        
        # Debug information
        print(f"Found {len(pdf_links)} PDF links")
        for idx, link in enumerate(pdf_links):
            print(f"PDF {idx+1}: '{link.text}' - {link.get_attribute('href')}")
        
        target_link = None
        for link in pdf_links:
            link_text = link.text.strip()
            url = link.get_attribute("href")
            
            if url and url.endswith(".pdf") and report_type in link_text:
                target_link = {
                    "year": target_year,
                    "type": link_text,
                    "url": url
                }
                print(f"Found {report_type} link: {url}")
                break
        
        driver.quit()
        
        if target_link:
            # Environment Variables
            AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
            if not AWS_BUCKET_NAME:
                print("AWS_BUCKET_NAME environment variable not set")
                return False
                
            base_path = "nvidia/raw_pdf_files/"
            s3_filename = f"FY{target_year}{target_quarter}.pdf"
            s3_key = base_path + s3_filename
            
            success = upload_pdf_from_url_to_s3(target_link["url"], AWS_BUCKET_NAME, s3_key)
            return success
        else:
            print(f"Could not find {report_type} report for {target_quarter} {target_year}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        driver.quit()
        return False

if __name__ == "__main__":
    # Check if correct number of arguments provided
    if len(sys.argv) != 3:
        print("Usage: python script.py <year> <quarter>")
        print("Example: python script.py 2024 Q4")
        sys.exit(1)
    
    year = sys.argv[1]
    quarter = sys.argv[2].upper()  # Convert to uppercase for consistency
    
    success = fetch_and_upload_nvidia_report(year, quarter)
    
    if success:
        print(f"Successfully fetched and uploaded NVIDIA FY{year}{quarter} report")
        sys.exit(0)
    else:
        print(f"Failed to fetch and upload NVIDIA FY{year}{quarter} report")
        sys.exit(1)
