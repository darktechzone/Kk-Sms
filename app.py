#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

# ─── CONFIG ──────────────────────────────────────────────────────────────
BASE_URL = "https://konektapremium.net"
USERNAME = "Slaeem777"
PASSWORD = "Slaeem1234"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive",
}

# ─── FULL COUNTRY MAPPING (UNIQUE) ─────────────────────────────────────
COUNTRY_MAP = {
    "1": {"code": "+1", "name": "USA/Canada", "flag": "🇺🇸"},
    "7": {"code": "+7", "name": "Russia", "flag": "🇷🇺"},
    "20": {"code": "+20", "name": "Egypt", "flag": "🇪🇬"},
    "27": {"code": "+27", "name": "South Africa", "flag": "🇿🇦"},
    "30": {"code": "+30", "name": "Greece", "flag": "🇬🇷"},
    "31": {"code": "+31", "name": "Netherlands", "flag": "🇳🇱"},
    "32": {"code": "+32", "name": "Belgium", "flag": "🇧🇪"},
    "33": {"code": "+33", "name": "France", "flag": "🇫🇷"},
    "34": {"code": "+34", "name": "Spain", "flag": "🇪🇸"},
    "36": {"code": "+36", "name": "Hungary", "flag": "🇭🇺"},
    "39": {"code": "+39", "name": "Italy", "flag": "🇮🇹"},
    "40": {"code": "+40", "name": "Romania", "flag": "🇷🇴"},
    "41": {"code": "+41", "name": "Switzerland", "flag": "🇨🇭"},
    "43": {"code": "+43", "name": "Austria", "flag": "🇦🇹"},
    "44": {"code": "+44", "name": "United Kingdom", "flag": "🇬🇧"},
    "45": {"code": "+45", "name": "Denmark", "flag": "🇩🇰"},
    "46": {"code": "+46", "name": "Sweden", "flag": "🇸🇪"},
    "47": {"code": "+47", "name": "Norway", "flag": "🇳🇴"},
    "48": {"code": "+48", "name": "Poland", "flag": "🇵🇱"},
    "49": {"code": "+49", "name": "Germany", "flag": "🇩🇪"},
    "51": {"code": "+51", "name": "Peru", "flag": "🇵🇪"},
    "52": {"code": "+52", "name": "Mexico", "flag": "🇲🇽"},
    "53": {"code": "+53", "name": "Cuba", "flag": "🇨🇺"},
    "54": {"code": "+54", "name": "Argentina", "flag": "🇦🇷"},
    "55": {"code": "+55", "name": "Brazil", "flag": "🇧🇷"},
    "56": {"code": "+56", "name": "Chile", "flag": "🇨🇱"},
    "57": {"code": "+57", "name": "Colombia", "flag": "🇨🇴"},
    "58": {"code": "+58", "name": "Venezuela", "flag": "🇻🇪"},
    "60": {"code": "+60", "name": "Malaysia", "flag": "🇲🇾"},
    "61": {"code": "+61", "name": "Australia", "flag": "🇦🇺"},
    "62": {"code": "+62", "name": "Indonesia", "flag": "🇮🇩"},
    "63": {"code": "+63", "name": "Philippines", "flag": "🇵🇭"},
    "64": {"code": "+64", "name": "New Zealand", "flag": "🇳🇿"},
    "65": {"code": "+65", "name": "Singapore", "flag": "🇸🇬"},
    "66": {"code": "+66", "name": "Thailand", "flag": "🇹🇭"},
    "81": {"code": "+81", "name": "Japan", "flag": "🇯🇵"},
    "82": {"code": "+82", "name": "South Korea", "flag": "🇰🇷"},
    "84": {"code": "+84", "name": "Vietnam", "flag": "🇻🇳"},
    "86": {"code": "+86", "name": "China", "flag": "🇨🇳"},
    "90": {"code": "+90", "name": "Turkey", "flag": "🇹🇷"},
    "91": {"code": "+91", "name": "India", "flag": "🇮🇳"},
    "92": {"code": "+92", "name": "Pakistan", "flag": "🇵🇰"},
    "93": {"code": "+93", "name": "Afghanistan", "flag": "🇦🇫"},
    "94": {"code": "+94", "name": "Sri Lanka", "flag": "🇱🇰"},
    "95": {"code": "+95", "name": "Myanmar", "flag": "🇲🇲"},
    "98": {"code": "+98", "name": "Iran", "flag": "🇮🇷"},
    "211": {"code": "+211", "name": "South Sudan", "flag": "🇸🇸"},
    "212": {"code": "+212", "name": "Morocco", "flag": "🇲🇦"},
    "213": {"code": "+213", "name": "Algeria", "flag": "🇩🇿"},
    "216": {"code": "+216", "name": "Tunisia", "flag": "🇹🇳"},
    "218": {"code": "+218", "name": "Libya", "flag": "🇱🇾"},
    "220": {"code": "+220", "name": "Gambia", "flag": "🇬🇲"},
    "221": {"code": "+221", "name": "Senegal", "flag": "🇸🇳"},
    "222": {"code": "+222", "name": "Mauritania", "flag": "🇲🇷"},
    "223": {"code": "+223", "name": "Mali", "flag": "🇲🇱"},
    "224": {"code": "+224", "name": "Guinea", "flag": "🇬🇳"},
    "225": {"code": "+225", "name": "Ivory Coast", "flag": "🇨🇮"},
    "226": {"code": "+226", "name": "Burkina Faso", "flag": "🇧🇫"},
    "227": {"code": "+227", "name": "Niger", "flag": "🇳🇪"},
    "228": {"code": "+228", "name": "Togo", "flag": "🇹🇬"},
    "229": {"code": "+229", "name": "Benin", "flag": "🇧🇯"},
    "230": {"code": "+230", "name": "Mauritius", "flag": "🇲🇺"},
    "231": {"code": "+231", "name": "Liberia", "flag": "🇱🇷"},
    "232": {"code": "+232", "name": "Sierra Leone", "flag": "🇸🇱"},
    "233": {"code": "+233", "name": "Ghana", "flag": "🇬🇭"},
    "234": {"code": "+234", "name": "Nigeria", "flag": "🇳🇬"},
    "235": {"code": "+235", "name": "Chad", "flag": "🇹🇩"},
    "236": {"code": "+236", "name": "Central African Republic", "flag": "🇨🇫"},
    "237": {"code": "+237", "name": "Cameroon", "flag": "🇨🇲"},
    "238": {"code": "+238", "name": "Cape Verde", "flag": "🇨🇻"},
    "239": {"code": "+239", "name": "São Tomé and Príncipe", "flag": "🇸🇹"},
    "240": {"code": "+240", "name": "Equatorial Guinea", "flag": "🇬🇶"},
    "241": {"code": "+241", "name": "Gabon", "flag": "🇬🇦"},
    "242": {"code": "+242", "name": "Congo", "flag": "🇨🇬"},
    "243": {"code": "+243", "name": "DR Congo", "flag": "🇨🇩"},
    "244": {"code": "+244", "name": "Angola", "flag": "🇦🇴"},
    "245": {"code": "+245", "name": "Guinea-Bissau", "flag": "🇬🇼"},
    "246": {"code": "+246", "name": "Diego Garcia", "flag": "🇮🇴"},
    "248": {"code": "+248", "name": "Seychelles", "flag": "🇸🇨"},
    "249": {"code": "+249", "name": "Sudan", "flag": "🇸🇩"},
    "250": {"code": "+250", "name": "Rwanda", "flag": "🇷🇼"},
    "251": {"code": "+251", "name": "Ethiopia", "flag": "🇪🇹"},
    "252": {"code": "+252", "name": "Somalia", "flag": "🇸🇴"},
    "253": {"code": "+253", "name": "Djibouti", "flag": "🇩🇯"},
    "254": {"code": "+254", "name": "Kenya", "flag": "🇰🇪"},
    "255": {"code": "+255", "name": "Tanzania", "flag": "🇹🇿"},
    "256": {"code": "+256", "name": "Uganda", "flag": "🇺🇬"},
    "257": {"code": "+257", "name": "Burundi", "flag": "🇧🇮"},
    "258": {"code": "+258", "name": "Mozambique", "flag": "🇲🇿"},
    "260": {"code": "+260", "name": "Zambia", "flag": "🇿🇲"},
    "261": {"code": "+261", "name": "Madagascar", "flag": "🇲🇬"},
    "262": {"code": "+262", "name": "Réunion", "flag": "🇷🇪"},
    "263": {"code": "+263", "name": "Zimbabwe", "flag": "🇿🇼"},
    "264": {"code": "+264", "name": "Namibia", "flag": "🇳🇦"},
    "265": {"code": "+265", "name": "Malawi", "flag": "🇲🇼"},
    "266": {"code": "+266", "name": "Lesotho", "flag": "🇱🇸"},
    "267": {"code": "+267", "name": "Botswana", "flag": "🇧🇼"},
    "268": {"code": "+268", "name": "Eswatini", "flag": "🇸🇿"},
    "269": {"code": "+269", "name": "Comoros", "flag": "🇰🇲"},
    "290": {"code": "+290", "name": "Saint Helena", "flag": "🇸🇭"},
    "291": {"code": "+291", "name": "Eritrea", "flag": "🇪🇷"},
    "297": {"code": "+297", "name": "Aruba", "flag": "🇦🇼"},
    "298": {"code": "+298", "name": "Faroe Islands", "flag": "🇫🇴"},
    "299": {"code": "+299", "name": "Greenland", "flag": "🇬🇱"},
    "350": {"code": "+350", "name": "Gibraltar", "flag": "🇬🇮"},
    "351": {"code": "+351", "name": "Portugal", "flag": "🇵🇹"},
    "352": {"code": "+352", "name": "Luxembourg", "flag": "🇱🇺"},
    "353": {"code": "+353", "name": "Ireland", "flag": "🇮🇪"},
    "354": {"code": "+354", "name": "Iceland", "flag": "🇮🇸"},
    "355": {"code": "+355", "name": "Albania", "flag": "🇦🇱"},
    "356": {"code": "+356", "name": "Malta", "flag": "🇲🇹"},
    "357": {"code": "+357", "name": "Cyprus", "flag": "🇨🇾"},
    "358": {"code": "+358", "name": "Finland", "flag": "🇫🇮"},
    "359": {"code": "+359", "name": "Bulgaria", "flag": "🇧🇬"},
    "370": {"code": "+370", "name": "Lithuania", "flag": "🇱🇹"},
    "371": {"code": "+371", "name": "Latvia", "flag": "🇱🇻"},
    "372": {"code": "+372", "name": "Estonia", "flag": "🇪🇪"},
    "373": {"code": "+373", "name": "Moldova", "flag": "🇲🇩"},
    "374": {"code": "+374", "name": "Armenia", "flag": "🇦🇲"},
    "375": {"code": "+375", "name": "Belarus", "flag": "🇧🇾"},
    "376": {"code": "+376", "name": "Andorra", "flag": "🇦🇩"},
    "377": {"code": "+377", "name": "Monaco", "flag": "🇲🇨"},
    "378": {"code": "+378", "name": "San Marino", "flag": "🇸🇲"},
    "379": {"code": "+379", "name": "Vatican City", "flag": "🇻🇦"},
    "380": {"code": "+380", "name": "Ukraine", "flag": "🇺🇦"},
    "381": {"code": "+381", "name": "Serbia", "flag": "🇷🇸"},
    "382": {"code": "+382", "name": "Montenegro", "flag": "🇲🇪"},
    "383": {"code": "+383", "name": "Kosovo", "flag": "🇽🇰"},
    "385": {"code": "+385", "name": "Croatia", "flag": "🇭🇷"},
    "386": {"code": "+386", "name": "Slovenia", "flag": "🇸🇮"},
    "387": {"code": "+387", "name": "Bosnia and Herzegovina", "flag": "🇧🇦"},
    "389": {"code": "+389", "name": "North Macedonia", "flag": "🇲🇰"},
    "420": {"code": "+420", "name": "Czech Republic", "flag": "🇨🇿"},
    "421": {"code": "+421", "name": "Slovakia", "flag": "🇸🇰"},
    "423": {"code": "+423", "name": "Liechtenstein", "flag": "🇱🇮"},
    "500": {"code": "+500", "name": "Falkland Islands", "flag": "🇫🇰"},
    "501": {"code": "+501", "name": "Belize", "flag": "🇧🇿"},
    "502": {"code": "+502", "name": "Guatemala", "flag": "🇬🇹"},
    "503": {"code": "+503", "name": "El Salvador", "flag": "🇸🇻"},
    "504": {"code": "+504", "name": "Honduras", "flag": "🇭🇳"},
    "505": {"code": "+505", "name": "Nicaragua", "flag": "🇳🇮"},
    "506": {"code": "+506", "name": "Costa Rica", "flag": "🇨🇷"},
    "507": {"code": "+507", "name": "Panama", "flag": "🇵🇦"},
    "508": {"code": "+508", "name": "Saint Pierre and Miquelon", "flag": "🇵🇲"},
    "509": {"code": "+509", "name": "Haiti", "flag": "🇭🇹"},
    "590": {"code": "+590", "name": "Guadeloupe", "flag": "🇬🇵"},
    "591": {"code": "+591", "name": "Bolivia", "flag": "🇧🇴"},
    "592": {"code": "+592", "name": "Guyana", "flag": "🇬🇾"},
    "593": {"code": "+593", "name": "Ecuador", "flag": "🇪🇨"},
    "594": {"code": "+594", "name": "French Guiana", "flag": "🇬🇫"},
    "595": {"code": "+595", "name": "Paraguay", "flag": "🇵🇾"},
    "596": {"code": "+596", "name": "Martinique", "flag": "🇲🇶"},
    "597": {"code": "+597", "name": "Suriname", "flag": "🇸🇷"},
    "598": {"code": "+598", "name": "Uruguay", "flag": "🇺🇾"},
    "599": {"code": "+599", "name": "Caribbean Netherlands", "flag": "🇧🇶"},
    "670": {"code": "+670", "name": "East Timor", "flag": "🇹🇱"},
    "672": {"code": "+672", "name": "Australian External Territories", "flag": "🇦🇺"},
    "673": {"code": "+673", "name": "Brunei", "flag": "🇧🇳"},
    "674": {"code": "+674", "name": "Nauru", "flag": "🇳🇷"},
    "675": {"code": "+675", "name": "Papua New Guinea", "flag": "🇵🇬"},
    "676": {"code": "+676", "name": "Tonga", "flag": "🇹🇴"},
    "677": {"code": "+677", "name": "Solomon Islands", "flag": "🇸🇧"},
    "678": {"code": "+678", "name": "Vanuatu", "flag": "🇻🇺"},
    "679": {"code": "+679", "name": "Fiji", "flag": "🇫🇯"},
    "680": {"code": "+680", "name": "Palau", "flag": "🇵🇼"},
    "681": {"code": "+681", "name": "Wallis and Futuna", "flag": "🇼🇫"},
    "682": {"code": "+682", "name": "Cook Islands", "flag": "🇨🇰"},
    "683": {"code": "+683", "name": "Niue", "flag": "🇳🇺"},
    "685": {"code": "+685", "name": "Samoa", "flag": "🇼🇸"},
    "686": {"code": "+686", "name": "Kiribati", "flag": "🇰🇮"},
    "687": {"code": "+687", "name": "New Caledonia", "flag": "🇳🇨"},
    "688": {"code": "+688", "name": "Tuvalu", "flag": "🇹🇻"},
    "689": {"code": "+689", "name": "French Polynesia", "flag": "🇵🇫"},
    "690": {"code": "+690", "name": "Tokelau", "flag": "🇹🇰"},
    "691": {"code": "+691", "name": "Micronesia", "flag": "🇫🇲"},
    "692": {"code": "+692", "name": "Marshall Islands", "flag": "🇲🇭"},
    "850": {"code": "+850", "name": "North Korea", "flag": "🇰🇵"},
    "852": {"code": "+852", "name": "Hong Kong", "flag": "🇭🇰"},
    "853": {"code": "+853", "name": "Macau", "flag": "🇲🇴"},
    "855": {"code": "+855", "name": "Cambodia", "flag": "🇰🇭"},
    "856": {"code": "+856", "name": "Laos", "flag": "🇱🇦"},
    "880": {"code": "+880", "name": "Bangladesh", "flag": "🇧🇩"},
    "886": {"code": "+886", "name": "Taiwan", "flag": "🇹🇼"},
    "960": {"code": "+960", "name": "Maldives", "flag": "🇲🇻"},
    "961": {"code": "+961", "name": "Lebanon", "flag": "🇱🇧"},
    "962": {"code": "+962", "name": "Jordan", "flag": "🇯🇴"},
    "963": {"code": "+963", "name": "Syria", "flag": "🇸🇾"},
    "964": {"code": "+964", "name": "Iraq", "flag": "🇮🇶"},
    "965": {"code": "+965", "name": "Kuwait", "flag": "🇰🇼"},
    "966": {"code": "+966", "name": "Saudi Arabia", "flag": "🇸🇦"},
    "967": {"code": "+967", "name": "Yemen", "flag": "🇾🇪"},
    "968": {"code": "+968", "name": "Oman", "flag": "🇴🇲"},
    "970": {"code": "+970", "name": "Palestine", "flag": "🇵🇸"},
    "971": {"code": "+971", "name": "UAE", "flag": "🇦🇪"},
    "972": {"code": "+972", "name": "Israel", "flag": "🇮🇱"},
    "973": {"code": "+973", "name": "Bahrain", "flag": "🇧🇭"},
    "974": {"code": "+974", "name": "Qatar", "flag": "🇶🇦"},
    "975": {"code": "+975", "name": "Bhutan", "flag": "🇧🇹"},
    "976": {"code": "+976", "name": "Mongolia", "flag": "🇲🇳"},
    "977": {"code": "+977", "name": "Nepal", "flag": "🇳🇵"},
    "992": {"code": "+992", "name": "Tajikistan", "flag": "🇹🇯"},
    "993": {"code": "+993", "name": "Turkmenistan", "flag": "🇹🇲"},
    "994": {"code": "+994", "name": "Azerbaijan", "flag": "🇦🇿"},
    "995": {"code": "+995", "name": "Georgia", "flag": "🇬🇪"},
    "996": {"code": "+996", "name": "Kyrgyzstan", "flag": "🇰🇬"},
    "998": {"code": "+998", "name": "Uzbekistan", "flag": "🇺🇿"},
}

