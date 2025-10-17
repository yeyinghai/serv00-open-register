import requests
import os
import json

# --- Configuration ---
API_URL = 'https://panel.serv00.com/api/stats' 
PANEL_URL = 'https://panel.serv00.com/' 
HOME_URL = 'https://www.serv00.com/' 

BARK_KEY = os.getenv('BARK_KEY')
BARK_SERVER_URL = os.getenv('BARK_SERVER_URL', 'https://api.day.app')
LAST_VALUE_FILE = 'last_accounts.txt'

# --- Helper Functions (Unchanged) ---
def send_bark_notification(title, body, url_to_open):
    if not BARK_KEY:
        print("Warning: Bark Key not set, skipping notification.")
        return
    api_url = f"{BARK_SERVER_URL}/{BARK_KEY}"
    payload = {"title": title, "body": body, "url": url_to_open, "group": "Serv00 Checker"}
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        if response.json().get("code") == 200:
            print("Bark push notification sent successfully!")
        else:
            print(f"Failed to send Bark notification: {response.text}")
    except Exception as e:
        print(f"Error sending Bark notification: {e}")

def get_last_known_accounts():
    try:
        if os.path.exists(LAST_VALUE_FILE):
            with open(LAST_VALUE_FILE, 'r') as f:
                content = f.read().strip()
                if content: return int(content)
    except (IOError, ValueError) as e:
        print(f"Warning: Could not read or parse old accounts file ({LAST_VALUE_FILE}): {e}")
    return None

def update_last_known_accounts(value):
    try:
        with open(LAST_VALUE_FILE, 'w') as f:
            f.write(str(value))
        print(f"Updated status file {LAST_VALUE_FILE} with new value: {value}")
    except IOError as e:
        print(f"Error: Could not write to status file: {e}")

# --- Core Function (Definitive Version) ---
def check_serv00_status():
    """
    Definitive solution combining all necessary steps:
    1. Use a Session to manage cookies.
    2. Visit the API's parent domain (panel.serv00.com) to get the correct session cookie.
    3. Make the API call with a complete set of browser-mimicking headers,
       including User-Agent, Referer, X-Requested-With, and the crucial Accept header.
    """
    print("Initializing session...")
    
    last_known_accounts = get_last_known_accounts()
    
    # Base headers applied to the entire session
    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    
    with requests.Session() as s:
        s.headers.update(base_headers)
        
        try:
            # --- Step 1: Get the correct cookie from the API's domain ---
            print(f"Visiting panel domain {PANEL_URL} to acquire the correct session cookie...")
            s.get(PANEL_URL, timeout=15).raise_for_status()
            print("Panel domain visited successfully, session cookie stored automatically.")

            # --- Step 2: Make the API call with the complete, correct headers ---
            print(f"Requesting API: {API_URL}...")
            
            # This complete header set is the key to success.
            api_headers = {
                'Accept': 'application/json, text/plain, */*', # The final missing piece
                'Referer': HOME_URL,
                'X-Requested-With': 'XMLHttpRequest'
            } 
            response = s.get(API_URL, headers=api_headers, timeout=15)
            
            response.raise_for_status()
            data = response.json()

            # Data Extraction and Comparison Logic (Unchanged)
            if 'accounts' not in data or 'total' not in data['accounts'] or 'limit' not in data['accounts']:
                print(f"Error: API response format is incorrect. Data received: {data}")
                send_bark_notification("Serv00 Script Error", "API data format is incorrect.", HOME_URL)
                return

            current_accounts = int(data['accounts']['total'])
            max_accounts = int(data['accounts']['limit'])

            print(f"Status: Successfully fetched current value from API -> {current_accounts} / {max_accounts}")
            if last_known_accounts is not None:
                 print(f"Record: Last known value was -> {last_known_accounts}")
            else:
                 print(f"Record: First run, no previous record.")

            if last_known_accounts is None:
                print("First run, recording initial value...")
                update_last_known_accounts(current_accounts)

            elif current_accounts != last_known_accounts:
                print("!!! VALUE HAS CHANGED !!!")
                notification_title = "Serv00 Account Number Changed!"
                notification_body = f"Account number changed from {last_known_accounts} to {current_accounts}.\nTotal limit: {max_accounts}."
                send_bark_notification(title=notification_title, body=notification_body, url_to_open=HOME_URL)
                update_last_known_accounts(current_accounts)
                
            else:
                print("Judgment: Value has not changed.")

        except requests.exceptions.RequestException as e:
            print(f"A network error occurred during access: {e}")
            send_bark_notification("Serv00 Script Error", f"Could not access website or API: {e}", HOME_URL)
        except json.JSONDecodeError:
            print(f"Error: Could not parse JSON data from API response. Server response: {response.text}")
            send_bark_notification("Serv00 Script Error", "API did not return valid JSON.", HOME_URL)
        except Exception as e:
            print(f"An unknown error occurred during processing: {e}")
            send_bark_notification("Serv00 Script Critical Error", f"An unexpected error occurred during execution: {e}", HOME_URL)

if __name__ == "__main__":
    check_serv00_status()
