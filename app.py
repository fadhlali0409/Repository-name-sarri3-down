from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

COBALT_API = "https://api.cobalt.tools/"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/download", methods=["POST", "OPTIONS"])
def download():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response, 200

    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "الرابط مطلوب"}), 400

    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # جرب جودات مختلفة
        qualities = ["1080", "720", "480", "360"]
        results = []

        for q in qualities:
            try:
                res = requests.post(COBALT_API, json={
                    "url": url,
                    "videoQuality": q,
                    "filenameStyle": "pretty"
                }, headers=headers, timeout=15)

                if res.status_code == 200:
                    d = res.json()
                    if d.get("status") in ["stream", "redirect", "tunnel"] and d.get("url"):
                        results.append({
                            "label": f"{q}p",
                            "ext": "MP4",
                            "size": "—",
                            "type": "video",
                            "url": d["url"]
                        })
            except:
                continue

        # أضف خيار الصوت
        try:
            res = requests.post(COBALT_API, json={
                "url": url,
                "downloadMode": "audio",
                "audioFormat": "mp3",
                "filenameStyle": "pretty"
            }, headers=headers, timeout=15)

            if res.status_code == 200:
                d = res.json()
                if d.get("status") in ["stream", "redirect", "tunnel"] and d.get("url"):
                    results.append({
                        "label": "Audio",
                        "ext": "MP3",
                        "size": "—",
                        "type": "audio",
                        "url": d["url"]
                    })
        except:
            pass

        if not results:
            return jsonify({"error": "تعذّر تحليل الرابط، جرب رابطاً آخر"}), 400

        # احذف المكررات
        seen = set()
        unique = []
        for f in results:
            if f["url"] not in seen:
                seen.add(f["url"])
                unique.append(f)

        response = jsonify({
            "title": "جاهز للتحميل",
            "thumbnail": "",
            "duration": "",
            "platform": "Auto",
            "formats": unique
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500