# ─── CAPTCHA SOLVER ──────────────────────────────────────────────────────
def solve_captcha(question_text: str) -> int:
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

# ─── CLIENT ──────────────────────────────────────────────────────────────
class KonektClient:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
        self.sesskey = None
        self.last_error = None

    def login(self) -> bool:
        print("[*] Logging in...")
        login_page_url = f"{BASE_URL}/sign-in"
        try:
            resp = self.session.get(login_page_url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                self.last_error = f"Login page returned {resp.status_code}"
                print(f"[!] {self.last_error}")
                return False

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Extract captcha
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
                self.last_error = "Could not find captcha question"
                print(f"[!] {self.last_error}")
                return False

            print(f"[*] Captcha: {captcha_text}")
            try:
                captcha_answer = solve_captcha(captcha_text)
                print(f"[*] Answer: {captcha_answer}")
            except Exception as e:
                self.last_error = f"Captcha solve error: {e}"
                print(f"[!] {self.last_error}")
                return False

            form = soup.find('form')
            if not form:
                self.last_error = "No form found on login page"
                print(f"[!] {self.last_error}")
                return False

            action = form.get('action', '')
            if not action:
                action = login_page_url
            elif not action.startswith('http'):
                if action.startswith('/'):
                    action = f"{BASE_URL}{action}"
                else:
                    action = f"{BASE_URL}/{action}"

            payload = {}
            for inp in form.find_all('input'):
                name = inp.get('name')
                value = inp.get('value', '')
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
                self.last_error = "Could not identify username/password fields"
                print(f"[!] {self.last_error}")
                return False

            payload[username_field] = USERNAME
            payload[password_field] = PASSWORD
            if captcha_field:
                payload[captcha_field] = str(captcha_answer)

            print(f"[*] Payload: {payload}")

            login_headers = {
                "User-Agent": HEADERS["User-Agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": login_page_url,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            resp2 = self.session.post(action, data=payload, headers=login_headers, allow_redirects=True, timeout=15)

            print(f"[*] Login POST status: {resp2.status_code}")
            print(f"[*] Final URL: {resp2.url}")

            if "dashboard" in resp2.url.lower() or "agent" in resp2.url.lower():
                self.logged_in = True
                self._extract_sesskey()
                print("[✓] Login successful.")
                return True
            else:
                snippet = resp2.text[:200] if resp2.text else ""
                self.last_error = f"Login POST returned {resp2.status_code}, URL: {resp2.url}. Snippet: {snippet}"
                print(f"[!] {self.last_error}")
                return False

        except Exception as e:
            self.last_error = f"Login exception: {str(e)}"
            print(f"[!] {self.last_error}")
            return False

    def _extract_sesskey(self):
        try:
            resp = self.session.get(f"{BASE_URL}/agent/SMSCDRStats", headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                html = resp.text
                patterns = [
                    r'sesskey=([^&\s"\']+)',
                    r'data_smscdr\.php[^"]*sesskey=([^&"\']+)',
                    r'var\s+sesskey\s*=\s*["\']([^"\']+)["\'];',
                    r'SESSKEY\s*[:=]\s*["\']?([a-zA-Z0-9+/=]+)["\']?'
                ]
                for pat in patterns:
                    match = re.search(pat, html)
                    if match:
                        self.sesskey = match.group(1)
                        print(f"[*] Found sesskey: {self.sesskey}")
                        return
        except:
            pass
        if 'sesskey' in self.session.cookies:
            self.sesskey = self.session.cookies['sesskey']
            print(f"[*] Found sesskey from cookies: {self.sesskey}")
            return
        print("[!] Could not extract sesskey.")

    def _api_request(self, endpoint: str, params: dict, referer: str) -> dict:
        if not self.logged_in:
            raise Exception("Not logged in.")
        url = f"{BASE_URL}{endpoint}"
        headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Accept": HEADERS["Accept"],
            "X-Requested-With": HEADERS["X-Requested-With"],
            "Referer": referer,
        }
        if self.sesskey:
            params['sesskey'] = self.sesskey
        resp = self.session.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code != 200:
            raise Exception(f"API error: {resp.status_code} - {resp.text[:100]}")
        return resp.json()

    def fetch_numbers(self) -> list:
        endpoint = "/agent/res/data_smsnumbers.php"
        params = {
            "frange": "", "fclient": "", "fnumber": "",
            "sEcho": "1", "iDisplayStart": "0", "iDisplayLength": "-1",
            "_": int(time.time() * 1000)
        }
        data = self._api_request(endpoint, params, f"{BASE_URL}/agent/MySMSNumbers2")
        rows = data.get('aaData', [])
        numbers = []
        for row in rows:
            if len(row) >= 4 and row[3]:
                numbers.append(row[3].strip())
        return numbers

    def fetch_sms(self, limit=20) -> list:
        endpoint = "/agent/res/data_smscdr.php"
        today = time.strftime("%Y-%m-%d")
        params = {
            "fdate1": f"{today} 00:00:00",
            "fdate2": f"{today} 23:59:59",
            "frange": "", "fclient": "", "fnum": "", "fcli": "",
            "fgdate": "", "fgmonth": "", "fgrange": "", "fgclient": "",
            "fgnumber": "", "fgcli": "",
            "fg": "0",
            "sEcho": "1",
            "iDisplayStart": "0",
            "iDisplayLength": str(limit),
            "_": int(time.time() * 1000)
        }
        data = self._api_request(endpoint, params, f"{BASE_URL}/agent/SMSCDRStats")
        rows = data.get('aaData', [])
        sms_list = []
        for row in rows:
            if len(row) < 6:
                continue
            number = row[2].strip() if row[2] else ''
            message = row[5].strip() if row[5] else ''
            timestamp = row[0].strip() if row[0] else ''
            if number and message:
                sms_list.append({
                    "number": number,
                    "message": message[:200],
                    "timestamp": timestamp
                })
        return sms_list

# ─── COUNTRY DETECTION ──────────────────────────────────────────────────
def get_country_for_number(number: str) -> dict:
    digits = re.sub(r'\D', '', number)
    if not digits:
        return {"code": "XX", "name": "Unknown", "flag": "🌍"}
    for length in range(4, 0, -1):
        prefix = digits[:length]
        if prefix in COUNTRY_MAP:
            return COUNTRY_MAP[prefix]
    return {"code": "XX", "name": "Unknown", "flag": "🌍"}

# ─── FLASK ENDPOINTS ────────────────────────────────────────────────────
client = KonektClient()

@app.before_request
def ensure_login():
    if not client.logged_in:
        if not client.login():
            return jsonify({
                "status": "error",
                "message": "Login failed",
                "reason": client.last_error
            }), 503

@app.route('/', methods=['GET', 'OPTIONS'])
def root():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        "message": "Konekt API Server",
        "endpoints": ["/numbers", "/sms"],
        "status": "running"
    })

@app.route('/numbers', methods=['GET', 'OPTIONS'])
def api_numbers():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        numbers = client.fetch_numbers()
        result = []
        for num in numbers:
            country = get_country_for_number(num)
            result.append({
                "number": num,
                "country": country["name"],
                "flag": country["flag"],
                "code": country["code"]
            })
        return jsonify({"success": True, "count": len(result), "numbers": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/sms', methods=['GET', 'OPTIONS'])
def api_sms():
    if request.method == 'OPTIONS':
        return '', 200
    limit = request.args.get('limit', 20, type=int)
    try:
        sms = client.fetch_sms(limit=limit)
        for s in sms:
            country = get_country_for_number(s["number"])
            s["country"] = country["name"]
            s["flag"] = country["flag"]
            s["code"] = country["code"]
        return jsonify({"success": True, "count": len(sms), "messages": sms})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─── MAIN ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[*] Starting Konekt API...")
    if client.login():
        print("✅ Initial login successful.")
    else:
        print("⚠️ Login failed.")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
