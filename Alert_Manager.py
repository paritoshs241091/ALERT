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
import re
from io import StringIO


def main():
    india_timezone = pytz.timezone('Asia/Kolkata')
    today = dt.datetime.now(india_timezone)
    file_access_token = "access_token.txt"
    if os.path.exists(file_access_token):
        os.remove(file_access_token)

    FY_ID = "XP28064"
    APP_ID_TYPE = "2"
    TOTP_KEY = "7BM4WGDX53VBXSK3RP2Q6OOBFLGRJUGB"
    PIN = "4411"
    APP_ID = "PCNUNWNEIB"
    REDIRECT_URI = "https://myapi.fyers.in/dashboard"
    APP_TYPE = "100"
    APP_ID_HASH = "6ea7fc08111a642192457b88ba18950b52a75bc6f231d47661b8cbb4bc1844bd"

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
            payload = {"fy_id": fy_id, "app_id": app_id}
            result_string = requests.post(url=URL_SEND_LOGIN_OTP, json=payload)
            if result_string.status_code != 200:
                return [ERROR, result_string.text]
            result = json.loads(result_string.text)
            return [SUCCESS, result["request_key"]]
        except Exception as e:
            return [ERROR, e]

    def generate_totp(secret):
        try:
            return [SUCCESS, pyotp.TOTP(secret).now()]
        except Exception as e:
            return [ERROR, e]

    def verify_totp(request_key, totp):
        try:
            payload = {"request_key": request_key, "otp": totp}
            result_string = requests.post(url=URL_VERIFY_TOTP, json=payload)
            if result_string.status_code != 200:
                return [ERROR, result_string.text]
            result = json.loads(result_string.text)
            return [SUCCESS, result["request_key"]]
        except Exception as e:
            return [ERROR, e]

    def verify_PIN(request_key, pin):
        try:
            payload = {"request_key": request_key, "identity_type": "pin", "identifier": pin}
            result_string = requests.post(url=URL_VERIFY_PIN, json=payload)
            if result_string.status_code != 200:
                return [ERROR, result_string.text]
            result = json.loads(result_string.text)
            return [SUCCESS, result["data"]["access_token"]]
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
            headers = {'Authorization': f'Bearer {access_token}'}
            result_string = requests.post(url=URL_TOKEN, json=payload, headers=headers)
            if result_string.status_code != 308:
                return [ERROR, result_string.text]
            result = json.loads(result_string.text)
            auth_code = parse.parse_qs(parse.urlparse(result["Url"]).query)['auth_code'][0]
            return [SUCCESS, auth_code]
        except Exception as e:
            return [ERROR, e]

    def validate_authcode(app_id_hash, auth_code):
        try:
            payload = {"grant_type": "authorization_code", "appIdHash": app_id_hash, "code": auth_code}
            result_string = requests.post(url=URL_VALIDATE_AUTH_CODE, json=payload)
            if result_string.status_code != 200:
                return [ERROR, result_string.text]
            result = json.loads(result_string.text)
            return [SUCCESS, result["access_token"]]
        except Exception as e:
            return [ERROR, e]

    send_otp_result = send_login_otp(fy_id=FY_ID, app_id=APP_ID_TYPE)
    if send_otp_result[0] != SUCCESS:
        print(f"send_login_otp failure - {send_otp_result[1]}")
        sys.exit()
    print("send_login_otp success")

    generate_totp_result = generate_totp(secret=TOTP_KEY)
    if generate_totp_result[0] != SUCCESS:
        print(f"generate_totp failure - {generate_totp_result[1]}")
        sys.exit()
    print("generate_totp success")

    verify_totp_result = verify_totp(request_key=send_otp_result[1], totp=generate_totp_result[1])
    if verify_totp_result[0] != SUCCESS:
        print(f"verify_totp_result failure - {verify_totp_result[1]}")
        sys.exit()
    print("verify_totp_result success")

    verify_pin_result = verify_PIN(request_key=verify_totp_result[1], pin=PIN)
    if verify_pin_result[0] != SUCCESS:
        print(f"verify_pin_result failure - {verify_pin_result[1]}")
        sys.exit()
    print("verify_pin_result success")

    token_result = token(
        fy_id=FY_ID, app_id=APP_ID, redirect_uri=REDIRECT_URI,
        app_type=APP_TYPE, access_token=verify_pin_result[1]
    )
    if token_result[0] != SUCCESS:
        print(f"token_result failure - {token_result[1]}")
        sys.exit()
    print("token_result success")

    validate_authcode_result = validate_authcode(app_id_hash=APP_ID_HASH, auth_code=token_result[1])
    if token_result[0] != SUCCESS:
        print(f"validate_authcode failure - {validate_authcode_result[1]}")
        sys.exit()
    print("validate_authcode success")

    return validate_authcode_result[1]


if __name__ == "__main__":
    access_token = main()
    print(access_token)


