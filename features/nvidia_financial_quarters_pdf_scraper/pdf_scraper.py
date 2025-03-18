from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time


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

years_to_select = ["2025", "2024", "2023", "2022", "2021", "2020"]

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
            ten_k_q_links.append({
                "year": year,
                "type": link_text,
                "url": url
            })

driver.quit()

from services.s3 import S3FileManager
for link in ten_k_q_links:
    
    print(link)