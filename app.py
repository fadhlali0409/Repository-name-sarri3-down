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

        # قائمة الطلبات حسب كل منصة
        requests_list = [
            # فيديو جودات مختلفة
            {"url": url, "videoQuality": "1080", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "720", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "480", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "360", "filenameStyle": "pretty"},
            # صوت
            {"url": url, "downloadMode": "audio", "audioFormat": "mp3", "filenameStyle": "pretty"},
            # فيديو بدون صوت مدمج
            {"url": url, "downloadMode": "mute", "filenameStyle": "pretty"},
        ]

        seen_urls = set()

        for payload in requests_list:
            try:
                r = req.post(
                    f"{COBALT_API}/",
                    json=payload,
                    headers=headers,
                    timeout=20
                )
                if r.status_code != 200:
                    continue

                d = r.json()
                status = d.get("status", "")

                if status == "picker":
                    # للمنصات التي ترجع خيارات متعددة
                    for item in (d.get("picker") or []):
                        item_url = item.get("url", "")
                        if item_url and item_url not in seen_urls:
                            seen_urls.add(item_url)
                            formats.append({
                                "label": "فيديو",
                                "ext": "MP4",
                                "size": "—",
                                "type": "video",
                                "url": item_url
                            })

                elif status in ["stream", "redirect", "tunnel"]:
                    dl_url = d.get("url") or d.get("stream")
                    if dl_url and dl_url not in seen_urls:
                        seen_urls.add(dl_url)
                        is_audio = payload.get("downloadMode") == "audio"
                        quality = payload.get("videoQuality", "")
                        label = "Audio MP3" if is_audio else (f"{quality}p" if quality else "فيديو")
                        formats.append({
                            "label": label,
                            "ext": "MP3" if is_audio else "MP4",
                            "size": "—",
                            "type": "audio" if is_audio else "video",
                            "url": dl_url
                        })

            except:
                continue

        if not formats:
            return jsonify({"error": "تعذّر تحليل الرابط، جرب رابطاً آخر"}), 400

        res = jsonify({
            "title": "جاهز للتحميل",
            "thumbnail": "",
            "duration": "",
            "platform": "Auto",
            "formats": formats[:10]
        })
        res.headers["Access-Control-Allow-Origin"] = "*"
        return res

    except Exception as e:
        return jsonify({"error": str(e)}), 500
