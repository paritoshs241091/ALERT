#pip install fyers_apiv3
#pip install pyotp

from dateutil.relativedelta import relativedelta
from fyers_apiv3 import fyersModel
from matplotlib.font_manager import FontProperties
from matplotlib.table import Table
from tabulate import tabulate
from urllib import parse
import csv
import datetime
import datetime as dt
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pyotp
import pytz
import requests
import subprocess
import sys
import time

def main():
    india_timezone = pytz.timezone('Asia/Kolkata')
    today = dt.datetime.now(india_timezone)
    formatted_date = today.strftime("%d")
    formatted_month = today.strftime("%b").lower()  # Using lowercase for the abbreviated month
#    file_access_token = f"ZZZ_{formatted_date}{formatted_month}.txt"
    file_access_token = "access_token.txt"
    if os.path.exists(file_access_token):
        os.remove(file_access_token)

    if os.path.exists(file_access_token):
        print("Access token already exists")
    else:
        # Client Info (ENTER YOUR OWN INFO HERE!! Data varies from users and app types)
        FY_ID = "XP28064"  # Your fyers ID
        APP_ID_TYPE = "2"  # Keep default as 2, It denotes web login
        TOTP_KEY = "7BM4WGDX53VBXSK3RP2Q6OOBFLGRJUGB"  # TOTP secret is generated when we enable 2Factor TOTP from myaccount portal
        PIN = "4411"  # User pin for fyers account
        APP_ID = "PCNUNWNEIB"  # App ID from myapi dashboard is in the form appId-appType. Example - EGNI8CE27Q-100, In this code EGNI8CE27Q will be APP_ID and 100 will be the APP_TYPE
        REDIRECT_URI = "https://myapi.fyers.in/dashboard"  # Redirect url from the app.
        APP_TYPE = "100"
        APP_ID_HASH = "6ea7fc08111a642192457b88ba18950b52a75bc6f231d47661b8cbb4bc1844bd"  # SHA-256 hash of appId-appType:appSecret

        # API endpoints
        BASE_URL = "https://api-t2.fyers.in/vagator/v2"
        BASE_URL_2 = "https://api-t1.fyers.in/api/v3"
        URL_SEND_LOGIN_OTP = BASE_URL + "/send_login_otp"
        URL_VERIFY_TOTP = BASE_URL + "/verify_otp"
        URL_VERIFY_PIN = BASE_URL + "/verify_pin"
        URL_TOKEN = BASE_URL_2 + "/token"
        URL_VALIDATE_AUTH_CODE = BASE_URL_2 + "/validate-authcode"

        SUCCESS = 1
        ERROR = -1

        def send_login_otp(fy_id, app_id):
            try:
                payload = {
                    "fy_id": fy_id,
                    "app_id": app_id
                }

                result_string = requests.post(url=URL_SEND_LOGIN_OTP, json=payload)
                if result_string.status_code != 200:
                    return [ERROR, result_string.text]

                result = json.loads(result_string.text)
                request_key = result["request_key"]

                return [SUCCESS, request_key]

            except Exception as e:
                return [ERROR, e]


        def generate_totp(secret):
            try:
                generated_totp = pyotp.TOTP(secret).now()
                return [SUCCESS, generated_totp]

            except Exception as e:
                return [ERROR, e]


        def verify_totp(request_key, totp):
            try:
                payload = {
                    "request_key": request_key,
                    "otp": totp
                }

                result_string = requests.post(url=URL_VERIFY_TOTP, json=payload)
                if result_string.status_code != 200:
                    return [ERROR, result_string.text]

                result = json.loads(result_string.text)
                request_key = result["request_key"]

                return [SUCCESS, request_key]

            except Exception as e:
                return [ERROR, e]


        def verify_PIN(request_key, pin):
            try:
                payload = {
                    "request_key": request_key,
                    "identity_type": "pin",
                    "identifier": pin
                }

                result_string = requests.post(url=URL_VERIFY_PIN, json=payload)
                if result_string.status_code != 200:
                    return [ERROR, result_string.text]

                result = json.loads(result_string.text)
                access_token = result["data"]["access_token"]

                return [SUCCESS, access_token]

            except Exception as e:
                return [ERROR, e]


        def token(fy_id, app_id, redirect_uri, app_type, access_token):
            try:
                payload = {
                    "fyers_id": fy_id,
                    "app_id": app_id,
                    "redirect_uri": redirect_uri,
                    "appType": app_type,
                    "code_challenge": "",
                    "state": "sample_state",
                    "scope": "",
                    "nonce": "",
                    "response_type": "code",
                    "create_cookie": True
                }
                headers={'Authorization': f'Bearer {access_token}'}

                result_string = requests.post(
                    url=URL_TOKEN, json=payload, headers=headers
                )

                if result_string.status_code != 308:
                    return [ERROR, result_string.text]

                result = json.loads(result_string.text)
                url = result["Url"]
                auth_code = parse.parse_qs(parse.urlparse(url).query)['auth_code'][0]

                return [SUCCESS, auth_code]

            except Exception as e:
                return [ERROR, e]


        def validate_authcode(app_id_hash, auth_code):
            try:
                payload = {
                    "grant_type": "authorization_code",
                    "appIdHash": app_id_hash,
                    "code": auth_code,
                }

                result_string = requests.post(url=URL_VALIDATE_AUTH_CODE, json=payload)
                if result_string.status_code != 200:
                    return [ERROR, result_string.text]

                result = json.loads(result_string.text)
                access_token = result["access_token"]

                return [SUCCESS, access_token]

            except Exception as e:
                return [ERROR, e]


        # Step 1 - Retrieve request_key from send_login_otp API
        send_otp_result = send_login_otp(fy_id=FY_ID, app_id=APP_ID_TYPE)
        if send_otp_result[0] != SUCCESS:
            print(f"send_login_otp failure - {send_otp_result[1]}")
            sys.exit()
        else:
            print("send_login_otp success")

        # Step 2 - Generate totp
        generate_totp_result = generate_totp(secret=TOTP_KEY)
        if generate_totp_result[0] != SUCCESS:
            print(f"generate_totp failure - {generate_totp_result[1]}")
            sys.exit()
        else:
            print("generate_totp success")

        # Step 3 - Verify totp and get request key from verify_otp API
        request_key = send_otp_result[1]
        totp = generate_totp_result[1]
        verify_totp_result = verify_totp(request_key=request_key, totp=totp)
        if verify_totp_result[0] != SUCCESS:
            print(f"verify_totp_result failure - {verify_totp_result[1]}")
            sys.exit()
        else:
            print("verify_totp_result success")

        # Step 4 - Verify pin and send back access token
        request_key_2 = verify_totp_result[1]
        verify_pin_result = verify_PIN(request_key=request_key_2, pin=PIN)
        if verify_pin_result[0] != SUCCESS:
            print(f"verify_pin_result failure - {verify_pin_result[1]}")
            sys.exit()
        else:
            print("verify_pin_result success")

        # Step 5 - Get auth code for API V2 App from trade access token
        token_result = token(
            fy_id=FY_ID, app_id=APP_ID, redirect_uri=REDIRECT_URI, app_type=APP_TYPE,
            access_token=verify_pin_result[1]
        )
        if token_result[0] != SUCCESS:
            print(f"token_result failure - {token_result[1]}")
            sys.exit()
        else:
            print("token_result success")

        # Step 6 - Get API V2 access token from validating auth code
        auth_code = token_result[1]
        validate_authcode_result = validate_authcode(
            app_id_hash=APP_ID_HASH, auth_code=auth_code
        )
        if token_result[0] != SUCCESS:
            print(f"validate_authcode failure - {validate_authcode_result[1]}")
            sys.exit()
        else:
            print("validate_authcode success")

        #access_token = APP_ID + "-" + APP_TYPE + ":" + validate_authcode_result[1]
        access_token =  validate_authcode_result[1]
        final_access_token = access_token
        return final_access_token


