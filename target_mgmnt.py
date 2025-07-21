import json
import os
import re
import requests
import pandas as pd
from io import StringIO

class AlertManager:
    def __init__(self, github_user, github_repo, github_token, email="you@example.com", name="Your Name"):
        self.github_user = github_user
        self.github_repo = github_repo
        self.github_token = github_token
        self.repo_url = f"https://{self.github_user}:{self.github_token}@github.com/{self.github_user}/{self.github_repo}.git"
        self.email = email
        self.name = name
        self.repo_path = github_repo + "/"
        self.symbols_file = os.path.join(self.repo_path, "symbols.json")
        self.targets_file = os.path.join(self.repo_path, "targets.json")
        
        self._setup_repo()
        self.symbols = self._load_symbols()
        self.targets = self._load_targets()

    # ----------------------- Repo Setup -----------------------
    def _setup_repo(self):
        if os.path.exists(self.github_repo):
            os.system(f"cd {self.github_repo} && git pull origin main")
        else:
            os.system(f"git clone {self.repo_url}")

    def _commit_and_push(self, message):
        os.chdir(self.repo_path)
        os.system(f'git config --global user.email "{self.email}"')
        os.system(f'git config --global user.name "{self.name}"')
        os.system("git add targets.json symbols.json")
        os.system(f'git commit -m "{message}" || echo "No changes to commit"')
        os.system("git pull origin main --rebase || true")
        os.system("git push origin main")
        os.chdir("..")

    # ----------------------- Load/Save -----------------------
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

    # ----------------------- Symbols Update -----------------------
    def update_symbols(self):
        url = "https://public.fyers.in/sym_details/NSE_CM.csv"
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text), header=None)
            raw_symbols = df[9].dropna().tolist()
            #*update1*#eq_symbols = sorted([f"NSE:{s}" for s in raw_symbols if s.endswith("-EQ")])
            eq_symbols = sorted([f"NSE:{s}" for s in raw_symbols if s.endswith("-EQ") or s.endswith("-INDEX")])
            with open(self.symbols_file, "w") as f:
                json.dump(eq_symbols, f, indent=4)
            self.symbols = eq_symbols
            self._commit_and_push("Updated symbols.json")
            print(f"Updated {len(eq_symbols)} symbols in symbols.json")
        else:
            print("Failed to fetch symbols:", response.status_code)

    # ----------------------- Target Management -----------------------
    def add_target(self, pattern, price, comment=""):
        # Find full NSE symbol name from pattern
        #*update2*#matched = [s for s in self.symbols if re.search(pattern, s, re.IGNORECASE)]
        matched = [s for s in self.symbols if re.search(rf"NSE:{pattern}-EQ$", s, re.IGNORECASE) or re.search(rf"NSE:{pattern}-INDEX$", s, re.IGNORECASE)]
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
        matched = [s for s in self.targets.keys() if re.search(pattern, s, re.IGNORECASE)]
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
            if re.search(pattern, s, re.IGNORECASE)
        }
        print(json.dumps(matched, indent=4))

