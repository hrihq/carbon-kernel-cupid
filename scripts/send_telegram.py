import urllib.request, json, os

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")
zip_name = os.environ.get("ZIP_NAME", "Carbon-Kernel.zip")
rel_tag = os.environ.get("REL_TAG", "v1.4")
banner_path = "branding/banner.jpg"

caption = """Carbon Kernel v1.4 - Phoenix A
Device: Xiaomi 12 (cupid)
Maintainer: @kuroya14

New in v1.4:
- Auto Disable Charging Thermal Throttle: No drop to 2W when battery warm
- WALT Fast Core Release: 1000ms coloc hysteresis for Snapdragon 8 Gen 1
- Faster Task Downmigrate: Rapidly shifts load back to Little A510 cores
- Bidirectional TCP Fast Open: Lower networking and gaming latency"""

release_url = f"https://github.com/hrihq/carbon-kernel-cupid/releases/tag/{rel_tag}"
guide_url = "https://telegra.ph/Carbon-Kernel-v14---Phoenix-A-Guide-and-Changelog-10-24"

reply_markup = {
    "inline_keyboard": [
        [
            {"text": "Download", "url": release_url},
            {"text": "Changelog and Guide", "url": guide_url}
        ]
    ]
}

if not bot_token or not chat_id:
    print("Telegram secrets missing. Skipping notification.")
    exit(0)

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = bytearray()

def add_field(name, value):
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())

add_field("chat_id", chat_id)
add_field("caption", caption)
add_field("reply_markup", json.dumps(reply_markup))

if os.path.exists(banner_path):
    with open(banner_path, "rb") as f:
        photo_bytes = f.read()
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"banner.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode())
    body.extend(photo_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
else:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    headers = {"Content-Type": "application/json"}
    body = json.dumps({"chat_id": chat_id, "text": caption, "reply_markup": reply_markup}).encode()

req = urllib.request.Request(url, data=bytes(body), headers=headers)
try:
    res = json.loads(urllib.request.urlopen(req).read().decode())
    print("Telegram notification sent successfully!", res.get("ok"))
except Exception as e:
    print("Failed to send Telegram notification:", e)
