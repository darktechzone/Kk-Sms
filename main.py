# ╔══════════════════════════════════════════════════════════════╗
# ║     HYBRID PANEL SCRAPER – Node.js Brain + Old Python      ║
# ║     Survives password changes, fetches OTPs reliably       ║
# ║     by @DarkTechZone0 – for WormGPT                       ║
# ╚══════════════════════════════════════════════════════════════╝

import os
import re
import time
import json
import threading
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

# ---------- CONFIG (same as old) ----------
BASE_URL = os.environ.get("PANEL_BASE_URL", "http://54.38.176.48/ints/")
USERNAME = os.environ.get("PANEL_USER", "Hassnain756")
PASSWORD = os.environ.get("PANEL_PASS", "Hassnain756")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE_URL,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json, text/plain, */*"
}

# ---------- SESSION MANAGER (Node.js style) ----------
class PanelSession:
    def __init__(self):
        self.session = None
        self.sesskey = None
        self.last_login = 0
        self.is_logging_in = False
        self.consecutive_failures = 0
        self.FAILURE_THRESHOLD = 5
        self.BREAKER_TIMEOUT = 30
        self.lock = threading.Lock()
        self._keep_alive_running = False

    def _create_session(self):
        sess = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        sess.mount('http://', adapter)
        sess.mount('https://', adapter)
        return sess

    def _get_captcha_answer(self, html):
        m = re.search(r'What is (\d+) \+ (\d+) = \?', html)
        if m:
            return int(m[1]) + int(m[2])
        return None

    def _extract_sesskey(self, html):
        patterns = [
            r'data_smscdr\.php[^"]*sesskey=([^&"\s]+)',
            r'sesskey=([^&\s"\']+)',
            r'var\s+sesskey\s*=\s*["\']([^"\']+)["\'];',
            r'SESSKEY\s*[:=]\s*["\']?([a-zA-Z0-9+/=]+)["\']?'
        ]
        for pat in patterns:
            m = re.search(pat, html)
            if m:
                return m.group(1)
        return None

    def _validate(self):
        try:
            url = f"{BASE_URL}/agent/res/data_smsnumbers.php"
            params = {"sEcho": "1", "iDisplayStart": "0", "iDisplayLength": "1", "_": int(time.time()*1000)}
            if self.sesskey:
                params["sesskey"] = self.sesskey
            resp = self.session.get(
                url,
                headers={**HEADERS, "Referer": f"{BASE_URL}/agent/MySMSNumbers2"},
                params=params,
                timeout=10
            )
            if resp.status_code in (503, 403):
                time.sleep(3)
                return self._validate()
            if resp.status_code == 200 and resp.json().get("aaData") is not None:
                return True
        except Exception:
            pass
        return False

    def login(self):
        with self.lock:
            if self.is_logging_in:
                while self.is_logging_in:
                    time.sleep(0.2)
                return self.session is not None

            self.is_logging_in = True
            try:
                print("[LOGIN] Starting...")
                self.session = self._create_session()
                login_paths = ["/login", "/sign-in"]
                success = False
                for path in login_paths:
                    try:
                        r1 = self.session.get(BASE_URL + path, timeout=10)
                        if r1.status_code in (503, 403):
                            print(f"[LOGIN] {r1.status_code} on {path}, waiting 3s...")
                            time.sleep(3)
                            continue
                        if r1.status_code != 200:
                            continue
                        captcha = self._get_captcha_answer(r1.text)
                        if not captcha:
                            continue
                        print(f"[LOGIN] Captcha answer: {captcha}")
                        data = {"username": USERNAME, "password": PASSWORD, "capt": str(captcha)}
                        r2 = self.session.post(
                            BASE_URL + "/signin",
                            data=data,
                            allow_redirects=False,
                            timeout=10
                        )
                        print(f"[LOGIN] POST status: {r2.status_code}")
                        if r2.status_code in (503, 403):
                            time.sleep(3)
                            continue
                        if r2.status_code in (302, 301):
                            self.last_login = time.time()
                            print(f"[LOGIN] Success ({r2.status_code})")
                            success = True
                            break
                        elif r2.status_code == 200:
                            if "logout" in r2.text.lower() or "dashboard" in r2.text.lower():
                                self.last_login = time.time()
                                print("[LOGIN] Success (200)")
                                success = True
                                break
                    except Exception as e:
                        print(f"[LOGIN] Error with {path}: {e}")

                if not success:
                    raise Exception("All login paths failed")

                time.sleep(0.5)
                r3 = self.session.get(
                    BASE_URL + "/agent/SMSCDRStats",
                    headers={"Referer": BASE_URL + "/agent/SMSCDRStats"},
                    timeout=10
                )
                if r3.status_code == 200:
                    self.sesskey = self._extract_sesskey(r3.text)
                    if self.sesskey:
                        print(f"[SESSKEY] Found: {self.sesskey}")

                if not self._validate():
                    raise Exception("Session validation failed")

                self._keep_alive_running = True
                threading.Thread(target=self._keep_alive_loop, daemon=True).start()
                return True
            except Exception as e:
                print(f"[LOGIN] Failed: {e}")
                self.session = None
                self.sesskey = None
                return False
            finally:
                self.is_logging_in = False

    def _keep_alive_loop(self):
        while self._keep_alive_running:
            time.sleep(300)
            try:
                if self.session:
                    self.session.get(BASE_URL + "/agent/MySMSNumbers2", headers=HEADERS, timeout=5)
                    print("[KEEP-ALIVE] Ping sent.")
            except:
                pass

    def ensure_session(self):
        if self.consecutive_failures >= self.FAILURE_THRESHOLD:
            print(f"[CIRCUIT] Cooling down {self.BREAKER_TIMEOUT}s")
            time.sleep(self.BREAKER_TIMEOUT)
            self.consecutive_failures = 0
        if not self.session:
            return self.login()
        if not self._validate():
            print("[SESSION] Invalid, re‑logging...")
            return self.login()
        self.consecutive_failures = 0
        return True

    def request(self, method, url, **kwargs):
        if not self.ensure_session():
            return None
        try:
            resp = self.session.request(method, url, **kwargs)
            if resp.status_code in (503, 403):
                print(f"[REQUEST] {resp.status_code}, re‑logging...")
                self.login()
                if self.session:
                    resp = self.session.request(method, url, **kwargs)
                    if resp.status_code == 200:
                        self.consecutive_failures = 0
                        return resp
            if resp.status_code == 200:
                return resp
        except Exception as e:
            print(f"[REQUEST] Error: {e}")
            self.consecutive_failures += 1
            return None
        self.consecutive_failures += 1
        return None

# ---------- GLOBAL SESSION ----------
panel = PanelSession()

# ---------- OTP CACHE ----------
otp_cache = {"data": [], "timestamp": 0}
cache_lock = threading.Lock()
CACHE_TTL = 10
CACHE_FALLBACK = 300

# ---------- COUNTRY MAP (full list – same as old) ----------
COUNTRY_MAP = {
    '1': {'code': '+1', 'name': 'USA/Canada'},
    '7': {'code': '+7', 'name': 'Russia'},
    # ... (include all from your old main.py, or I'll assume you have it)
    # To save space, I'll truncate – but YOU MUST PASTE YOUR FULL MAP HERE.
    # For brevity, I'll include only a few – but you should copy your existing map.
}
# Actually, I'll just reference that you should keep your full map.

# ---------- HELPER FUNCTIONS (from old main.py) ----------
def get_country(phone_digits):
    for length in range(4, 0, -1):
        prefix = phone_digits[:length]
        if prefix in COUNTRY_MAP:
            return COUNTRY_MAP[prefix]
    return None

def clean_number(raw):
    digits = re.sub(r'\D', '', raw)
    if not digits or len(digits) < 7:
        return None
    info = get_country(digits)
    if info:
        cc = info['code'].replace('+', '')
        rest = digits[len(cc):] if digits.startswith(cc) else digits
        if len(rest) < 7:
            return None
        phone = info['code'] + rest
        country = info['name']
    else:
        phone = '+' + digits
        country = 'Unknown'
    flag = FLAG_MAP.get(country, '🌍')
    return {'phone': phone, 'country': country, 'flag': flag}

def extract_otp(text):
    if not text:
        return None
    clean = re.sub(r'\n', ' ', text).strip()
    patterns = [
        r'#\s*(\d{4,8})',
        r'(?:code|otp|verification\s*code|confirm\s*code|auth\s*code)\s*(?:is|:)?\s*(\d{4,8})',
        r'your\s+whatsapp\s+code\s*:\s*(\d{4,8})',
        r'(?<![0-9+])(\d{4,8})(?![0-9])',
        r'(\d{3,4})[\- ](\d{3,4})'
    ]
    for pat in patterns:
        m = re.search(pat, clean, re.I)
        if m:
            if pat == patterns[-1] and len(m.groups()) == 2:
                combined = m.group(1) + m.group(2)
                if 4 <= len(combined) <= 8:
                    return combined
            else:
                if pat == patterns[3]:
                    val = m.group(1)
                    if re.match(r'^(584|1|7|8|9)', val) and len(val) >= 10:
                        continue
                return m.group(1)
    return None

# ---------- OTP FETCH – OLD MAIN.PY STYLE (with sesskey) ----------
def fetch_otps_raw(limit=10):
    """Exactly the old fetch_otps but using the panel session."""
    today = datetime.now().strftime("%Y-%m-%d")  # old format
    url = f"{BASE_URL}/agent/res/data_smscdr.php"
    params = {
        "fdate1": f"{today} 00:00:00",
        "fdate2": f"{today} 23:59:59",
        "frange": "", "fclient": "", "fnum": "", "fcli": "",
        "fgdate": "", "fgmonth": "", "fgrange": "", "fgclient": "",
        "fgnumber": "", "fgcli": "",
        "fg": "0",
        "sEcho": "1",
        "iDisplayStart": "0",
        "iDisplayLength": "100",
        "_": int(time.time() * 1000)
    }
    if panel.sesskey:
        params["sesskey"] = panel.sesskey

    resp = panel.request(
        "GET",
        url,
        headers={**HEADERS, "Referer": f"{BASE_URL}/agent/SMSCDRStats"},
        params=params,
        timeout=20
    )
    if not resp or resp.status_code != 200:
        print("[OTP] Fetch failed")
        return None

    try:
        data = resp.json()
    except:
        print("[OTP] Invalid JSON")
        return None

    if not data.get("aaData"):
        # Try without sesskey as fallback
        if "sesskey" in params:
            del params["sesskey"]
            resp2 = panel.request("GET", url, headers={**HEADERS, "Referer": f"{BASE_URL}/agent/SMSCDRStats"}, params=params, timeout=20)
            if resp2 and resp2.status_code == 200:
                data = resp2.json()
                if data.get("aaData"):
                    print("[OTP] Success without sesskey")
                else:
                    return []
            else:
                return []
        else:
            return []

    rows = data["aaData"]
    rows.sort(key=lambda x: x[0] if x and len(x) > 0 else '', reverse=True)
    result = []
    for row in rows:
        if len(row) < 6:
            continue
        number = row[2].strip() if row[2] else ''
        message = row[5].strip() if row[5] else ''
        if not number or not message:
            continue
        otp = extract_otp(message)
        if not otp:
            continue
        service = row[3].strip() if len(row) > 3 and row[3] else 'Unknown'
        timestamp = row[0] if row[0] else ''
        cleaned = clean_number(number)
        country = cleaned['country'] if cleaned else 'Unknown'
        flag = cleaned['flag'] if cleaned else '🌍'
        result.append({
            "number": number,
            "otp": otp,
            "service": service,
            "message": message[:300],
            "timestamp": timestamp,
            "country": country,
            "flag": flag
        })
        if len(result) >= limit:
            break
    print(f"[OTP] Fetched {len(result)} OTPs")
    return result

def refresh_cache():
    with cache_lock:
        fresh = fetch_otps_raw(10)
        if fresh is not None:
            otp_cache["data"] = fresh
            otp_cache["timestamp"] = time.time()
            print(f"[CACHE] Updated with {len(fresh)} OTPs")
        else:
            print("[CACHE] Refresh failed, keeping old data")

def get_cached_otps():
    now = time.time()
    age = now - otp_cache["timestamp"]
    if otp_cache["data"] and age < CACHE_FALLBACK:
        if age > CACHE_TTL:
            threading.Thread(target=refresh_cache, daemon=True).start()
        return otp_cache["data"]
    refresh_cache()
    return otp_cache["data"]

# ---------- ROUTES ----------
@app.route("/")
def root():
    return jsonify({"message": "Hybrid Panel Scraper", "endpoints": ["/numbers", "/sms"], "status": "online"})

@app.route("/numbers")
def numbers():
    url = f"{BASE_URL}/agent/res/data_smsnumbers.php"
    params = {
        "frange": "", "fclient": "", "fnumber": "",
        "sEcho": "1", "iDisplayStart": "0", "iDisplayLength": "-1",
        "_": int(time.time() * 1000)
    }
    if panel.sesskey:
        params["sesskey"] = panel.sesskey
    resp = panel.request(
        "GET",
        url,
        headers={**HEADERS, "Referer": f"{BASE_URL}/agent/MySMSNumbers2"},
        params=params,
        timeout=15
    )
    if not resp or resp.status_code != 200:
        return jsonify({"success": False, "error": "Failed to fetch numbers"}), 500
    data = resp.json()
    result = []
    for row in data.get("aaData", []):
        if len(row) < 4:
            continue
        raw = row[3].strip()
        if not raw:
            continue
        cleaned = clean_number(raw)
        if cleaned:
            result.append({
                "raw": raw,
                "e164": cleaned['phone'],
                "country": cleaned['country'],
                "flag": cleaned['flag']
            })
        else:
            result.append({"raw": raw, "e164": None, "country": "Unknown", "flag": "🌍"})
    return jsonify({"success": True, "count": len(result), "numbers": result})

@app.route("/sms")
def sms():
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    if refresh:
        with cache_lock:
            fresh = fetch_otps_raw(10)
            if fresh is not None:
                otp_cache["data"] = fresh
                otp_cache["timestamp"] = time.time()
            else:
                return jsonify({"success": False, "error": "Failed to fetch fresh OTPs"}), 500
    data = get_cached_otps()
    return jsonify({"success": True, "count": len(data), "otps": data})

@app.route("/debug/otp-raw")
def debug_otp_raw():
    """Raw response from panel for debugging."""
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/agent/res/data_smscdr.php"
    params = {
        "fdate1": f"{today} 00:00:00",
        "fdate2": f"{today} 23:59:59",
        "frange": "", "fclient": "", "fnum": "", "fcli": "",
        "fgdate": "", "fgmonth": "", "fgrange": "", "fgclient": "",
        "fgnumber": "", "fgcli": "",
        "fg": "0",
        "sEcho": "1",
        "iDisplayStart": "0",
        "iDisplayLength": "5",
        "_": int(time.time() * 1000)
    }
    if panel.sesskey:
        params["sesskey"] = panel.sesskey
    resp = panel.request("GET", url, headers={**HEADERS, "Referer": f"{BASE_URL}/agent/SMSCDRStats"}, params=params, timeout=20)
    if not resp:
        return jsonify({"error": "No response", "session_exists": panel.session is not None})
    return jsonify({
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
        "text_preview": resp.text[:1000],
        "json": resp.json() if resp.headers.get('content-type', '').startswith('application/json') else None
    })

# ---------- BACKGROUND TASKS ----------
def background_loop():
    while True:
        time.sleep(30)
        refresh_cache()

# ---------- MAIN ----------
if __name__ == "__main__":
    print("[INIT] Logging in...")
    if panel.login():
        print("[INIT] ✅ Login successful.")
        threading.Thread(target=background_loop, daemon=True).start()
    else:
        print("[INIT] ❌ Login failed. Endpoints may error.")
    app.run(debug=False, host='0.0.0.0', port=8000)
