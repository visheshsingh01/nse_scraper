import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(headless=True):
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--disable-extensions")
    
    if headless:
        chrome_options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def navigate_to_nse(driver, url="https://www.nseindia.com/option-chain"):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        print("✅ Page loaded successfully!")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Error loading page: {e}")

def clean_number(value):
    if isinstance(value, str):
        try:
            return int(value.replace(",", ""))
        except ValueError:
            return 0
    return 0

def extract_selected_columns(driver, center_row=41, range_size=9):
    try:
        table = driver.find_element(By.CSS_SELECTOR, "table#optionChainTable-indices")
        table_body = table.find_element(By.TAG_NAME, "tbody")
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        start_row = center_row - range_size
        end_row = center_row + range_size

        extracted_data = []

        for index in range(start_row - 1, end_row):
            columns = rows[index].find_elements(By.TAG_NAME, "td")
            
            if len(columns) >= 10:
                selected_columns = [col.text.strip() for col in columns[1:5] + columns[-5:-1]]
                extracted_data.append(selected_columns)

        print(f"✅ Extracted {len(extracted_data)} rows successfully!")
        return extracted_data

    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return None

def save_to_excel(data, filename="nse_option_chain.xlsx"):
    if data:
        headers = ["Call OI", "Call Change OI", "Call Volume", "Call IV", 
                   "Put IV", "Put Volume", "Put Change OI", "Put OI"]
        
        df = pd.DataFrame(data, columns=headers)
        
        # Calculate totals correctly - first convert string numbers to integers
        numeric_df = df.copy()
        for col in ["Call OI", "Call Volume", "Put Volume", "Put OI"]:
            numeric_df[col] = numeric_df[col].apply(clean_number)
            
        # Calculate the sums
        total_call_oi = numeric_df["Call OI"].sum()
        total_call_volume = numeric_df["Call Volume"].sum()
        total_put_oi = numeric_df["Put OI"].sum()
        total_put_volume = numeric_df["Put Volume"].sum()
        
        # Create a totals row with empty values for columns that don't need totals
        totals_row = {
            "Call OI": f"{total_call_oi:,}",
            "Call Change OI": "",
            "Call Volume": f"{total_call_volume:,}",
            "Call IV": "",
            "Put IV": "",
            "Put Volume": f"{total_put_volume:,}",
            "Put Change OI": "",
            "Put OI": f"{total_put_oi:,}"
        }
        
        # Append totals row to DataFrame
        df = df._append(totals_row, ignore_index=True)

        df.to_excel(filename, index=False)
        print(f"✅ Data saved to {filename}")


def main():
    driver = setup_driver(headless=False)
    navigate_to_nse(driver)
    extracted_data = extract_selected_columns(driver, center_row=41, range_size=9)
    save_to_excel(extracted_data)
    driver.quit()
    print("✅ Scraping completed!")

if __name__ == "__main__":
    main()