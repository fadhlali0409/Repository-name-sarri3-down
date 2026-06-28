from flask import Flask, render_template, request, jsonify
import requests as req

app = Flask(__name__)

COBALT_API = "https://cobalt-production-712b.up.railway.app"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/download", methods=["POST", "OPTIONS"])
def download():
    if request.method == "OPTIONS":
        res = jsonify({})
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return res, 200

    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "الرابط مطلوب"}), 400

    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        formats = []

        # جرب جودات مختلفة
        for quality in ["1080", "720", "480", "360"]:
            try:
                r = req.post(
                    f"{COBALT_API}/",
                    json={"url": url, "videoQuality": quality, "filenameStyle": "pretty"},
                    headers=headers,
                    timeout=20
                )
                if r.status_code == 200:
                    d = r.json()
                    status = d.get("status", "")
                    dl_url = d.get("url") or d.get("stream")
                    if status in ["stream", "redirect", "tunnel", "picker"] and dl_url:
                        formats.append({
                            "label": f"{quality}p",
                            "ext": "MP4",
                            "size": "—",
                            "type": "video",
                            "url": dl_url
                        })
                        break
            except:
                continue

        # أضف خيار الصوت
        try:
            r = req.post(
                f"{COBALT_API}/",
                json={"url": url, "downloadMode": "audio", "audioFormat": "mp3", "filenameStyle": "pretty"},
                headers=headers,
                timeout=20
            )
            if r.status_code == 200:
                d = r.json()
                dl_url = d.get("url") or d.get("stream")
                if dl_url:
                    formats.append({
                        "label": "Audio MP3",
                        "ext": "MP3",
                        "size": "—",
                        "type": "audio",
                        "url": dl_url
                    })
        except:
            pass

        if not formats:
            return jsonify({"error": "تعذّر تحليل الرابط، جرب رابطاً آخر"}), 400

        res = jsonify({
            "title": "جاهز للتحميل",
            "thumbnail": "",
            "duration": "",
            "platform": "Auto",
            "formats": formats
        })
        res.headers["Access-Control-Allow-Origin"] = "*"
        return res

    except Exception as e:
        return jsonify({"error": str(e)}), 500