def my_code_60():
    india_timezone = pytz.timezone('Asia/Kolkata')
    global access_token
    now = dt.datetime.now(india_timezone)
    file_access_token = "access_token.txt"
    client_id = "PCNUNWNEIB-100"
    fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")

    # Define symbols
    url = "https://raw.githubusercontent.com/paritoshs241091/ALERT/main/targets.json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Will raise HTTPError for bad status
        all_symbols = list(json.loads(response.text).keys())
    except Exception as e:
        print("Error fetching symbols:", e)
        all_symbols = []

    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0) - dt.timedelta(days=2)
    end_time = now
    epoch_start_time = int(start_time.timestamp())
    epoch_end_time = int(end_time.timestamp())

    cmp_data = {}
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
            response = fyers.history(data=data)
            if response['s'] == "ok":
                df = pd.DataFrame(response['candles'], columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                df['date'] = pd.to_datetime(df['date'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
                df['date'] = df['date'].dt.tz_localize(None)
                cmp_data[symbol] = float(df['low'].iloc[-1])
                print(symbol)
                print(df['low'].iloc[-1])
            else:
                continue
        except IndexError as e:
            print(f"{symbol}: {e}.")
            continue
    return cmp_data


class AlertManager:
    def __init__(self, github_user, github_repo, github_token=None, email="you@example.com", name="Your Name"):
        self.github_user = github_user
        self.github_repo = github_repo
        self.github_token = github_token.strip() or ""
        if self.github_token:
            self.repo_url = f"https://{github_user}:{self.github_token}@github.com/{github_user}/{github_repo}.git"
        else:
            self.repo_url = f"https://github.com/{github_user}/{github_repo}.git"
        self.email = email
        self.name = name
        self.repo_path = github_repo + "/"
        self.symbols_file = os.path.join(self.repo_path, "symbols.json")
        self.targets_file = os.path.join(self.repo_path, "targets.json")
        self._setup_repo()
        self.symbols = self._load_symbols()
        self.targets = self._load_targets()

    def _setup_repo(self):
        if os.path.exists(self.github_repo):
            os.system(f"cd {self.github_repo} && git fetch origin && git rebase origin/main || true")
        else:
            os.system(f"git clone {self.repo_url}")
        os.system(f"cd {self.github_repo} && git remote set-url origin {self.repo_url}")

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
        # Step 1: Always pull latest before saving
        os.chdir(self.repo_path)
        os.system("git pull origin main --rebase --autostash || true")
        os.chdir("/content")
        # Step 2: Merge current targets with latest targets.json
        if os.path.exists(self.targets_file):
            with open(self.targets_file, "r") as f:
                latest_targets = json.load(f)
            # Merge data (avoid overwriting)
            for symbol, target_list in self.targets.items():
                if symbol not in latest_targets:
                    latest_targets[symbol] = target_list
                else:
                    for t in target_list:
                        if t not in latest_targets[symbol]:
                            latest_targets[symbol].append(t)
            self.targets = latest_targets


    def _commit_and_push(self, message):
        os.chdir(self.repo_path)
        os.system(f'git config --global user.email "{self.email}"')
        os.system(f'git config --global user.name "{self.name}"')
        os.system("git pull origin main --rebase --autostash || true")
        os.system("git add targets.json")
        os.system(f'git commit -m "{message}" || echo "No changes to commit"')
        os.system("git push origin main")
        os.chdir("/content")

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

    def check_alerts_with_cmp(self, cmp_data, tolerance=0.08):
        print("\n--- Checking Alerts with External CMP ---")
        updated_targets = {}
        alert_rows = []
        current_date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for symbol, price_list in self.targets.items():
            if symbol not in cmp_data:
                print(f"CMP not provided for {symbol}, skipping.")
                updated_targets[symbol] = price_list
                continue

            cmp = cmp_data[symbol]
            remaining_prices = []
            for target in price_list:
                diff = abs((cmp - target["price"]) / target["price"]) * 100
                if diff <= tolerance:
                    print(f"Target hit & removed: {symbol} @ {target['price']}")
                    comment = target.get("comment", "").lower()
                    buy_symbol = symbol if "buy" in comment else ""
                    sell_symbol = symbol if "sell" in comment else ""
                    other_symbol = symbol if (buy_symbol == "" and sell_symbol == "") else ""
                    alert_rows.append([current_date, buy_symbol, sell_symbol, other_symbol])
                    print("Remaining Targets after check:", json.dumps(updated_targets, indent=4))
                else:
                    remaining_prices.append(target)
            if remaining_prices:
                updated_targets[symbol] = remaining_prices

        self.targets = updated_targets
        self._save_targets()

        if not alert_rows:
            print("No alerts triggered this minute.")
            return

        df = pd.DataFrame(alert_rows, columns=["date", "buy", "sell", "others"])
        self._send_alert_image(df)

    def _send_alert_image(self, df):
        table = tabulate(df, headers='keys', tablefmt='grid')
        fig, ax = plt.subplots()
        ax.axis('off')
        ax.text(0, 0.95, table, va='top', family='monospace', bbox=dict(facecolor='#ffd9df', alpha=0.5))
        filename = "999_trades_image.png"
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close()
        files = {'photo': open(filename, 'rb')}
        resp = requests.post(
            'https://api.telegram.org/bot6798563481:AAGJ7INwt7HxawkhxdgK8FTklJF_VRA5LsU/sendPhoto?chat_id=-1002189329732',
            files=files
        )
        print("Telegram response:", resp.status_code)

token = os.getenv("GITHUB_TOKEN")
manager = AlertManager(
    github_user="paritoshs241091",
    github_repo="ALERT",
    github_token= token,
    email="you@example.com",
    name="Your Name"
)

cmp_data = my_code_60()
manager.check_alerts_with_cmp(cmp_data)


def execute_script():
    while True:
        current_time = datetime.datetime.now()
        current_second = current_time.second
        if current_second == 0:
            print("start time:", datetime.datetime.now().strftime("%H:%M:%S"))
            cmp_data = my_code_60()
            manager.check_alerts_with_cmp(cmp_data)
            print("end time:", datetime.datetime.now().strftime("%H:%M:%S"))
            time.sleep(30)
        time.sleep(1)


execute_script()
