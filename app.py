from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests as req

app = Flask(__name__)

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
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestvideo+bestaudio/best",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        seen = set()

        for f in (info.get("formats") or []):
            furl = f.get("url", "")
            height = f.get("height")
            acodec = f.get("acodec", "none")
            vcodec = f.get("vcodec", "none")
            ext = f.get("ext", "mp4")
            tbr = f.get("tbr") or 0

            if not furl:
                continue

            if vcodec != "none" and height:
                label = f"{height}p"
                ftype = "video"
            elif acodec != "none" and vcodec == "none":
                label = f"Audio ({ext.upper()})"
                ftype = "audio"
            else:
                continue

            key = f"{label}_{round(tbr)}"
            if key in seen:
                continue
            seen.add(key)

            size = f.get("filesize") or f.get("filesize_approx")
            size_str = f"{round(size/1024/1024)}MB" if size else "—"

            http_headers = f.get("http_headers", {})

            formats.append({
                "label": label,
                "ext": ext.upper(),
                "size": size_str,
                "type": ftype,
                "url": f"/api/proxy?url={req.utils.quote(furl)}",
                "headers": http_headers,
                "tbr": tbr
            })

        formats.sort(key=lambda x: (
            0 if x["type"] == "video" else 1,
            -(int(x["label"].replace("p","")) if x["type"] == "video" and x["label"].endswith("p") else x.get("tbr",0))
        ))

        for f in formats:
            f.pop("tbr", None)
            f.pop("headers", None)

        res = jsonify({
            "title": info.get("title", "بدون عنوان"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration_string", ""),
            "platform": info.get("extractor_key", "Unknown"),
            "formats": formats[:10]
        })
        res.headers["Access-Control-Allow-Origin"] = "*"
        return res

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/proxy")
def proxy():
    url = request.args.get("url", "")
    if not url:
        return "No URL", 400
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.youtube.com/",
        }
        r = req.get(url, headers=headers, stream=True, timeout=60)
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk
        return Response(
            generate(),
            content_type=r.headers.get("Content-Type", "video/mp4"),
            headers={"Content-Disposition": "attachment; filename=video.mp4"}
        )
    except Exception as e:
        return str(e), 500
