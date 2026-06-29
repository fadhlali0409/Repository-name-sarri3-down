from flask import Flask, render_template, request, jsonify
import requests as req
import yt_dlp

app = Flask(__name__)

COBALT_API = "https://cobalt-production-712b.up.railway.app"

def resolve_url(url):
    # تحويل الروابط المختصرة للروابط الكاملة
    try:
        r = req.get(url, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url

def get_meta(url):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "جاهز للتحميل"),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration_string", ""),
                "platform": info.get("extractor_key", "Auto")
            }
    except:
        return {"title": "جاهز للتحميل", "thumbnail": "", "duration": "", "platform": "Auto"}

def try_cobalt(url):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    is_youtube = "youtube.com" in url or "youtu.be" in url

    if is_youtube:
        payloads = [
            {"url": url, "videoQuality": "1080", "youtubeVideoCodec": "h264", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "720", "youtubeVideoCodec": "h264", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "480", "youtubeVideoCodec": "h264", "filenameStyle": "pretty"},
            {"url": url, "downloadMode": "audio", "audioFormat": "mp3", "filenameStyle": "pretty"},
        ]
    else:
        payloads = [
            {"url": url, "videoQuality": "1080", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "720", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "480", "filenameStyle": "pretty"},
            {"url": url, "videoQuality": "360", "filenameStyle": "pretty"},
            {"url": url, "downloadMode": "audio", "audioFormat": "mp3", "filenameStyle": "pretty"},
        ]

    formats = []
    seen = set()

    for payload in payloads:
        try:
            r = req.post(f"{COBALT_API}/", json=payload, headers=headers, timeout=20)
            if r.status_code != 200:
                continue
            d = r.json()
            status = d.get("status", "")

            if status == "picker":
                for item in (d.get("picker") or []):
                    u = item.get("url", "")
                    if u and u not in seen:
                        seen.add(u)
                        formats.append({
                            "label": "فيديو",
                            "ext": "MP4",
                            "size": "—",
                            "type": "video",
                            "url": u
                        })

            elif status in ["stream", "redirect", "tunnel"]:
                u = d.get("url") or d.get("stream")
                if u and u not in seen:
                    seen.add(u)
                    is_audio = payload.get("downloadMode") == "audio"
                    q = payload.get("videoQuality", "")
                    formats.append({
                        "label": "Audio MP3" if is_audio else (f"{q}p" if q else "فيديو"),
                        "ext": "MP3" if is_audio else "MP4",
                        "size": "—",
                        "type": "audio" if is_audio else "video",
                        "url": u
                    })
        except:
            continue

    return formats

def try_ytdlp(url):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        formats = []
        seen = set()
        for f in (info.get("formats") or []):
            furl = f.get("url", "")
            height = f.get("height")
            acodec = f.get("acodec", "none")
            vcodec = f.get("vcodec", "none")
            ext = f.get("ext", "mp4")
            if not furl:
                continue
            if vcodec != "none" and acodec != "none" and height:
                label = f"{height}p"
                ftype = "video"
            elif acodec != "none" and vcodec == "none":
                label = f"Audio ({ext.upper()})"
                ftype = "audio"
            else:
                continue
            if label not in seen:
                seen.add(label)
                formats.append({
                    "label": label,
                    "ext": ext.upper(),
                    "size": "—",
                    "type": ftype,
                    "url": furl
                })
        formats.sort(key=lambda x: (
            0 if x["type"] == "video" else 1,
            -(int(x["label"].replace("p","")) if x["type"] == "video" and x["label"].endswith("p") else 0)
        ))
        return formats[:8]
    except:
        return []

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
        # تحويل الروابط المختصرة
        if any(x in url for x in ["fb.watch", "bit.ly", "t.co", "tinyurl"]):
            url = resolve_url(url)

        # جلب معلومات الفيديو
        meta = get_meta(url)

        # جرب Cobalt أولاً
        formats = try_cobalt(url)

        # إذا فشل جرب yt-dlp
        if not formats:
            formats = try_ytdlp(url)

        if not formats:
            return jsonify({"error": "تعذّر تحليل الرابط، جرب رابطاً آخر"}), 400

        res = jsonify({
            "title": meta["title"],
            "thumbnail": meta["thumbnail"],
            "duration": meta["duration"],
            "platform": meta["platform"],
            "formats": formats[:10]
        })
        res.headers["Access-Control-Allow-Origin"] = "*"
        return res

    except Exception as e:
        return jsonify({"error": str(e)}), 500
