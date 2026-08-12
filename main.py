import os
import re
import time
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List

# ─── COUNTRY & FLAG MAPPING ──────────────────────────────────────────
# Simple mapping based on phone prefixes (works for most numbers)
COUNTRY_CODES = {
    "1": {"name": "USA/Canada", "flag": "🇺🇸"},
    "44": {"name": "UK", "flag": "🇬🇧"},
    "91": {"name": "India", "flag": "🇮🇳"},
    "92": {"name": "Pakistan", "flag": "🇵🇰"},
    "93": {"name": "Afghanistan", "flag": "🇦🇫"},
    "94": {"name": "Sri Lanka", "flag": "🇱🇰"},
    "95": {"name": "Myanmar", "flag": "🇲🇲"},
    "98": {"name": "Iran", "flag": "🇮🇷"},
    "211": {"name": "South Sudan", "flag": "🇸🇸"},
    "212": {"name": "Morocco", "flag": "🇲🇦"},
    "213": {"name": "Algeria", "flag": "🇩🇿"},
    "216": {"name": "Tunisia", "flag": "🇹🇳"},
    "218": {"name": "Libya", "flag": "🇱🇾"},
    "220": {"name": "Gambia", "flag": "🇬🇲"},
    "221": {"name": "Senegal", "flag": "🇸🇳"},
    "222": {"name": "Mauritania", "flag": "🇲🇷"},
    "223": {"name": "Mali", "flag": "🇲🇱"},
    "224": {"name": "Guinea", "flag": "🇬🇳"},
    "225": {"name": "Ivory Coast", "flag": "🇨🇮"},
    "226": {"name": "Burkina Faso", "flag": "🇧🇫"},
    "227": {"name": "Niger", "flag": "🇳🇪"},
    "228": {"name": "Togo", "flag": "🇹🇬"},
    "229": {"name": "Benin", "flag": "🇧🇯"},
    "230": {"name": "Mauritius", "flag": "🇲🇺"},
    "231": {"name": "Liberia", "flag": "🇱🇷"},
    "232": {"name": "Sierra Leone", "flag": "🇸🇱"},
    "233": {"name": "Ghana", "flag": "🇬🇭"},
    "234": {"name": "Nigeria", "flag": "🇳🇬"},
    "235": {"name": "Chad", "flag": "🇹🇩"},
    "236": {"name": "Central African Republic", "flag": "🇨🇫"},
    "237": {"name": "Cameroon", "flag": "🇨🇲"},
    "238": {"name": "Cape Verde", "flag": "🇨🇻"},
    "239": {"name": "Sao Tome and Principe", "flag": "🇸🇹"},
    "240": {"name": "Equatorial Guinea", "flag": "🇬🇶"},
    "241": {"name": "Gabon", "flag": "🇬🇦"},
    "242": {"name": "Congo", "flag": "🇨🇬"},
    "243": {"name": "DRC", "flag": "🇨🇩"},
    "244": {"name": "Angola", "flag": "🇦🇴"},
    "245": {"name": "Guinea-Bissau", "flag": "🇬🇼"},
    "246": {"name": "Diego Garcia", "flag": "🇩🇬"},
    "248": {"name": "Seychelles", "flag": "🇸🇨"},
    "249": {"name": "Sudan", "flag": "🇸🇩"},
    "250": {"name": "Rwanda", "flag": "🇷🇼"},
    "251": {"name": "Ethiopia", "flag": "🇪🇹"},
    "252": {"name": "Somalia", "flag": "🇸🇴"},
    "253": {"name": "Djibouti", "flag": "🇩🇯"},
    "254": {"name": "Kenya", "flag": "🇰🇪"},
    "255": {"name": "Tanzania", "flag": "🇹🇿"},
    "256": {"name": "Uganda", "flag": "🇺🇬"},
    "257": {"name": "Burundi", "flag": "🇧🇮"},
    "258": {"name": "Mozambique", "flag": "🇲🇿"},
    "260": {"name": "Zambia", "flag": "🇿🇲"},
    "261": {"name": "Madagascar", "flag": "🇲🇬"},
    "262": {"name": "Reunion", "flag": "🇷🇪"},
    "263": {"name": "Zimbabwe", "flag": "🇿🇼"},
    "264": {"name": "Namibia", "flag": "🇳🇦"},
    "265": {"name": "Malawi", "flag": "🇲🇼"},
    "266": {"name": "Lesotho", "flag": "🇱🇸"},
    "267": {"name": "Botswana", "flag": "🇧🇼"},
    "268": {"name": "Eswatini", "flag": "🇸🇿"},
    "269": {"name": "Comoros", "flag": "🇰🇲"},
    "290": {"name": "St. Helena", "flag": "🇸🇭"},
    "291": {"name": "Eritrea", "flag": "🇪🇷"},
    "297": {"name": "Aruba", "flag": "🇦🇼"},
    "298": {"name": "Faroe Islands", "flag": "🇫🇴"},
    "299": {"name": "Greenland", "flag": "🇬🇱"},
    "350": {"name": "Gibraltar", "flag": "🇬🇮"},
    "351": {"name": "Portugal", "flag": "🇵🇹"},
    "352": {"name": "Luxembourg", "flag": "🇱🇺"},
    "353": {"name": "Ireland", "flag": "🇮🇪"},
    "354": {"name": "Iceland", "flag": "🇮🇸"},
    "355": {"name": "Albania", "flag": "🇦🇱"},
    "356": {"name": "Malta", "flag": "🇲🇹"},
    "357": {"name": "Cyprus", "flag": "🇨🇾"},
    "358": {"name": "Finland", "flag": "🇫🇮"},
    "359": {"name": "Bulgaria", "flag": "🇧🇬"},
    "370": {"name": "Lithuania", "flag": "🇱🇹"},
    "371": {"name": "Latvia", "flag": "🇱🇻"},
    "372": {"name": "Estonia", "flag": "🇪🇪"},
    "373": {"name": "Moldova", "flag": "🇲🇩"},
    "374": {"name": "Armenia", "flag": "🇦🇲"},
    "375": {"name": "Belarus", "flag": "🇧🇾"},
    "376": {"name": "Andorra", "flag": "🇦🇩"},
    "377": {"name": "Monaco", "flag": "🇲🇨"},
    "378": {"name": "San Marino", "flag": "🇸🇲"},
    "379": {"name": "Vatican City", "flag": "🇻🇦"},
    "380": {"name": "Ukraine", "flag": "🇺🇦"},
    "381": {"name": "Serbia", "flag": "🇷🇸"},
    "382": {"name": "Montenegro", "flag": "🇲🇪"},
    "383": {"name": "Kosovo", "flag": "🇽🇰"},
    "385": {"name": "Croatia", "flag": "🇭🇷"},
    "386": {"name": "Slovenia", "flag": "🇸🇮"},
    "387": {"name": "Bosnia and Herzegovina", "flag": "🇧🇦"},
    "389": {"name": "North Macedonia", "flag": "🇲🇰"},
    "420": {"name": "Czech Republic", "flag": "🇨🇿"},
    "421": {"name": "Slovakia", "flag": "🇸🇰"},
    "423": {"name": "Liechtenstein", "flag": "🇱🇮"},
    "500": {"name": "Falkland Islands", "flag": "🇫🇰"},
    "501": {"name": "Belize", "flag": "🇧🇿"},
    "502": {"name": "Guatemala", "flag": "🇬🇹"},
    "503": {"name": "El Salvador", "flag": "🇸🇻"},
    "504": {"name": "Honduras", "flag": "🇭🇳"},
    "505": {"name": "Nicaragua", "flag": "🇳🇮"},
    "506": {"name": "Costa Rica", "flag": "🇨🇷"},
    "507": {"name": "Panama", "flag": "🇵🇦"},
    "508": {"name": "St. Pierre and Miquelon", "flag": "🇵🇲"},
    "509": {"name": "Haiti", "flag": "🇭🇹"},
    "590": {"name": "Guadeloupe", "flag": "🇬🇵"},
    "591": {"name": "Bolivia", "flag": "🇧🇴"},
    "592": {"name": "Guyana", "flag": "🇬🇾"},
    "593": {"name": "Ecuador", "flag": "🇪🇨"},
    "594": {"name": "French Guiana", "flag": "🇬🇫"},
    "595": {"name": "Paraguay", "flag": "🇵🇾"},
    "596": {"name": "Martinique", "flag": "🇲🇶"},
    "597": {"name": "Suriname", "flag": "🇸🇷"},
    "598": {"name": "Uruguay", "flag": "🇺🇾"},
    "599": {"name": "Caribbean Netherlands", "flag": "🇧🇶"},
    "670": {"name": "East Timor", "flag": "🇹🇱"},
    "672": {"name": "Australian External Territories", "flag": "🇦🇺"},
    "673": {"name": "Brunei", "flag": "🇧🇳"},
    "674": {"name": "Nauru", "flag": "🇳🇷"},
    "675": {"name": "Papua New Guinea", "flag": "🇵🇬"},
    "676": {"name": "Tonga", "flag": "🇹🇴"},
    "677": {"name": "Solomon Islands", "flag": "🇸🇧"},
    "678": {"name": "Vanuatu", "flag": "🇻🇺"},
    "679": {"name": "Fiji", "flag": "🇫🇯"},
    "680": {"name": "Palau", "flag": "🇵🇼"},
    "681": {"name": "Wallis and Futuna", "flag": "🇼🇫"},
    "682": {"name": "Cook Islands", "flag": "🇨🇰"},
    "683": {"name": "Niue", "flag": "🇳🇺"},
    "685": {"name": "Samoa", "flag": "🇼🇸"},
    "686": {"name": "Kiribati", "flag": "🇰🇮"},
    "687": {"name": "New Caledonia", "flag": "🇳🇨"},
    "688": {"name": "Tuvalu", "flag": "🇹🇻"},
    "689": {"name": "French Polynesia", "flag": "🇵🇫"},
    "690": {"name": "Tokelau", "flag": "🇹🇰"},
    "691": {"name": "Micronesia", "flag": "🇫🇲"},
    "692": {"name": "Marshall Islands", "flag": "🇲🇭"},
    "850": {"name": "North Korea", "flag": "🇰🇵"},
    "852": {"name": "Hong Kong", "flag": "🇭🇰"},
    "853": {"name": "Macau", "flag": "🇲🇴"},
    "855": {"name": "Cambodia", "flag": "🇰🇭"},
    "856": {"name": "Laos", "flag": "🇱🇦"},
    "880": {"name": "Bangladesh", "flag": "🇧🇩"},
    "886": {"name": "Taiwan", "flag": "🇹🇼"},
    "960": {"name": "Maldives", "flag": "🇲🇻"},
    "961": {"name": "Lebanon", "flag": "🇱🇧"},
    "962": {"name": "Jordan", "flag": "🇯🇴"},
    "963": {"name": "Syria", "flag": "🇸🇾"},
    "964": {"name": "Iraq", "flag": "🇮🇶"},
    "965": {"name": "Kuwait", "flag": "🇰🇼"},
    "966": {"name": "Saudi Arabia", "flag": "🇸🇦"},
    "967": {"name": "Yemen", "flag": "🇾🇪"},
    "968": {"name": "Oman", "flag": "🇴🇲"},
    "970": {"name": "Palestine", "flag": "🇵🇸"},
    "971": {"name": "UAE", "flag": "🇦🇪"},
    "972": {"name": "Israel", "flag": "🇮🇱"},
    "973": {"name": "Bahrain", "flag": "🇧🇭"},
    "974": {"name": "Qatar", "flag": "🇶🇦"},
    "975": {"name": "Bhutan", "flag": "🇧🇹"},
    "976": {"name": "Mongolia", "flag": "🇲🇳"},
    "977": {"name": "Nepal", "flag": "🇳🇵"},
    "992": {"name": "Tajikistan", "flag": "🇹🇯"},
    "993": {"name": "Turkmenistan", "flag": "🇹🇲"},
    "994": {"name": "Azerbaijan", "flag": "🇦🇿"},
    "995": {"name": "Georgia", "flag": "🇬🇪"},
    "996": {"name": "Kyrgyzstan", "flag": "🇰🇬"},
    "998": {"name": "Uzbekistan", "flag": "🇺🇿"}
}

