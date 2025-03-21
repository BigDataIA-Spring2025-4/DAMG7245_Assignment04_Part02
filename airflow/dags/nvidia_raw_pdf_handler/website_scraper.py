from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
def scrape_from_nvidia_website(**kwargs):
    # Get year from DAG run configuration
    year = kwargs['dag_run'].conf.get('year', '2025')  # Default to 2025 if not specified
    
    # Set up Chrome options for headless mode
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')  
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        # Set up the WebDriver with options - connect to Selenium service
        driver = webdriver.Remote(
            command_executor='http://selenium-chrome:4444/wd/hub',
            options=options
        )

        driver.get("https://investor.nvidia.com/financial-info/quarterly-results/default.aspx")
        driver.implicitly_wait(10)
        
        print("Current URL:", driver.current_url)

        dropdown_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "_ctrl0_ctl75_selectEvergreenFinancialAccordionYear"))
        )
        dropdown = Select(dropdown_element)

        # Select the specified year
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
        
        ten_k_q_links = []
        for link in links:
            link_text = link.text.strip()
            url = link.get_attribute("href")
            
            if url and url.endswith(".pdf") and ("10-K" in link_text or "10-Q" in link_text):
                quarter = None
                if "/q1" in url.lower():
                    quarter = "Q1"
                elif "/q2" in url.lower():
                    quarter = "Q2"
                elif "/q3" in url.lower():
                    quarter = "Q3"
                elif "/q4" in url.lower() or "10-K" in link_text:
                    quarter = "Q4"
                
                ten_k_q_links.append({
                    "year": year,
                    "type": link_text,
                    "url": url,
                    "quarter": quarter
                })
        
        # Push to XCom for the next task
        kwargs['ti'].xcom_push(key='nvidia_financial_docs', value=ten_k_q_links)
        
        print(f"Found {len(ten_k_q_links)} financial documents for year {year}")
        for doc in ten_k_q_links:
            print(f"Year: {doc['year']}, Quarter: {doc['quarter']}, Type: {doc['type']}, URL: {doc['url']}")
            
        return ten_k_q_links
        
    finally:
        driver.quit()