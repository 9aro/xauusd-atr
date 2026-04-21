from flask import Flask, jsonify
import requests
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

_cache = {"atr": None, "ts": 0}
CACHE_TTL = 60

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
    return round(atr, 2)

def fetch_from_twelvedata():
    url = "https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&outputsize=500&apikey=c48c422fd1744197b804c436036e6315"
    r = requests.get(url, timeout=15)
    d = r.json()
    candles = list(reversed(d["values"]))
    highs  = [float(c["high"])  for c in candles]
    lows   = [float(c["low"])   for c in candles]
    closes = [float(c["close"]) for c in candles]
    return compute_wilder_atr(highs, lows, closes)

def fetch_from_yahoo():
    url = "https://query2.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=5d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://finance.yahoo.com/"
    }
    r = requests.get(url, headers=headers, timeout=15)
    data = r.json()
    q = data["chart"]["result"][0]["indicators"]["quote"][0]
    filtered = [(h,l,c) for h,l,c in zip(q["high"],q["low"],q["close"]) if h and l and c]
    highs  = [x[0] for x in filtered]
    lows   = [x[1] for x in filtered]
    closes = [x[2] for x in filtered]
    return compute_wilder_atr(highs, lows, closes)

def get_atr():
    now = time.time()
    if _cache["atr"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["atr"], "cache"
    try:
        atr = fetch_from_yahoo()
        if atr:
            _cache["atr"] = atr
            _cache["ts"] = now
            return atr, "yahoo"
    except Exception as e:
        print(f"Yahoo failed: {e}")
    try:
        atr = fetch_from_twelvedata()
        if atr:
            _cache["atr"] = atr
            _cache["ts"] = now
            return atr, "twelvedata"
    except Exception as e:
        print(f"TD failed: {e}")
    return None, None

@app.route("/atr")
def atr_endpoint():
    val, source = get_atr()
    if val is None:
        return jsonify({"error": "Failed to fetch ATR"}), 500
    return jsonify({"atr": val, "source": source, "symbol": "GC=F", "period": 14, "interval": "1m"})

@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "XAUUSD ATR API"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
