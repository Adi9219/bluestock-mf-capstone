import os
import time
import requests
import pandas as pd

def fetch_live_nav():
    # Define AMFI codes to fetch
    amfi_codes = [
        125497, # HDFC Top 100 Fund - Direct Plan - Growth
        119551, # SBI Bluechip Fund - Regular Plan - Growth
        120503, # ICICI Pru Bluechip Fund - Regular - Growth
        118632, # Nippon India Large Cap Fund - Regular - Growth
        119092, # Axis Bluechip Fund - Regular - Growth
        120841  # Kotak Bluechip Fund - Regular - Growth
    ]
    
    base_dir = r"d:\bluestock_mf_capstone"
    output_dir = os.path.join(base_dir, "data", "raw", "live_nav")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    print(f"Target directory verified/created at: {output_dir}\n")
    
    # Retry settings
    max_retries = 3
    retry_delay = 3 # seconds
    
    for code in amfi_codes:
        url = f"https://api.mfapi.in/mf/{code}"
        print(f"Fetching live NAV data for AMFI code {code} from {url}...")
        
        success = False
        for attempt in range(1, max_retries + 1):
            try:
                # Send GET request with a timeout of 15 seconds
                response = requests.get(url, timeout=15)
                
                # Raise exception for HTTP errors (e.g., 404, 500)
                response.raise_for_status()
                
                # Parse JSON response
                result = response.json()
                
                # Validate structure of JSON response
                if 'data' not in result or not isinstance(result['data'], list):
                    print(f"Error: Invalid data format received for AMFI code {code}. Missing 'data' list.")
                    break
                    
                nav_list = result['data']
                if not nav_list:
                    print(f"Warning: Received empty data list for AMFI code {code}.")
                    break
                    
                # Convert to DataFrame
                df = pd.DataFrame(nav_list)
                
                # Ensure the required columns exist
                if 'date' not in df.columns or 'nav' not in df.columns:
                    print(f"Error: Missing required columns 'date' or 'nav' in response for AMFI code {code}.")
                    break
                    
                # Reorder columns to standard format
                df = df[['date', 'nav']]
                
                # Save to CSV
                output_file = os.path.join(output_dir, f"{code}.csv")
                df.to_csv(output_file, index=False)
                print(f"Successfully saved {len(df)} records to {output_file}\n")
                success = True
                break # break out of retry loop on success
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"Attempt {attempt}/{max_retries} failed for AMFI code {code} due to network issue: {e}")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Error: Failed to fetch AMFI code {code} after {max_retries} attempts.\n")
            except requests.exceptions.HTTPError as he:
                print(f"Error: HTTP exception occurred for AMFI code {code}: {he}\n")
                break
            except ValueError as ve:
                print(f"Error: Failed to parse JSON response for AMFI code {code}: {ve}\n")
                break
            except Exception as e:
                print(f"Error: An unexpected error occurred for AMFI code {code}: {e}\n")
                break

if __name__ == "__main__":
    fetch_live_nav()
