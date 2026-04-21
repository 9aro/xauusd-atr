from flask import Flask, jsonify, request
import requests
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TWELVE_KEY = "0236a5701f2e4e7399c67d452984516b"
_cache = {"atr": None, "ts": 0}
_correction = {"factor": 1.0}

def fetch_raw_atr():
    url = "https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&outputsize=500&apikey=" + TWELVE_KEY
    resp = requests.get(url, timeout=15)
    data = resp.json()
    candles = list(reversed(data["values"]))
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    closes = [float(c["close"]) for c in candles]
    trs = []
    for i in range(1, len(candles)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    atr = sum(trs[:14]) / 14
    for i in range(14, len(trs)):
        atr = (atr * 13 + trs[i]) / 14
    return round(atr, 4)

def get_atr():
    now = time.time()
    if _cache["atr"] and (now - _cache["ts"]) < 60:
        return round(_cache["atr"] * _correction["factor"], 2), "cache", int(now - _cache["ts"])
    raw = fetch_raw_atr()
    _cache["atr"] = raw
    _cache["ts"] = time.time()
    return round(raw * _correction["factor"], 2), "twelvedata", 0

@app.route("/atr")
def atr_endpoint():
    try:
        val, source, age = get_atr()
        return jsonify({"atr": val, "raw": _cache["atr"], "source": source, "age": age, "correction": _correction["factor"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/calibrate", methods=["POST"])
def calibrate():
    try:
        tv_atr = float(request.json.get("tv_atr", 0))
        if tv_atr <= 0:
            return jsonify({"error": "invalid"}), 400
        raw = _cache["atr"] or fetch_raw_atr()
        _cache["atr"] = raw
        _cache["ts"] = time.time()
        factor = round(tv_atr / raw, 4)
        _correction["factor"] = factor
        return jsonify({"tv_atr": tv_atr, "raw_atr": raw, "correction_factor": factor})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
