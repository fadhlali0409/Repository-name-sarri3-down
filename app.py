from flask import Flask, render_template, request, jsonify
import requests as req

app = Flask(__name__)

RAPIDAPI_KEY = "a5ae9ead30msh2f29ecfb811f6dap1c7b51jsncc3045951bc0"
RAPIDAPI_HOST = "auto-download-all-in-one.p.rapidapi.com"

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
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }

        response = req.post(
            "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink",
            json={"url": url},
            headers=headers,
            timeout=30
        )

        result = response.json()

        if response.status_code != 200 or not result:
            return jsonify({"error": "تعذّر تحليل الرابط"}), 400

        formats = []
        medias = result.get("medias", [])

        for i, m in enumerate(medias[:10]):
            murl = m.get("url", "")
            quality = m.get("quality", "")
            ext = m.get("extension", "mp4")
            size = m.get("size", 0)

            if not murl:
                continue

            label = quality if quality else f"خيار {i+1}"
            size_str = f"{round(size/1024/1024)}MB" if size else "—"
            ftype = "audio" if ext in ["mp3", "m4a", "aac"] else "video"

            formats.append({
                "label": label,
                "ext": ext.upper(),
                "size": size_str,
                "type": ftype,
                "url": murl
            })

        if not formats:
            return jsonify({"error": "لا توجد صيغ متاحة"}), 400

        res = jsonify({
            "title": result.get("title", "بدون عنوان"),
            "thumbnail": result.get("thumbnail", ""),
            "duration": result.get("duration", ""),
            "platform": result.get("source", "Unknown"),
            "formats": formats
        })
        res.headers["Access-Control-Allow-Origin"] = "*"
        return res

    except Exception as e:
        return jsonify({"error": str(e)}), 500
