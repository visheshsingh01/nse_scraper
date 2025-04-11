import os
import time
import logging
import urllib.parse
import random
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
    """Set up a Selenium Chrome WebDriver with optimizations for Docker & anti-bot measures."""
    options = webdriver.ChromeOptions()

    # ✅ Essential arguments for running in Docker & Render
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage")  
    options.add_argument("--disable-gpu")  
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")  
    options.add_argument("--log-level=3")  
    options.add_argument("--start-maximized")

    if headless:
        options.add_argument("--headless=new")  

    # ✅ Prevent multiple instances from using the same Chrome profile
    options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{int(time.time())}")

    # ✅ Rotate User-Agent to bypass detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    ]
    random_user_agent = random.choice(user_agents)
    options.add_argument(f"user-agent={random_user_agent}")

    # ✅ Explicitly set Chrome binary & Chromedriver path in Docker
    chrome_binary = os.getenv("CHROMIUM_PATH", "/usr/bin/chromium")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    options.binary_location = chrome_binary

    service = Service(chromedriver_path if os.path.exists(chromedriver_path) else ChromeDriverManager().install())
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

def extract_selected_columns(driver):
    """Extract rows based on color marking in specific columns:
       - Scenario 1: When the second column in a row does NOT have 'bg-yellow',
         extract the 9 rows immediately above that row.
       - Scenario 2: When the second column in a row does NOT have 'bg-yellow' 
         but the 13th column DOES have 'bg-yellow', extract that row and the next 8 rows.
       
       For each extracted row, we extract columns 2-5 and the last 4 columns.
    """
    try:
        table = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "table#optionChainTable-indices"))
        )
        table_body = table.find_element(By.TAG_NAME, "tbody")
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        
        extracted_data = []
        scenario1_done = False
        scenario2_done = False

        # Iterate through every row by index
        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 13:
                # Skip rows that don't have enough columns to check scenario 2
                continue

            # Scenario 1: Check if second column does NOT have "bg-yellow"
            col2_class = cells[1].get_attribute("class")
            if not scenario1_done and "bg-yellow" not in col2_class:
                if i >= 9:  # Ensure there are 9 rows above
                    for j in range(i - 9, i):
                        r = rows[j]
                        cols = r.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 10:
                            # Extract columns 2-5 and the last 4 columns
                            data_row = [col.text.strip() for col in cols[1:5] + cols[-5:-1]]
                            extracted_data.append(data_row)
                    scenario1_done = True

            # Scenario 2: Check if col2 does NOT have "bg-yellow" and col13 DOES have "bg-yellow"
            col13_class = cells[12].get_attribute("class")
            if not scenario2_done and ("bg-yellow" not in col2_class) and ("bg-yellow" in col13_class):
                # Extract 9 rows starting with current row, if available
                end_index = min(i + 9, len(rows))
                for j in range(i, end_index):
                    r = rows[j]
                    cols = r.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 10:
                        data_row = [col.text.strip() for col in cols[1:5] + cols[-5:-1]]
                        extracted_data.append(data_row)
                scenario2_done = True

            # If both scenarios are done, we can exit early
            if scenario1_done and scenario2_done:
                break

        logging.info("✅ Extracted %s rows successfully!", len(extracted_data))
        return extracted_data
    except Exception as e:
        logging.error("❌ Error extracting data: %s", e)
        return None

@app.route("/")
def index():
    # Initialize and run the scraper
    driver = setup_driver(headless=False)
    
    data = []
    if navigate_to_nse(driver):
        data = extract_selected_columns(driver)
    
    driver.quit()
    
    if not data:
        data = []
        
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
            <p>No data found.</p>
        {% endif %}
      </body>
    </html>
    """
    return render_template_string(html_template, data=data)
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)