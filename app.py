#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import hashlib
from typing import Optional, Dict, Any, List
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ─── CONFIG ──────────────────────────────────────────────────────────────
BASE_URL = "https://konektapremium.net"
USERNAME = "Slaeem777"
PASSWORD = "Slaeem1234"
PORT = int(os.environ.get("PORT", 8034))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE_URL,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json, text/plain, */*"
}

# ─── CACHE CONFIG ────────────────────────────────────────────────────────
CACHE_TTL_FRESH = 10          # seconds – use fresh cache
CACHE_TTL_FALLBACK = 5 * 60   # 5 min – fallback if fetch fails

# ─── STATE ──────────────────────────────────────────────────────────────
session_cookie = None
sesskey = None
last_login = 0
is_logging_in = False

otp_cache = {"data": [], "timestamp": 0}
numbers_cache = {"data": [], "timestamp": 0}
cache_refresh_in_progress = False

consecutive_failures = 0
FAILURE_THRESHOLD = 5
BREAKER_TIMEOUT = 30  # seconds

# ─── HELPER: GET COUNTRY FROM PHONE NUMBER ─────────────────────────────

COUNTRY_MAP = {
    '1': {'code': '+1', 'name': 'USA/Canada'},
    '7': {'code': '+7', 'name': 'Russia'},
    '20': {'code': '+20', 'name': 'Egypt'},
    '27': {'code': '+27', 'name': 'South Africa'},
    '30': {'code': '+30', 'name': 'Greece'},
    '31': {'code': '+31', 'name': 'Netherlands'},
    '32': {'code': '+32', 'name': 'Belgium'},
    '33': {'code': '+33', 'name': 'France'},
    '34': {'code': '+34', 'name': 'Spain'},
    '36': {'code': '+36', 'name': 'Hungary'},
    '39': {'code': '+39', 'name': 'Italy'},
    '40': {'code': '+40', 'name': 'Romania'},
    '41': {'code': '+41', 'name': 'Switzerland'},
    '43': {'code': '+43', 'name': 'Austria'},
    '44': {'code': '+44', 'name': 'United Kingdom'},
    '45': {'code': '+45', 'name': 'Denmark'},
    '46': {'code': '+46', 'name': 'Sweden'},
    '47': {'code': '+47', 'name': 'Norway'},
    '48': {'code': '+48', 'name': 'Poland'},
    '49': {'code': '+49', 'name': 'Germany'},
    '51': {'code': '+51', 'name': 'Peru'},
    '52': {'code': '+52', 'name': 'Mexico'},
    '53': {'code': '+53', 'name': 'Cuba'},
    '54': {'code': '+54', 'name': 'Argentina'},
    '55': {'code': '+55', 'name': 'Brazil'},
    '56': {'code': '+56', 'name': 'Chile'},
    '57': {'code': '+57', 'name': 'Colombia'},
    '58': {'code': '+58', 'name': 'Venezuela'},
    '60': {'code': '+60', 'name': 'Malaysia'},
    '61': {'code': '+61', 'name': 'Australia'},
    '62': {'code': '+62', 'name': 'Indonesia'},
    '63': {'code': '+63', 'name': 'Philippines'},
    '64': {'code': '+64', 'name': 'New Zealand'},
    '65': {'code': '+65', 'name': 'Singapore'},
    '66': {'code': '+66', 'name': 'Thailand'},
    '81': {'code': '+81', 'name': 'Japan'},
    '82': {'code': '+82', 'name': 'South Korea'},
    '84': {'code': '+84', 'name': 'Vietnam'},
    '86': {'code': '+86', 'name': 'China'},
    '90': {'code': '+90', 'name': 'Turkey'},
    '91': {'code': '+91', 'name': 'India'},
    '92': {'code': '+92', 'name': 'Pakistan'},
    '93': {'code': '+93', 'name': 'Afghanistan'},
    '94': {'code': '+94', 'name': 'Sri Lanka'},
    '95': {'code': '+95', 'name': 'Myanmar'},
    '98': {'code': '+98', 'name': 'Iran'},
    '211': {'code': '+211', 'name': 'South Sudan'},
    '212': {'code': '+212', 'name': 'Morocco'},
    '213': {'code': '+213', 'name': 'Algeria'},
    '216': {'code': '+216', 'name': 'Tunisia'},
    '218': {'code': '+218', 'name': 'Libya'},
    '220': {'code': '+220', 'name': 'Gambia'},
    '221': {'code': '+221', 'name': 'Senegal'},
    '222': {'code': '+222', 'name': 'Mauritania'},
    '223': {'code': '+223', 'name': 'Mali'},
    '224': {'code': '+224', 'name': 'Guinea'},
    '225': {'code': '+225', 'name': 'Ivory Coast'},
    '226': {'code': '+226', 'name': 'Burkina Faso'},
    '227': {'code': '+227', 'name': 'Niger'},
    '228': {'code': '+228', 'name': 'Togo'},
    '229': {'code': '+229', 'name': 'Benin'},
    '230': {'code': '+230', 'name': 'Mauritius'},
    '231': {'code': '+231', 'name': 'Liberia'},
    '232': {'code': '+232', 'name': 'Sierra Leone'},
    '233': {'code': '+233', 'name': 'Ghana'},
    '234': {'code': '+234', 'name': 'Nigeria'},
    '235': {'code': '+235', 'name': 'Chad'},
    '236': {'code': '+236', 'name': 'Central African Republic'},
    '237': {'code': '+237', 'name': 'Cameroon'},
    '238': {'code': '+238', 'name': 'Cape Verde'},
    '239': {'code': '+239', 'name': 'Sao Tome and Principe'},
    '240': {'code': '+240', 'name': 'Equatorial Guinea'},
    '241': {'code': '+241', 'name': 'Gabon'},
    '242': {'code': '+242', 'name': 'Congo'},
    '243': {'code': '+243', 'name': 'DRC'},
    '244': {'code': '+244', 'name': 'Angola'},
    '245': {'code': '+245', 'name': 'Guinea-Bissau'},
    '246': {'code': '+246', 'name': 'Diego Garcia'},
    '248': {'code': '+248', 'name': 'Seychelles'},
    '249': {'code': '+249', 'name': 'Sudan'},
    '250': {'code': '+250', 'name': 'Rwanda'},
    '251': {'code': '+251', 'name': 'Ethiopia'},
    '252': {'code': '+252', 'name': 'Somalia'},
    '253': {'code': '+253', 'name': 'Djibouti'},
    '254': {'code': '+254', 'name': 'Kenya'},
    '255': {'code': '+255', 'name': 'Tanzania'},
    '256': {'code': '+256', 'name': 'Uganda'},
    '257': {'code': '+257', 'name': 'Burundi'},
    '258': {'code': '+258', 'name': 'Mozambique'},
    '260': {'code': '+260', 'name': 'Zambia'},
    '261': {'code': '+261', 'name': 'Madagascar'},
    '262': {'code': '+262', 'name': 'Reunion'},
    '263': {'code': '+263', 'name': 'Zimbabwe'},
    '264': {'code': '+264', 'name': 'Namibia'},
    '265': {'code': '+265', 'name': 'Malawi'},
    '266': {'code': '+266', 'name': 'Lesotho'},
    '267': {'code': '+267', 'name': 'Botswana'},
    '268': {'code': '+268', 'name': 'Swaziland'},
    '269': {'code': '+269', 'name': 'Comoros'},
    '290': {'code': '+290', 'name': 'St. Helena'},
    '291': {'code': '+291', 'name': 'Eritrea'},
    '297': {'code': '+297', 'name': 'Aruba'},
    '298': {'code': '+298', 'name': 'Faroe Islands'},
    '299': {'code': '+299', 'name': 'Greenland'},
    '350': {'code': '+350', 'name': 'Gibraltar'},
    '351': {'code': '+351', 'name': 'Portugal'},
    '352': {'code': '+352', 'name': 'Luxembourg'},
    '353': {'code': '+353', 'name': 'Ireland'},
    '354': {'code': '+354', 'name': 'Iceland'},
    '355': {'code': '+355', 'name': 'Albania'},
    '356': {'code': '+356', 'name': 'Malta'},
    '357': {'code': '+357', 'name': 'Cyprus'},
    '358': {'code': '+358', 'name': 'Finland'},
    '359': {'code': '+359', 'name': 'Bulgaria'},
    '370': {'code': '+370', 'name': 'Lithuania'},
    '371': {'code': '+371', 'name': 'Latvia'},
    '372': {'code': '+372', 'name': 'Estonia'},
    '373': {'code': '+373', 'name': 'Moldova'},
    '374': {'code': '+374', 'name': 'Armenia'},
    '375': {'code': '+375', 'name': 'Belarus'},
    '376': {'code': '+376', 'name': 'Andorra'},
    '377': {'code': '+377', 'name': 'Monaco'},
    '378': {'code': '+378', 'name': 'San Marino'},
    '379': {'code': '+379', 'name': 'Vatican City'},
    '380': {'code': '+380', 'name': 'Ukraine'},
    '381': {'code': '+381', 'name': 'Serbia'},
    '382': {'code': '+382', 'name': 'Montenegro'},
    '383': {'code': '+383', 'name': 'Kosovo'},
    '385': {'code': '+385', 'name': 'Croatia'},
    '386': {'code': '+386', 'name': 'Slovenia'},
    '387': {'code': '+387', 'name': 'Bosnia and Herzegovina'},
    '389': {'code': '+389', 'name': 'North Macedonia'},
    '420': {'code': '+420', 'name': 'Czech Republic'},
    '421': {'code': '+421', 'name': 'Slovakia'},
    '423': {'code': '+423', 'name': 'Liechtenstein'},
    '500': {'code': '+500', 'name': 'Falkland Islands'},
    '501': {'code': '+501', 'name': 'Belize'},
    '502': {'code': '+502', 'name': 'Guatemala'},
    '503': {'code': '+503', 'name': 'El Salvador'},
    '504': {'code': '+504', 'name': 'Honduras'},
    '505': {'code': '+505', 'name': 'Nicaragua'},
    '506': {'code': '+506', 'name': 'Costa Rica'},
    '507': {'code': '+507', 'name': 'Panama'},
    '508': {'code': '+508', 'name': 'St. Pierre and Miquelon'},
    '509': {'code': '+509', 'name': 'Haiti'},
    '590': {'code': '+590', 'name': 'Guadeloupe'},
    '591': {'code': '+591', 'name': 'Bolivia'},
    '592': {'code': '+592', 'name': 'Guyana'},
    '593': {'code': '+593', 'name': 'Ecuador'},
    '594': {'code': '+594', 'name': 'French Guiana'},
    '595': {'code': '+595', 'name': 'Paraguay'},
    '596': {'code': '+596', 'name': 'Martinique'},
    '597': {'code': '+597', 'name': 'Suriname'},
    '598': {'code': '+598', 'name': 'Uruguay'},
    '599': {'code': '+599', 'name': 'Caribbean Netherlands'},
    '670': {'code': '+670', 'name': 'East Timor'},
    '672': {'code': '+672', 'name': 'Australian External Territories'},
    '673': {'code': '+673', 'name': 'Brunei'},
    '674': {'code': '+674', 'name': 'Nauru'},
    '675': {'code': '+675', 'name': 'Papua New Guinea'},
    '676': {'code': '+676', 'name': 'Tonga'},
    '677': {'code': '+677', 'name': 'Solomon Islands'},
    '678': {'code': '+678', 'name': 'Vanuatu'},
    '679': {'code': '+679', 'name': 'Fiji'},
    '680': {'code': '+680', 'name': 'Palau'},
    '681': {'code': '+681', 'name': 'Wallis and Futuna'},
    '682': {'code': '+682', 'name': 'Cook Islands'},
    '683': {'code': '+683', 'name': 'Niue'},
    '685': {'code': '+685', 'name': 'Samoa'},
    '686': {'code': '+686', 'name': 'Kiribati'},
    '687': {'code': '+687', 'name': 'New Caledonia'},
    '688': {'code': '+688', 'name': 'Tuvalu'},
    '689': {'code': '+689', 'name': 'French Polynesia'},
    '690': {'code': '+690', 'name': 'Tokelau'},
    '691': {'code': '+691', 'name': 'Micronesia'},
    '692': {'code': '+692', 'name': 'Marshall Islands'},
    '850': {'code': '+850', 'name': 'North Korea'},
    '852': {'code': '+852', 'name': 'Hong Kong'},
    '853': {'code': '+853', 'name': 'Macau'},
    '855': {'code': '+855', 'name': 'Cambodia'},
    '856': {'code': '+856', 'name': 'Laos'},
    '880': {'code': '+880', 'name': 'Bangladesh'},
    '886': {'code': '+886', 'name': 'Taiwan'},
    '960': {'code': '+960', 'name': 'Maldives'},
    '961': {'code': '+961', 'name': 'Lebanon'},
    '962': {'code': '+962', 'name': 'Jordan'},
    '963': {'code': '+963', 'name': 'Syria'},
    '964': {'code': '+964', 'name': 'Iraq'},
    '965': {'code': '+965', 'name': 'Kuwait'},
    '966': {'code': '+966', 'name': 'Saudi Arabia'},
    '967': {'code': '+967', 'name': 'Yemen'},
    '968': {'code': '+968', 'name': 'Oman'},
    '970': {'code': '+970', 'name': 'Palestine'},
    '971': {'code': '+971', 'name': 'UAE'},
    '972': {'code': '+972', 'name': 'Israel'},
    '973': {'code': '+973', 'name': 'Bahrain'},
    '974': {'code': '+974', 'name': 'Qatar'},
    '975': {'code': '+975', 'name': 'Bhutan'},
    '976': {'code': '+976', 'name': 'Mongolia'},
    '977': {'code': '+977', 'name': 'Nepal'},
    '992': {'code': '+992', 'name': 'Tajikistan'},
    '993': {'code': '+993', 'name': 'Turkmenistan'},
    '994': {'code': '+994', 'name': 'Azerbaijan'},
    '995': {'code': '+995', 'name': 'Georgia'},
    '996': {'code': '+996', 'name': 'Kyrgyzstan'},
    '998': {'code': '+998', 'name': 'Uzbekistan'}
}

FLAG_MAP = {
    'USA/Canada': '🇺🇸',
    'Russia': '🇷🇺',
    'Egypt': '🇪🇬',
    'South Africa': '🇿🇦',
    'Greece': '🇬🇷',
    'Netherlands': '🇳🇱',
    'Belgium': '🇧🇪',
    'France': '🇫🇷',
    'Spain': '🇪🇸',
    'Hungary': '🇭🇺',
    'Italy': '🇮🇹',
    'Romania': '🇷🇴',
    'Switzerland': '🇨🇭',
    'Austria': '🇦🇹',
    'United Kingdom': '🇬🇧',
    'Denmark': '🇩🇰',
    'Sweden': '🇸🇪',
    'Norway': '🇳🇴',
    'Poland': '🇵🇱',
    'Germany': '🇩🇪',
    'Peru': '🇵🇪',
    'Mexico': '🇲🇽',
    'Cuba': '🇨🇺',
    'Argentina': '🇦🇷',
    'Brazil': '🇧🇷',
    'Chile': '🇨🇱',
    'Colombia': '🇨🇴',
    'Venezuela': '🇻🇪',
    'Malaysia': '🇲🇾',
    'Australia': '🇦🇺',
    'Indonesia': '🇮🇩',
    'Philippines': '🇵🇭',
    'New Zealand': '🇳🇿',
    'Singapore': '🇸🇬',
    'Thailand': '🇹🇭',
    'Japan': '🇯🇵',
    'South Korea': '🇰🇷',
    'Vietnam': '🇻🇳',
    'China': '🇨🇳',
    'Turkey': '🇹🇷',
    'India': '🇮🇳',
    'Pakistan': '🇵🇰',
    'Afghanistan': '🇦🇫',
    'Sri Lanka': '🇱🇰',
    'Myanmar': '🇲🇲',
    'Iran': '🇮🇷',
    'South Sudan': '🇸🇸',
    'Morocco': '🇲🇦',
    'Algeria': '🇩🇿',
    'Tunisia': '🇹🇳',
    'Libya': '🇱🇾',
    'Gambia': '🇬🇲',
    'Senegal': '🇸🇳',
    'Mauritania': '🇲🇷',
    'Mali': '🇲🇱',
    'Guinea': '🇬🇳',
    'Ivory Coast': '🇨🇮',
    'Burkina Faso': '🇧🇫',
    'Niger': '🇳🇪',
    'Togo': '🇹🇬',
    'Benin': '🇧🇯',
    'Mauritius': '🇲🇺',
    'Liberia': '🇱🇷',
    'Sierra Leone': '🇸🇱',
    'Ghana': '🇬🇭',
    'Nigeria': '🇳🇬',
    'Chad': '🇹🇩',
    'Central African Republic': '🇨🇫',
    'Cameroon': '🇨🇲',
    'Cape Verde': '🇨🇻',
    'Sao Tome and Principe': '🇸🇹',
    'Equatorial Guinea': '🇬🇶',
    'Gabon': '🇬🇦',
    'Congo': '🇨🇬',
    'DRC': '🇨🇩',
    'Angola': '🇦🇴',
    'Guinea-Bissau': '🇬🇼',
    'Seychelles': '🇸🇨',
    'Sudan': '🇸🇩',
    'Rwanda': '🇷🇼',
    'Ethiopia': '🇪🇹',
    'Somalia': '🇸🇴',
    'Djibouti': '🇩🇯',
    'Kenya': '🇰🇪',
    'Tanzania': '🇹🇿',
    'Uganda': '🇺🇬',
    'Burundi': '🇧🇮',
    'Mozambique': '🇲🇿',
    'Zambia': '🇿🇲',
    'Madagascar': '🇲🇬',
    'Reunion': '🇷🇪',
    'Zimbabwe': '🇿🇼',
    'Namibia': '🇳🇦',
    'Malawi': '🇲🇼',
    'Lesotho': '🇱🇸',
    'Botswana': '🇧🇼',
    'Swaziland': '🇸🇿',
    'Comoros': '🇰🇲',
    'St. Helena': '🇸🇭',
    'Eritrea': '🇪🇷',
    'Aruba': '🇦🇼',
    'Faroe Islands': '🇫🇴',
    'Greenland': '🇬🇱',
    'Gibraltar': '🇬🇮',
    'Portugal': '🇵🇹',
    'Luxembourg': '🇱🇺',
    'Ireland': '🇮🇪',
    'Iceland': '🇮🇸',
    'Albania': '🇦🇱',
    'Malta': '🇲🇹',
    'Cyprus': '🇨🇾',
    'Finland': '🇫🇮',
    'Bulgaria': '🇧🇬',
    'Lithuania': '🇱🇹',
    'Latvia': '🇱🇻',
    'Estonia': '🇪🇪',
    'Moldova': '🇲🇩',
    'Armenia': '🇦🇲',
    'Belarus': '🇧🇾',
    'Andorra': '🇦🇩',
    'Monaco': '🇲🇨',
    'San Marino': '🇸🇲',
    'Vatican City': '🇻🇦',
    'Ukraine': '🇺🇦',
    'Serbia': '🇷🇸',
    'Montenegro': '🇲🇪',
    'Kosovo': '🇽🇰',
    'Croatia': '🇭🇷',
    'Slovenia': '🇸🇮',
    'Bosnia and Herzegovina': '🇧🇦',
    'North Macedonia': '🇲🇰',
    'Czech Republic': '🇨🇿',
    'Slovakia': '🇸🇰',
    'Liechtenstein': '🇱🇮',
    'Belize': '🇧🇿',
    'Guatemala': '🇬🇹',
    'El Salvador': '🇸🇻',
    'Honduras': '🇭🇳',
    'Nicaragua': '🇳🇮',
    'Costa Rica': '🇨🇷',
    'Panama': '🇵🇦',
    'St. Pierre and Miquelon': '🇵🇲',
    'Haiti': '🇭🇹',
    'Guadeloupe': '🇬🇵',
    'Bolivia': '🇧🇴',
    'Guyana': '🇬🇾',
    'Ecuador': '🇪🇨',
    'French Guiana': '🇬🇫',
    'Paraguay': '🇵🇾',
    'Martinique': '🇲🇶',
    'Suriname': '🇸🇷',
    'Uruguay': '🇺🇾',
    'Caribbean Netherlands': '🇧🇶',
    'East Timor': '🇹🇱',
    'Brunei': '🇧🇳',
    'Nauru': '🇳🇷',
    'Papua New Guinea': '🇵🇬',
    'Tonga': '🇹🇴',
    'Solomon Islands': '🇸🇧',
    'Vanuatu': '🇻🇺',
    'Fiji': '🇫🇯',
    'Palau': '🇵🇼',
    'Cook Islands': '🇨🇰',
    'Samoa': '🇼🇸',
    'Kiribati': '🇰🇮',
    'New Caledonia': '🇳🇨',
    'Tuvalu': '🇹🇻',
    'French Polynesia': '🇵🇫',
    'Micronesia': '🇫🇲',
    'Marshall Islands': '🇲🇭',
    'North Korea': '🇰🇵',
    'Hong Kong': '🇭🇰',
    'Macau': '🇲🇴',
    'Cambodia': '🇰🇭',
    'Laos': '🇱🇦',
    'Bangladesh': '🇧🇩',
    'Taiwan': '🇹🇼',
    'Maldives': '🇲🇻',
    'Lebanon': '🇱🇧',
    'Jordan': '🇯🇴',
    'Syria': '🇸🇾',
    'Iraq': '🇮🇶',
    'Kuwait': '🇰🇼',
    'Saudi Arabia': '🇸🇦',
    'Yemen': '🇾🇪',
    'Oman': '🇴🇲',
    'Palestine': '🇵🇸',
    'UAE': '🇦🇪',
    'Israel': '🇮🇱',
    'Bahrain': '🇧🇭',
    'Qatar': '🇶🇦',
    'Bhutan': '🇧🇹',
    'Mongolia': '🇲🇳',
    'Nepal': '🇳🇵',
    'Tajikistan': '🇹🇯',
    'Turkmenistan': '🇹🇲',
    'Azerbaijan': '🇦🇿',
    'Georgia': '🇬🇪',
    'Kyrgyzstan': '🇰🇬',
    'Uzbekistan': '🇺🇿'
}

def get_country(phone_digits: str) -> Optional[Dict]:
    for length in range(4, 0, -1):
        prefix = phone_digits[:length]
        if prefix in COUNTRY_MAP:
            return COUNTRY_MAP[prefix]
    return None

def clean_number(raw: str) -> Optional[Dict]:
    digits = re.sub(r'\D', '', raw)
    if not digits or len(digits) < 7:
        return None
    info = get_country(digits)
    if info:
        cc = info['code'].replace('+', '')
        rest = digits
        if digits.startswith(cc):
            rest = digits[len(cc):]
        if len(rest) < 7:
            return None
        phone = info['code'] + rest
        country = info['name']
    else:
        phone = '+' + digits
        country = 'Unknown'
    flag = FLAG_MAP.get(country, '🌍')
    return {'phone': phone, 'country': country, 'flag': flag}

# ─── CAPTCHA & SESSION ─────────────────────────────────────────────────

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

def get_cookie_from_headers(headers):
    if not headers or 'set-cookie' not in headers:
        return None
    cookie_string = headers['set-cookie']
    if isinstance(cookie_string, list):
        cookie_string = cookie_string[0]
    match = re.match(r'^([^=]+)=([^;]+)', cookie_string)
    return f"{match.group(1)}={match.group(2)}" if match else None

def login():
    global session_cookie, sesskey, last_login, is_logging_in
    if is_logging_in:
        while is_logging_in:
            time.sleep(0.1)
        return session_cookie is not None
    is_logging_in = True
    try:
        print("[LOGIN] Starting...")
        login_url = f"{BASE_URL}/sign-in"
        resp = requests.get(login_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[LOGIN] Failed to load login page: {resp.status_code}")
            return False
        soup = BeautifulSoup(resp.text, 'html.parser')
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
            print("[!] Could not find captcha question.")
            return False
        print(f"[*] Captcha: {captcha_text}")
        captcha_answer = solve_captcha(captcha_text)
        print(f"[*] Captcha answer: {captcha_answer}")

        form = soup.find('form')
        if not form:
            print("[!] No form found.")
            return False

        action = form.get('action', '')
        if not action:
            action = login_url
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
            print("[!] Could not identify username/password fields.")
            return False

        payload[username_field] = USERNAME
        payload[password_field] = PASSWORD
        if captcha_field:
            payload[captcha_field] = str(captcha_answer)

        current_cookie = get_cookie_from_headers(resp.headers)
        login_headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": login_url,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if current_cookie:
            login_headers["Cookie"] = current_cookie

        r2 = requests.post(action, data=payload, headers=login_headers, allow_redirects=True, timeout=15)
        print(f"[LOGIN] POST status: {r2.status_code}")

        final_cookie = get_cookie_from_headers(r2.headers)
        if final_cookie:
            current_cookie = final_cookie
        if not current_cookie:
            current_cookie = get_cookie_from_headers(resp.headers)

        if r2.status_code in [301, 302] or "dashboard" in r2.url.lower() or "agent" in r2.url.lower():
            session_cookie = current_cookie
            last_login = time.time()
            print(f"[LOGIN] Success with cookie: {session_cookie}")
            fetch_sesskey()
            return True

        print("[!] Login failed.")
        return False
    except Exception as e:
        print(f"[!] Login error: {e}")
        return False
    finally:
        is_logging_in = False

def fetch_sesskey():
    global sesskey
    try:
        url = f"{BASE_URL}/agent/SMSCDRStats"
        headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Cookie": session_cookie,
            "Referer": url
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            patterns = [
                r'data_smscdr\.php[^"]*sesskey=([^&\s"\']+)',
                r'sesskey=([^&\s"\']+)',
                r'var\s+sesskey\s*=\s*["\']([^"\']+)["\'];',
                r'SESSKEY\s*[:=]\s*["\']?([a-zA-Z0-9+/=]+)["\']?'
            ]
            for pat in patterns:
                m = re.search(pat, html)
                if m:
                    sesskey = m.group(1)
                    print(f"[SESSKEY] Found: {sesskey}")
                    return
    except Exception as e:
        print(f"[SESSKEY] Error: {e}")
    sesskey = None

def ensure_session():
    global session_cookie, last_login
    if not session_cookie or (time.time() - last_login) > 3600:
        print("[SESSION] Expired, re-logging...")
        return login()
    if sesskey is None:
        fetch_sesskey()
    return True

# ─── FETCH NUMBERS ──────────────────────────────────────────────────────

def fetch_numbers_raw():
    if not ensure_session():
        raise Exception("Not logged in")
    url = f"{BASE_URL}/agent/res/data_smsnumbers.php"
    params = {
        "frange": "", "fclient": "", "fnumber": "",
        "sEcho": "1", "iDisplayStart": "0", "iDisplayLength": "-1",
        "_": int(time.time() * 1000)
    }
    if sesskey:
        params["sesskey"] = sesskey
    headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Accept": HEADERS["Accept"],
        "X-Requested-With": HEADERS["X-Requested-With"],
        "Referer": f"{BASE_URL}/agent/MySMSNumbers2",
        "Cookie": session_cookie
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"Numbers fetch failed: {resp.status_code}")
    data = resp.json()
    if not data.get("aaData"):
        return []
    result = []
    for row in data["aaData"]:
        if len(row) < 4:
            continue
        raw = (row[3] or "").strip()
        if not raw:
            continue
        cleaned = clean_number(raw)
        if cleaned:
            result.append({
                "raw": raw,
                "e164": cleaned["phone"],
                "country": cleaned["country"],
                "flag": cleaned["flag"]
            })
        else:
            result.append({"raw": raw, "e164": None, "country": "Unknown", "flag": "🌍"})
    return result

# ─── FETCH OTPs ────────────────────────────────────────────────────────

def extract_otp(text: str) -> Optional[str]:
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

def fetch_otps_raw(limit: int = 10):
    if not ensure_session():
        raise Exception("Not logged in")
    today = time.strftime("%Y-%m-%d")
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
    if sesskey:
        params["sesskey"] = sesskey
    headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Accept": HEADERS["Accept"],
        "X-Requested-With": HEADERS["X-Requested-With"],
        "Referer": f"{BASE_URL}/agent/SMSCDRStats",
        "Cookie": session_cookie
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"OTP fetch failed: {resp.status_code}")
    data = resp.json()
    if not data.get("aaData"):
        return []
    rows = data["aaData"]
    rows.sort(key=lambda x: x[0] or "", reverse=True)
    result = []
    for row in rows:
        if len(row) < 6:
            continue
        number = (row[2] or "").strip()
        message = (row[5] or "").strip()
        if not number or not message:
            continue
        otp = extract_otp(message)
        if not otp:
            continue
        service = (row[3] or "Unknown").strip()
        timestamp = row[0] or ""
        cleaned = clean_number(number)
        country = cleaned["country"] if cleaned else "Unknown"
        flag = cleaned["flag"] if cleaned else "🌍"
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
    return result

# ─── CACHE MANAGEMENT ──────────────────────────────────────────────────

def refresh_cache():
    global otp_cache, numbers_cache, cache_refresh_in_progress
    if cache_refresh_in_progress:
        return
    cache_refresh_in_progress = True
    try:
        # Refresh numbers
        nums = fetch_numbers_raw()
        numbers_cache["data"] = nums
        numbers_cache["timestamp"] = time.time()
        # Refresh OTPs
        otps = fetch_otps_raw(10)
        otp_cache["data"] = otps
        otp_cache["timestamp"] = time.time()
        print(f"[CACHE] Updated: {len(nums)} numbers, {len(otps)} OTPs")
    except Exception as e:
        print(f"[CACHE] Error: {e}")
    finally:
        cache_refresh_in_progress = False

def get_cached_otps():
    now = time.time()
    age = now - otp_cache["timestamp"]
    if otp_cache["data"] and age < CACHE_TTL_FALLBACK:
        if age > CACHE_TTL_FRESH:
            # Refresh in background
            threading.Thread(target=refresh_cache, daemon=True).start()
        return otp_cache["data"]
    # Force refresh
    refresh_cache()
    return otp_cache["data"]

def get_cached_numbers():
    now = time.time()
    age = now - numbers_cache["timestamp"]
    if numbers_cache["data"] and age < CACHE_TTL_FALLBACK:
        if age > CACHE_TTL_FRESH:
            threading.Thread(target=refresh_cache, daemon=True).start()
        return numbers_cache["data"]
    refresh_cache()
    return numbers_cache["data"]

# ─── API ROUTES ─────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Konekt API Server",
        "endpoints": ["/api/numbers", "/api/otps/last10"],
        "status": "running"
    })

@app.route('/api/numbers', methods=['GET'])
def api_numbers():
    try:
        numbers = get_cached_numbers()
        return jsonify({"success": True, "count": len(numbers), "numbers": numbers})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/otps/last10', methods=['GET'])
def api_otps():
    try:
        otps = get_cached_otps()
        return jsonify({"success": True, "count": len(otps), "otps": otps})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─── STARTUP ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[*] Starting Konekt API (Vercel-compatible)...")
    if login():
        print("✅ Initial login successful.")
        refresh_cache()
    else:
        print("⚠️ Initial login failed. Endpoints may return errors.")
    app.run(host='0.0.0.0', port=PORT, debug=False)
