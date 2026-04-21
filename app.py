from flask import Flask, jsonify
import requests
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

POLYGON_KEY = "bgH0QPcnGgwSFPBib3TpGdfVpylpC3Bu"
_cache = {"atr": None, "ts": 0}

def get_atr_from_polygon():
    now = time.gmtime()
    today = "%04d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
    past = time.gmtime(time.time() - 3 * 24 * 3600)
    from_date = "%04d-%02d-%02d" % (past.tm_year, past.tm_mon, past.tm_mday)
    url = "https://api.polygon.io/v2/aggs/ticker/C:XAUUSD/range/1/minute/" + from_date + "/" + today + "?sort=asc&limit=500&apiKey=" + POLYGON_KEY
    resp = requests.get(url, timeout=15)
    data = resp.json()
    candles = data.get("results", [])
    if len(candles) < 15:
        return None
    highs  = [c["h"] for c in candles]
    lows   = [c["l"] for c in candles]
    closes = [c["c"] for c in candles]
    trs = []
    for i in range(1, len(candles)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    atr = sum(trs[:14]) / 14
    for i in range(14, len(trs)):
        atr = (atr * 13 + trs[i]) / 14
    return round(atr, 2)

@app.route("/atr")
def atr():
    now = time.time()
    if _cache["atr"] and (now - _cache["ts"]) < 60:
        return jsonify({"atr": _cache["atr"], "source": "cache", "age": int(now - _cache["ts"])})
    try:
        val = get_atr_from_polygon()
        if val:
            _cache["atr"] = val
            _cache["ts"] = time.time()
            return jsonify({"atr": val, "source": "polygon"})
        return jsonify({"error": "no data"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
