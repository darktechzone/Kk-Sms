import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from typing import Optional, Dict, Any, List

# ─── CONFIG ──────────────────────────────────────────────────────────────
BASE_URL = "https://konektapremium.net"
USERNAME = os.environ.get("KONEKT_USER", "Slaeem777")
PASSWORD = os.environ.get("KONEKT_PASS", "Slaeem1234")

# ─── CLIENT ──────────────────────────────────────────────────────────────
class KonektClient:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
        self.sesskey = None

    def login(self) -> bool:
        print("[*] Logging in...")
        login_page_url = f"{BASE_URL}/sign-in"

        try:
            resp = self.session.get(login_page_url, timeout=15)
            if resp.status_code != 200:
                print(f"Failed to load login page: {resp.status_code}")
                return False

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Captcha
            captcha_text = None
            for selector in ['#captchaQuestion', '.captcha-question', 'label[for="capt"]']:
                elem = soup.select_one(selector)
                if elem:
                    captcha_text = elem.get_text(strip=True)
                    break
            if not captcha_text:
                for elem in soup.find_all(['span', 'div', 'label']):
                    txt = elem.get_text(strip=True)
                    if re.search(r'what\s*is\s*\d+\s*[+\-*/]\s*\d+', txt, re.I):
                        captcha_text = txt
                        break
            if not captcha_text:
                print("Captcha not found")
                return False

            try:
                captcha_answer = self._solve_captcha(captcha_text)
            except Exception as e:
                print(f"Captcha solve error: {e}")
                return False

            # Find form
            form = soup.find('form')
            if not form:
                print("No form found")
                return False

            action = form.get('action', '')
            if not action:
                action = login_page_url
            elif not action.startswith('http'):
                if action.startswith('/'):
                    action = f"{BASE_URL}{action}"
                else:
                    action = f"{BASE_URL}/{action}"

            # Extract fields
            payload = {}
            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    payload[name] = value

            username_field = None
            password_field = None
            captcha_field = None
            for field in ['username', 'user', 'email']:
                if field in payload:
                    username_field = field
                    break
            for field in ['password', 'pass', 'pwd']:
                if field in payload:
                    password_field = field
                    break
            for field in ['capt', 'captcha']:
                if field in payload:
                    captcha_field = field
                    break

            if not username_field or not password_field:
                print("No username/password fields")
                return False

            payload[username_field] = USERNAME
            payload[password_field] = PASSWORD
            if captcha_field:
                payload[captcha_field] = str(captcha_answer)

            login_headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": login_page_url,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            resp2 = self.session.post(action, data=payload, headers=login_headers, allow_redirects=True)

            if "dashboard" in resp2.url.lower() or "agent" in resp2.url.lower():
                print("Login successful")
                self.logged_in = True
                self._extract_sesskey()
                return True

            print("Login failed")
            return False

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def _solve_captcha(self, question_text: str) -> int:
        clean = re.sub(r'[^0-9+\-*/=]', ' ', question_text).strip()
        match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', clean)
        if not match:
            raise ValueError(f"Could not parse captcha: {question_text}")
        a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
        if op == '+': return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '/': return a // b
        raise ValueError(f"Unknown operator: {op}")

    def _extract_sesskey(self):
        try:
            resp = self.session.get(f"{BASE_URL}/agent/SMSCDRStats", timeout=10)
            if resp.status_code == 200:
                match = re.search(r'sesskey=([^&\s"\']+)', resp.text)
                if match:
                    self.sesskey = match.group(1)
                    print(f"Found sesskey: {self.sesskey}")
                    return
        except Exception:
            pass
        if 'sesskey' in self.session.cookies:
            self.sesskey = self.session.cookies['sesskey']
            print(f"Found sesskey from cookies: {self.sesskey}")

    def _ensure_login(self):
        if not self.logged_in:
            return self.login()
        return True

    def _api_request(self, method: str, endpoint: str, params: dict = None, referer: str = None) -> Optional[Dict]:
        if not self._ensure_login():
            return None

        url = f"{BASE_URL}{endpoint}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer or f"{BASE_URL}/agent/MySMSNumbers",
        }

        try:
            resp = self.session.request(method, url, params=params, headers=headers, timeout=15)
            if resp.status_code == 401:
                self.logged_in = False
                print("Session expired. Re-login required.")
                return None
            if resp.status_code != 200:
                print(f"API request failed: {resp.status_code}")
                return None
            return resp.json()
        except Exception as e:
            print(f"API request error: {e}")
            return None

    def get_numbers(self) -> List[str]:
        endpoint = "/agent/res/data_smsnumbers.php"
        params = {
            "frange": "",
            "fclient": "",
            "fnumber": "",
            "sEcho": "2",
            "iColumns": "8",
            "sColumns": ",,,,,,,",
            "iDisplayStart": "0",
            "iDisplayLength": "200",
            "mDataProp_0": "0",
            "sSearch_0": "",
            "bRegex_0": "false",
            "bSearchable_0": "true",
            "bSortable_0": "false",
            "mDataProp_1": "1",
            "sSearch_1": "",
            "bRegex_1": "false",
            "bSearchable_1": "true",
            "bSortable_1": "true",
            "mDataProp_2": "2",
            "sSearch_2": "",
            "bRegex_2": "false",
            "bSearchable_2": "true",
            "bSortable_2": "true",
            "mDataProp_3": "3",
            "sSearch_3": "",
            "bRegex_3": "false",
            "bSearchable_3": "true",
            "bSortable_3": "true",
            "mDataProp_4": "4",
            "sSearch_4": "",
            "bRegex_4": "false",
            "bSearchable_4": "true",
            "bSortable_4": "true",
            "mDataProp_5": "5",
            "sSearch_5": "",
            "bRegex_5": "false",
            "bSearchable_5": "true",
            "bSortable_5": "true",
            "mDataProp_6": "6",
            "sSearch_6": "",
            "bRegex_6": "false",
            "bSearchable_6": "true",
            "bSortable_6": "true",
            "mDataProp_7": "7",
            "sSearch_7": "",
            "bRegex_7": "false",
            "bSearchable_7": "true",
            "bSortable_7": "false",
            "sSearch": "",
            "bRegex": "false",
            "iSortCol_0": "0",
            "sSortDir_0": "asc",
            "iSortingCols": "1",
            "_": str(int(time.time() * 1000))
        }

        data = self._api_request("GET", endpoint, params=params, referer=f"{BASE_URL}/agent/MySMSNumbers")
        if data and isinstance(data, dict):
            rows = data.get('aaData', [])
            numbers = [row[3].strip() for row in rows if isinstance(row, list) and len(row) > 3 and row[3].strip()]
            return numbers
        return []

    def get_sms(self, limit: int = 50) -> List[Dict]:
        endpoint = "/agent/res/data_smscdr.php"
        today = time.strftime("%Y-%m-%d")
        params = {
            "fdate1": f"{today} 00:00:00",
            "fdate2": f"{today} 23:59:59",
            "frange": "",
            "fclient": "",
            "fnum": "",
            "fcli": "",
            "fgdate": "",
            "fgmonth": "",
            "fgrange": "",
            "fgclient": "",
            "fgnumber": "",
            "fgcli": "",
            "fg": "0",
            "sesskey": self.sesskey or "",
            "sEcho": "2",
            "iColumns": "9",
            "sColumns": ",,,,,,,,",
            "iDisplayStart": "0",
            "iDisplayLength": str(limit),
            "mDataProp_0": "0",
            "sSearch_0": "",
            "bRegex_0": "false",
            "bSearchable_0": "true",
            "bSortable_0": "true",
            "mDataProp_1": "1",
            "sSearch_1": "",
            "bRegex_1": "false",
            "bSearchable_1": "true",
            "bSortable_1": "true",
            "mDataProp_2": "2",
            "sSearch_2": "",
            "bRegex_2": "false",
            "bSearchable_2": "true",
            "bSortable_2": "true",
            "mDataProp_3": "3",
            "sSearch_3": "",
            "bRegex_3": "false",
            "bSearchable_3": "true",
            "bSortable_3": "true",
            "mDataProp_4": "4",
            "sSearch_4": "",
            "bRegex_4": "false",
            "bSearchable_4": "true",
            "bSortable_4": "true",
            "mDataProp_5": "5",
            "sSearch_5": "",
            "bRegex_5": "false",
            "bSearchable_5": "true",
            "bSortable_5": "true",
            "mDataProp_6": "6",
            "sSearch_6": "",
            "bRegex_6": "false",
            "bSearchable_6": "true",
            "bSortable_6": "true",
            "mDataProp_7": "7",
            "sSearch_7": "",
            "bRegex_7": "false",
            "bSearchable_7": "true",
            "bSortable_7": "true",
            "mDataProp_8": "8",
            "sSearch_8": "",
            "bRegex_8": "false",
            "bSearchable_8": "true",
            "bSortable_8": "false",
            "sSearch": "",
            "bRegex": "false",
            "iSortCol_0": "0",
            "sSortDir_0": "desc",
            "iSortingCols": "1",
            "_": str(int(time.time() * 1000))
        }

        data = self._api_request("GET", endpoint, params=params, referer=f"{BASE_URL}/agent/SMSCDRStats")
        if data and isinstance(data, dict):
            rows = data.get('aaData', [])
            sms_list = []
            for row in rows:
                if not isinstance(row, list) or len(row) < 6:
                    continue
                number = row[2].strip() if row[2] else ''
                message = row[5].strip() if row[5] else ''
                timestamp = row[0].strip() if row[0] else ''
                if not number or not message:
                    continue
                if re.search(r'\*{4,}', message):
                    # masked message, skip or mark
                    continue
                otp = self._extract_otp(message)
                sms_list.append({
                    "number": number,
                    "message": message[:300],
                    "timestamp": timestamp,
                    "otp": otp
                })
            return sms_list
        return []

    def _extract_otp(self, message: str) -> Optional[str]:
        if not message:
            return None
        patterns = [
            r'#\s*(\d{4,8})',
            r'(?:code|otp|verification\s*code|confirm\s*code|auth\s*code)\s*(?:is|:)?\s*(\d{4,8})',
            r'your\s+whatsapp\s+code\s*:\s*(\d{4,8})',
            r'(?<![0-9+])(\d{4,8})(?![0-9])',
            r'(\d{3,4})[\- ](\d{3,4})',
        ]
        for pat in patterns:
            m = re.search(pat, message, re.I)
            if m:
                if len(m.groups()) == 2:
                    combined = m.group(1) + m.group(2)
                    if 4 <= len(combined) <= 8:
                        return combined
                else:
                    val = m.group(1)
                    if re.match(r'^(584|1|7|8|9)', val) and len(val) >= 10:
                        continue
                    return val
        return None

# ─── GLOBAL CLIENT INSTANCE ────────────────────────────────────────────
client = KonektClient()

# ─── FLASK APP ──────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "service": "Konekt Panel API",
        "endpoints": {
            "/numbers": "GET – returns list of phone numbers",
            "/sms": "GET – returns list of SMS with OTPs (optional param ?limit=50)"
        }
    })

@app.route('/numbers')
def get_numbers():
    try:
        numbers = client.get_numbers()
        return jsonify({"success": True, "count": len(numbers), "numbers": numbers})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/sms')
def get_sms():
    try:
        limit = request.args.get('limit', 50, type=int)
        sms_list = client.get_sms(limit=limit)
        return jsonify({"success": True, "count": len(sms_list), "sms": sms_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─── VERCEL HARNESS ────────────────────────────────────────────────────
# Vercel expects a variable named 'app' as the WSGI callable.
# We already have 'app' from Flask.

# ─── DEVELOPMENT SERVER ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
