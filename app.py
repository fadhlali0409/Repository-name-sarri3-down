from flask import Flask, render_template, request, jsonify
import yt_dlp

app = Flask(__name__)

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
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        seen = set()

        for f in (info.get("formats") or []):
            furl = f.get("url", "")
            height = f.get("height")
            acodec = f.get("acodec", "none")
            vcodec = f.get("vcodec", "none")
            ext = f.get("ext", "")

            if not furl or furl in seen:
                continue
            seen.add(furl)

            if vcodec != "none" and height:
                label = f"{height}p"
                ftype = "video"
            elif acodec != "none" and vcodec == "none":
                label = f"Audio ({ext.upper()})"
                ftype = "audio"
            else:
                continue

            size = f.get("filesize") or f.get("filesize_approx")
            size_str = f"{round(size/1024/1024)}MB" if size else "—"

            formats.append({
                "label": label,
                "ext": ext.upper(),
                "size": size_str,
                "type": ftype,
                "url": furl
            })

        formats.sort(key=lambda x: (
            0 if x["type"] == "video" else 1,
            -(int(x["label"].replace("p","")) if x["type"] == "video" and x["label"].endswith("p") else 0)
        ))

        response = jsonify({
            "title": info.get("title", "بدون عنوان"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration_string", ""),
            "platform": info.get("extractor_key", "Unknown"),
            "formats": formats[:10]
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500