def get_country_info(phone_number: str) -> Dict[str, str]:
    """Extract country name and flag from a phone number prefix."""
    # Remove non‑digits
    digits = re.sub(r'\D', '', phone_number)
    if not digits:
        return {"country": "Unknown", "flag": "🌍"}
    # Try prefixes from longest to shortest
    for i in range(4, 0, -1):
        prefix = digits[:i]
        if prefix in COUNTRY_CODES:
            info = COUNTRY_CODES[prefix]
            return {"country": info["name"], "flag": info["flag"]}
    return {"country": "Unknown", "flag": "🌍"}

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

    def get_numbers(self) -> List[Dict[str, str]]:
        """Return numbers with country info."""
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
            numbers = []
            for row in rows:
                if isinstance(row, list) and len(row) > 3 and row[3].strip():
                    number = row[3].strip()
                    info = get_country_info(number)
                    numbers.append({
                        "number": number,
                        "country": info["country"],
                        "flag": info["flag"]
                    })
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
                    continue
                otp = self._extract_otp(message)
                info = get_country_info(number)
                sms_list.append({
                    "number": number,
                    "message": message[:300],
                    "timestamp": timestamp,
                    "otp": otp,
                    "country": info["country"],
                    "flag": info["flag"]
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

# ─── FLASK APP WITH CORS ───────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

@app.route('/')
def index():
    return jsonify({
        "service": "Konekt Panel API",
        "endpoints": {
            "/numbers": "GET – returns list of phone numbers with country flags",
            "/sms": "GET – returns list of SMS with OTPs, country flags (optional ?limit=50)"
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

# ─── VERCEL ENTRY POINT ────────────────────────────────────────────────
# Vercel expects a variable named 'app' – already defined.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
