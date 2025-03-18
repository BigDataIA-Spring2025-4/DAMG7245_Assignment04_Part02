from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# Set up Chrome options for headless mode
options = Options()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--disable-dev-shm-usage")  # For resource constraints
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

pdf_links = []

for year in years_to_select:
    dropdown.select_by_visible_text(year)
    print(f"Selected year: {year}")
    
    time.sleep(3)

    # Extract all links
    links = driver.find_elements(By.TAG_NAME, "a")
    
    for link in links:
        url = link.get_attribute("href")
        if url and url.startswith("https://s201.q4cdn.com/141608511/files/doc_financials/") and url.endswith(".pdf"):
            pdf_links.append(url)

driver.quit()

for pdf in pdf_links:
    print(pdf)
