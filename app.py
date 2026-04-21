from flask import Flask, jsonify
import requests
import time
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

_cache = {"atr": None, "ts": 0}
CACHE_TTL = 60
API_KEY = "bgH0QPcnGgwSFPBib3TpGdfVpylpC3Bu"

def compute_wilder_atr(candles, period=14):
    highs  = [c["h"] for c in candles]
    lows   = [c["l"] for c in candles]
    closes = [c["c"] for c in candles]
    trs = []
    for i in range(1, len(highs)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i]  - closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        return None
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
    return round(atr, 2)

def fetch_atr():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
    url = (f"https://api.polygon.io/v2/aggs/ticker/C:XAUUSD/range/1/minute"
           f"/{yesterday}/{today}?sort=asc&limit=500&apiKey={API_KEY}")
    r = requests.get(url, timeout=15)
    d = r.json()
    results = d.get("results", [])
    if not results:
        raise Exception("No data from Polygon")
    return compute_wilder_atr(results)

def get_atr():
    now = time.time()
    if _cache["atr"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["atr"], "cache"
    try:
        atr = fetch_atr()
        if atr:
            _cache["atr"] = atr
            _cache["ts"] = now
            return atr, "polygon"
    except Exception as e:
        print(f"Fetch failed: {e}")
    return None, None

@app.route("/atr")
def atr_endpoint():
    val, source = get_atr()
    if val is None:
        return jsonify({"error": "Failed to fetch ATR"}), 500
    return jsonify({"atr": val, "source": source, "symbol": "XAU/USD", "period": 14, "interval": "1m"})

@app.route("/")
def home():
    return jsonify({"status": "ok", "mess