if __name__ == "__main__":
  access_token = main()  # Call main and store the return value
  print(access_token)  # Now print the access token outside the function

	
def my_code_60():
	india_timezone = pytz.timezone('Asia/Kolkata')
	global access_token
	now = dt.datetime.now(india_timezone)
	today = dt.datetime.now(india_timezone)
	# Get the current date and time in the India/Kolkata timezone
	file_access_token = "access_token.txt"
	year = now.year
	month=now.month
	day=now.day


	today_9_20 = datetime.datetime(year=year, month=month, day=day, hour=9, minute=20)
	today_9_15 = datetime.datetime(year=year, month=month, day=day, hour=9, minute=15)
	desired_date = now.date()
	today_date = desired_date

	client_id = "PCNUNWNEIB-100"
	access_token = access_token
	fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")




	# Define symbols
	url = "https://raw.githubusercontent.com/paritoshs241091/ALERT/main/targets.json"
	headers = {"Authorization": "token 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"}

	try:
	   all_symbols = list(json.loads(requests.get(url, headers=headers).text).keys())
	except Exception as e:
	   print("Error fetching symbols:", e)
	   all_symbols = []
	#all_symbols = ["NSE:ADANIENT-EQ","NSE:ADANIPORTS-EQ","NSE:APOLLOHOSP-EQ","NSE:ASIANPAINT-EQ","NSE:AXISBANK-EQ","NSE:BAJAJ-AUTO-EQ","NSE:BAJFINANCE-EQ","NSE:BAJAJFINSV-EQ","NSE:BPCL-EQ","NSE:BHARTIARTL-EQ","NSE:BRITANNIA-EQ","NSE:CIPLA-EQ","NSE:COALINDIA-EQ","NSE:DIVISLAB-EQ","NSE:DRREDDY-EQ","NSE:EICHERMOT-EQ","NSE:GRASIM-EQ","NSE:HCLTECH-EQ","NSE:HDFCBANK-EQ","NSE:HDFCLIFE-EQ","NSE:HEROMOTOCO-EQ","NSE:HINDALCO-EQ","NSE:HINDUNILVR-EQ","NSE:ICICIBANK-EQ","NSE:INDUSINDBK-EQ","NSE:INFY-EQ","NSE:ITC-EQ","NSE:JSWSTEEL-EQ","NSE:KOTAKBANK-EQ","NSE:LT-EQ","NSE:LTIM-EQ","NSE:M&M-EQ","NSE:MARUTI-EQ","NSE:NESTLEIND-EQ","NSE:NTPC-EQ","NSE:ONGC-EQ","NSE:POWERGRID-EQ","NSE:RELIANCE-EQ","NSE:SBILIFE-EQ","NSE:SHRIRAMFIN-EQ","NSE:SBIN-EQ","NSE:SUNPHARMA-EQ","NSE:TCS-EQ","NSE:TATACONSUM-EQ","NSE:TATAMOTORS-EQ","NSE:TATASTEEL-EQ","NSE:TECHM-EQ","NSE:TITAN-EQ","NSE:ULTRACEMCO-EQ","NSE:WIPRO-EQ","NSE:AUBANK-EQ","NSE:BANDHANBNK-EQ","NSE:BANKBARODA-EQ","NSE:PNB-EQ","NSE:IDFCFIRSTB-EQ","NSE:FEDERALBNK-EQ","NSE:FINNIFTY-INDEX","NSE:MIDCPNIFTY-INDEX","NSE:NIFTY50-INDEX","NSE:NIFTYBANK-INDEX"]

	# Set the desired start time to 9:00 AM of the day when you believe 200 candles data or more wud be available to calc. 200 sma
	start_time = now.replace(hour=9, minute=0, second=0, microsecond=0) - dt.timedelta(days=2)

	# Set the desired end time to 11:55 PM of today
	end_time = now
	#end_time = now.replace(hour=23, minute=55, second=0, microsecond=0)

	# Convert the start and end times to epoch time
	epoch_start_time = int(start_time.timestamp())
	epoch_end_time = int(end_time.timestamp())

	# Define symbols
	# Create an empty DataFrame to store the results
	S = pd.DataFrame()
	T = pd.DataFrame()
	U = pd.DataFrame()
	V = pd.DataFrame()
	W = pd.DataFrame()
	X = pd.DataFrame()
	Y = pd.DataFrame()
	Z = pd.DataFrame()
	filtered_ce_today = pd.DataFrame()
	filtered_pe_today = pd.DataFrame()

    cmp_data = {}

	# Loop through symbols
	for symbol in all_symbols:
	  try:

	      data = {
	          "symbol": symbol,
	          "resolution": "1",
	          "date_format": "0",
	          "range_from": epoch_start_time,
	          "range_to": epoch_end_time,
	          "cont_flag": "1"
	      }

	      # Fetch historical data
	      response = fyers.history(data=data)
	      if response['s'] == "ok":
	          # Create DataFrame
	          df = pd.DataFrame(response['candles'], columns=['date', 'open', 'high', 'low', 'close', 'volume'])
	          #print(df)

	          # Convert timestamp to datetime and adjust timezone
	          df['date'] = pd.to_datetime(df['date'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
	          df['date'] = df['date'].dt.tz_localize(None)

	          # Calculate SMAs
	          df['sma_8'] = df['close'].rolling(window=7).mean()
	          df['sma_21'] = df['close'].rolling(window=21).mean()
	          df['sma_100'] = df['close'].rolling(window=100).mean()
	          df['sma_200'] = df['close'].rolling(window=200).mean()
	          df['symbol'] = symbol

	          # Calculate RSI
	          delta = df['close'].diff()
	          u = delta * 0
	          d = u.copy()
	          u[delta > 0] = delta[delta > 0]
	          d[delta < 0] = -delta[delta < 0]
	          u[u.index[13]] = np.mean(u[:14])
	          u = u.drop(u.index[:13])
	          d[d.index[13]] = np.mean(d[:14])
	          d = d.drop(d.index[:13])
	          rs = pd.DataFrame.ewm(u, com=13, adjust=False).mean() / pd.DataFrame.ewm(d, com=13, adjust=False).mean()
	          df['rsi'] = 100 - 100 / (1 + rs)
	          #print(symbol)
	          df_filtered = df.copy()
	          cmp_data[symbol] = float(df['low'].iloc[-1])  # Add to dictionary


	      else:
	          continue

	  except IndexError as e:
	    print(f"{symbol}: {e}.")
	    continue
	return cmp_data
	##########################################

class AlertManager:
    def __init__(self, github_user, github_repo, github_token, email="you@example.com", name="Your Name"):
        self.github_user = github_user
        self.github_repo = github_repo
        self.github_token = github_token
        self.repo_url = f"https://{github_user}:{github_token}@github.com/{github_user}/{github_repo}.git"
        self.email = email
        self.name = name
        self.repo_path = github_repo + "/"
        self.symbols_file = os.path.join(self.repo_path, "symbols.json")
        self.targets_file = os.path.join(self.repo_path, "targets.json")
        
        self._setup_repo()
        self.symbols = self._load_symbols()
        self.targets = self._load_targets()

    # ----------------------- Repo & File Setup -----------------------
    def _setup_repo(self):
        if os.path.exists(self.github_repo):
            os.system(f"cd {self.github_repo} && git pull")
        else:
            os.system(f"git clone {self.repo_url}")

    def _load_symbols(self):
        if not os.path.exists(self.symbols_file):
            print("symbols.json not found. Fetching latest symbols...")
            self.update_symbols()
        with open(self.symbols_file, "r") as f:
            return json.load(f)

    def _load_targets(self):
        if os.path.exists(self.targets_file):
            with open(self.targets_file, "r") as f:
                return json.load(f)
        return {}

    def _save_targets(self):
        with open(self.targets_file, "w") as f:
            json.dump(self.targets, f, indent=4)
        self._commit_and_push("Updated targets.json")

    def _commit_and_push(self, message):
        os.chdir(self.repo_path)
        os.system(f'git config --global user.email "{self.email}"')
        os.system(f'git config --global user.name "{self.name}"')
        os.system("git add targets.json")
        os.system(f'git commit -m "{message}" || echo "No changes to commit"')
        os.system(f"git push {self.repo_url} HEAD:main")
        os.chdir("/content")

    # ----------------------- Symbols Update -----------------------
    def update_symbols(self):
        url = "https://public.fyers.in/sym_details/NSE_CM.csv"
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text), header=None)
            raw_symbols = df[9].dropna().tolist()
            eq_symbols = sorted([s for s in raw_symbols if s.endswith("-EQ")])
            with open(self.symbols_file, "w") as f:
                json.dump(eq_symbols, f, indent=4)
            self.symbols = eq_symbols
            self._commit_and_push("Updated symbols.json")
            print(f"Updated {len(eq_symbols)} symbols in symbols.json")
        else:
            print("Failed to fetch symbols:", response.status_code)

    # ----------------------- Target Management -----------------------
    def add_target(self, pattern, price, comment=""):
        matched = [s for s in self.symbols if re.search(f":{pattern}", s, re.IGNORECASE)]
        if not matched:
            print(f"No stock matched for pattern: {pattern}")
            return

        for symbol in matched:
            if symbol not in self.targets:
                self.targets[symbol] = []
            existing = [t for t in self.targets[symbol] if t["price"] == price and t.get("comment", "") == comment]

            print(f"\nStock: {symbol}")
            if not existing:
                self.targets[symbol].append({"price": price, "comment": comment, "triggered": False})
                print(f"Added {price} ({comment})")
            else:
                print(f"Target {price} ({comment}) already exists.")

            updated = [(t["price"], t["comment"]) for t in self.targets[symbol]]
            print(f"Updated targets: {updated}")

        self._save_targets()

    def remove_target(self, pattern, price):
        matched = [s for s in self.targets.keys() if re.search(f":{pattern}", s, re.IGNORECASE)]
        if not matched:
            print(f"No stock matched for pattern: {pattern}")
            return

        for symbol in matched:
            old_count = len(self.targets[symbol])
            self.targets[symbol] = [t for t in self.targets[symbol] if t["price"] != price]

            if len(self.targets[symbol]) < old_count:
                print(f"Removed all entries with price {price} from {symbol}")
            else:
                print(f"No target with price {price} found in {symbol}")

            if not self.targets[symbol]:
                del self.targets[symbol]
                print(f"Removed {symbol} completely as no targets left.")

        self._save_targets()

    def show_targets(self, pattern=None):
        matched = self.targets if not pattern else {
            s: v for s, v in self.targets.items()
            if re.search(f":{pattern}", s, re.IGNORECASE)
        }
        print(json.dumps(matched, indent=4))

    # ----------------------- Alerts Check (External CMP) -----------------------
    def check_alerts_with_cmp(self, cmp_data, tolerance=0.08):
        """
        Automatically removes targets if hit.
        """
        print("\n--- Checking Alerts with External CMP ---")
        updated_targets = {}
        alert_rows = []  # Alerts ke liye list
        current_date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for symbol, price_list in self.targets.items():
            if symbol not in cmp_data:
                print(f"CMP not provided for {symbol}, skipping.")
                updated_targets[symbol] = price_list
                continue

            cmp = cmp_data[symbol]
            remaining_prices = []
            #for target in price_list:
            #    diff = abs((cmp - target["price"]) / target["price"]) * 100
            #    if diff <= tolerance:
            #        print(f"ALERT: {symbol} [{target.get('comment', '').upper()}] hit target {target['price']} (CMP={cmp})")
            #    else:
            #        remaining_prices.append(target)

            for target in price_list:
                diff = abs((cmp - target["price"]) / target["price"]) * 100
                if diff <= tolerance:
                    comment = target.get("comment", "").lower()


                    buy_symbol = symbol if "buy" in comment else ""
                    sell_symbol = symbol if "sell" in comment else ""
                    other_symbol = symbol if (buy_symbol == "" and sell_symbol == "") else ""
                    alert_rows.append([current_date, buy_symbol, sell_symbol, other_symbol])

                else:
                    remaining_prices.append(target)

            if remaining_prices:
                updated_targets[symbol] = remaining_prices

        self.targets = updated_targets
        self._save_targets()

        # Agar alerts aaye hain to DataFrame banao
        if not alert_rows:
            print("No alerts triggered this minute.")
            return  # Agar koi alert nahi hai to function yahin stop
        df = pd.DataFrame(alert_rows, columns=["date", "buy", "sell", "others"])
        self._send_alert_image(df)

    def _send_alert_image(self, df):
        # DataFrame ko table me convert karo
        table = tabulate(df, headers='keys', tablefmt='grid')
    
        fig, ax = plt.subplots()
        ax.axis('off')
        ax.text(
            0, 0.95, table, va='top', family='monospace',
            bbox=dict(facecolor='#ffd9df', alpha=0.5)
        )
    
        filename = "999_trades_image.png"
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close()
    
        # Telegram pe bhejo
        files = {'photo': open(filename, 'rb')}
        resp = requests.post(
            'https://api.telegram.org/bot6798563481:AAGJ7INwt7HxawkhxdgK8FTklJF_VRA5LsU/sendPhoto?chat_id=-1002189329732',
            files=files
        )
        print("Telegram response:", resp.status_code)

