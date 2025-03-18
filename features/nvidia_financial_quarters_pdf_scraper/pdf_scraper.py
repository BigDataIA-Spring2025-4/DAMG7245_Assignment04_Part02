import os
import sys
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from s3 import S3FileManager

def fetch_and_upload_nvidia_report(year):
    # Set up Chrome options for headless mode
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Set up the WebDriver with options
    driver = webdriver.Chrome(options=options)
    driver.get("https://investor.nvidia.com/financial-info/quarterly-results/default.aspx")

    driver.implicitly_wait(10)

    print("Current URL:", driver.current_url)

    dropdown_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "_ctrl0_ctl75_selectEvergreenFinancialAccordionYear"))
    )
    dropdown = Select(dropdown_element)

    years_to_select = [year]

    ten_k_q_links = []

    for year in years_to_select:
        dropdown.select_by_visible_text(year)
        print(f"Selected year: {year}")
        time.sleep(3)
        # Find all accordion toggles and expand them
        toggles = driver.find_elements(By.CSS_SELECTOR, ".accordion-toggle-icon.evergreen-icon-plus")
        for toggle in toggles:
            try:
                toggle.click()
                time.sleep(1)
            except:
                pass
        
        links = driver.find_elements(By.CSS_SELECTOR, "a.evergreen-financial-accordion-attachment-PDF")
        
        for link in links:
            link_text = link.text.strip()
            url = link.get_attribute("href")
            
            if url and url.endswith(".pdf") and ("10-K" in link_text or "10-Q" in link_text):
                quarter = None
                if "/q1/" in url.lower():
                    quarter = "Q1"
                elif "/q2/" in url.lower():
                    quarter = "Q2"
                elif "/q3/" in url.lower():
                    quarter = "Q3"
                elif "/q4/" in url.lower() or "10-K" in link_text:
                    quarter = "Q4"
                
                ten_k_q_links.append({
                    "year": year,
                    "type": link_text,
                    "url": url,
                    "quarter": quarter
                })

    driver.quit()

    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    base_path = "nvidia/raw_pdf_files"

    s3_manager = S3FileManager(AWS_BUCKET_NAME, base_path)

    def upload_pdf_from_url_to_s3(pdf_url, file_name):
        """
        Uploads a PDF from a URL directly to an S3 bucket.

        :param pdf_url: URL of the PDF file.
        :param file_name: File name to use in S3.
        """
        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            s3_key = f"{base_path}/{file_name}"
        
            s3_manager.upload_file(AWS_BUCKET_NAME, s3_key, response.content)
            print(f"Uploaded {file_name} to S3 bucket {AWS_BUCKET_NAME} at {s3_key}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch PDF from URL {pdf_url}: {e}")
            return False
        except Exception as e:
            print(f"Failed to upload PDF to S3: {e}")
            return False

    # Process each link and upload to S3
    for link in ten_k_q_links:
        year = link["year"]
        quarter = link["quarter"]
        url = link["url"]
        
        if quarter:
            file_name = f"FY{year}{quarter}.pdf"
        else:
            file_name = f"FY{year}_{link['type'].replace(' ', '_')}.pdf"
        
        print(f"Uploading {file_name} from {url}")
        success = upload_pdf_from_url_to_s3(url, file_name)
        
        if success:
            print(f"Successfully uploaded {file_name}")
        else:
            print(f"Failed to upload {file_name}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <year>")
        print("Example: python script.py 2024")
        sys.exit(1)
    
    year = sys.argv[1]
    success = fetch_and_upload_nvidia_report(year)