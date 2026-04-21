from flask import Flask, jsonify
import requests
import time
from flask_cors import CORS

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
    now = time.gmtime()
    today = "%04d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
    epoch_3days_ago = time.time() - (3 * 24 * 3600)
    past = time.gmtime(epoch_3days_ago)
    from_date = "%04d-%02d-%02d" % (past.tm_year, past.tm_mon, past.tm_mday)
    url = (
        "https://api.polygon.io/v2/aggs/ticker/C:XAUUSD/range/1/minute"
        "/" + from_date + "/" + today + "?sort=asc&limit=500&apiKey=" + API_KEY
    )
    print("Fetching: " + url)
    r = requests.get(url, timeout=15)
    d = r.json()
    print("Polygon status: " + str(d.get("status")) + " count: " + str(d.get("resultsCount")))
    results = d.get("results", [])
    if not results:
        raise Exception("No results: " + str(d))
    atr = compute_wilder_atr(results)
    print("ATR: " + str(atr))
    return atr

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
        print("Fetch failed: " + str(e))
    return None, None

@app.route("/atr")
def atr_endpo