manager = AlertManager(
    github_user="paritoshs241091",
    github_repo="ALERT",
    github_token="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",
    email="you@example.com",
    name="Your Name"
)
    
    # Add targets
    #manager.add_target("RELIANCE", 1474, "buy")
    #manager.add_target("tcs", 3190, "hehe")
    #manager.add_target("WSTCSTPAPR", 558, "sell")
    
    #manager.remove_target("RELIANCE", 2502)
    
    #manager.show_targets("RELIANCE")
    #manager.show_targets()
    
    # Check alerts using CMP data
    #cmp_data = {"NSE:RELIANCE-EQ": 2501}
    #manager.check_alerts_with_cmp(cmp_data)

cmp_data = my_code_60()
manager.check_alerts_with_cmp(cmp_data)  # CMP ke saath check karo
def execute_script():
    while True:
        current_time = datetime.datetime.now()
        current_minute = current_time.minute
        current_second = current_time.second
	
        if (current_second == 0):
            print("start time:", datetime.datetime.now().strftime("%H:%M:%S"))
            cmp_data = my_code_60()
            manager.check_alerts_with_cmp(cmp_data)  # CMP ke saath check karo
            print("end time:", datetime.datetime.now().strftime("%H:%M:%S"))
            time.sleep(30)
        time.sleep(1)

# Call the function to start printing
execute_script()
