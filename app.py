from flask import Flask, jsonify
import requests
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

_cache = {"atr": None, "ts": 0}
CACHE_TTL = 60

CORRECTION = 1.34

def compute_wilder_atr(highs, lows, closes, period=14):
    trs = []
    for i in range(1, len(highs)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        return None
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period-1) + trs[i]) / period
    return round(atr * CORRECTION, 2)

def fetch_atr():
    url = "https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&outputsize=500&apikey=c48c422fd1744197b804c436036e6315"
    r = requests.get(url, timeout=15)
    d = r.json()
    candles = list(reversed(d["values"]))
    highs  = [float(c["high"])  for c in candles]
    lows   = [float(c["low"])   for c in candles]
    closes = [float(c["close"]) for c in candles]
    return compute_wilder_atr(highs, lows, closes)

def get_atr():
    now = time.time()
    if _cache["atr"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["atr"], "cache"
    try:
        atr = fetch_atr()
        if atr:
            _cache["atr"] = atr
            _cache["ts"] = now
            return atr, "twelvedata"
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
    return jsonify({"status": "ok", "message": "XAUUSD ATR API"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
