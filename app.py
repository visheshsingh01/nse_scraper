from flask import Flask, jsonify, send_file
import time
from nse_scraper import setup_driver, navigate_to_nse, extract_selected_columns, clean_number, save_to_excel

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('option_chain.html')

@app.route('/api/option-chain-data')
def get_option_chain_data():
    driver = setup_driver(headless=False)
    navigate_to_nse(driver)
    
    # Get the raw data
    raw_data = extract_selected_columns(driver, center_row=41, range_size=9)
    
    # Calculate totals for the needed columns
    numeric_data = []
    for row in raw_data:
        numeric_data.append([
            clean_number(row[0]),  # Call OI
            row[1],                # Call Change OI
            clean_number(row[2]),  # Call Volume
            row[3],                # Call IV
            row[4],                # Put IV
            clean_number(row[5]),  # Put Volume
            row[6],                # Put Change OI
            clean_number(row[7])   # Put OI
        ])
    
    # Calculate totals
    total_call_oi = sum(row[0] for row in numeric_data)
    total_call_volume = sum(row[2] for row in numeric_data)
    total_put_volume = sum(row[5] for row in numeric_data) 
    total_put_oi = sum(row[7] for row in numeric_data)
    
    # Create totals row and format back to strings with commas
    totals_row = [
        f"{total_call_oi:,}",  # Call OI
        "",                    # Call Change OI
        f"{total_call_volume:,}", # Call Volume
        "",                    # Call IV
        "",                    # Put IV
        f"{total_put_volume:,}", # Put Volume
        "",                    # Put Change OI
        f"{total_put_oi:,}"    # Put OI
    ]
    
    # Convert numeric data back to formatted strings
    formatted_data = []
    for row in raw_data:
        formatted_data.append(row)
    
    # Add totals row
    formatted_data.append(totals_row)
    
    driver.quit()
    return jsonify(formatted_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)