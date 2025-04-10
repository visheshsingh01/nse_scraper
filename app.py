
import time
import logging
import urllib.parse
import json
import pandas as pd
from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

def setup_driver(headless=True):
    """Set up Selenium Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    
    # ✅ Fix user-data-dir issue by using a unique temp directory
    options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{int(time.time())}")

    # ✅ Common arguments
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")  # ✅ Required for running in Docker
    options.add_argument("--disable-dev-shm-usage")  # ✅ Prevent memory issues in Docker
    options.add_argument("--disable-gpu")  # ✅ Ensure stability

    if headless:
        options.add_argument("--headless=new")  # ✅ Required for new headless mode

    # ✅ Set a Real User-Agent to Bypass Detection
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.84 Safari/537.36"
    )

    # ✅ Ensure ChromeDriver is installed correctly
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def navigate_to_nse(driver, url="https://www.nseindia.com/option-chain"):
    """Navigate to the NSE Option Chain page."""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        logging.info("✅ Page loaded successfully!")
        time.sleep(5)  # Allow dynamic content to load
    except Exception as e:
        logging.error("❌ Error loading page: %s", e)

def clean_number(value):
    """Convert formatted string numbers to integer."""
    if isinstance(value, str):
        try:
            return int(value.replace(",", ""))
        except ValueError:
            return 0
    return 0

def extract_selected_columns(driver, center_row=41, range_size=9):
    """Extract selected rows and columns from the NSE Option Chain table."""
    try:
        table = WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "table#optionChainTable-indices")))
        table_body = table.find_element(By.TAG_NAME, "tbody")
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        start_row = center_row - range_size
        end_row = center_row + range_size
        extracted_data = []
        # Loop through the desired range (adjusting for zero-based index)
        for index in range(start_row - 1, end_row):
            columns = rows[index].find_elements(By.TAG_NAME, "td")
            if len(columns) >= 10:
                # Extract columns 2-5 and the last 4 columns (you may adjust these as needed)
                selected_columns = [col.text.strip() for col in columns[1:5] + columns[-5:-1]]
                extracted_data.append(selected_columns)
        logging.info("✅ Extracted %s rows successfully!", len(extracted_data))
        return extracted_data
    except Exception as e:
        logging.error("❌ Error extracting data: %s", e)
        return None

# Optional: A scrolling function if needed (can be improved further)
def scroll_page(driver, target_ads=10, max_scrolls=10):
    ad_selector = "div.x193iq5w.xxymvpz.xeuugli.x78zum5.x1iyjqo2.xs83m0k.x1d52u69.xktsk01.x1yztbdb.x1gslohp"
    last_count = len(driver.find_elements(By.CSS_SELECTOR, ad_selector))
    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        current_count = len(driver.find_elements(By.CSS_SELECTOR, ad_selector))
        if current_count >= target_ads:
            break
        if current_count == last_count:
            break
        last_count = current_count
    logging.info("Scrolling finished. Total elements found: %s", last_count)

@app.route("/")
def index():
    driver = None
    data = []
    try:
        # Initialize and run the scraper
        driver = setup_driver(headless=True)
        navigate_to_nse(driver)
        data = extract_selected_columns(driver, center_row=41, range_size=9)
    except Exception as e:
        logging.error("Error in scraper: %s", e)
    finally:
        # Make sure the driver is always properly closed
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    # Define a simple HTML template to show data in a table
    html_template = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>NSE Option Chain Data</title>
        <style>
            table, th, td {
                border: 1px solid #333;
                border-collapse: collapse;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
      </head>
      <body>
        <h1>NSE Option Chain Data</h1>
        {% if data and data|length > 0 %}
        <table>
            <thead>
                <tr>
                    <th>Call OI</th>
                    <th>Call Change OI</th>
                    <th>Call Volume</th>
                    <th>Call IV</th>
                    <th>Put IV</th>
                    <th>Put Volume</th>
                    <th>Put Change OI</th>
                    <th>Put OI</th>
                </tr>
            </thead>
            <tbody>
                {% for row in data %}
                <tr>
                    {% for col in row %}
                    <td>{{ col }}</td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
            <p>No data found or error occurred during scraping.</p>
        {% endif %}
      </body>
    </html>
    """
    return render_template_string(html_template, data=data)
    

if __name__ == "__main__":
    app.run(debug=True)

