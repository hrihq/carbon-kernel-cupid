import urllib.request, json, os

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")
zip_name = os.environ.get("ZIP_NAME", "Carbon-Kernel.zip")
rel_tag = os.environ.get("REL_TAG", "v1.2")
banner_path = "branding/banner.jpg"

caption = """Carbon Kernel v1.2 - Cygnus-X1
Device: Xiaomi 12 (cupid)
Maintainer: @kuroya14

Information:
- Linux 5.10.269 GKI
- Support Android 14 to 17 AOSP
- KernelSU-Next v3.4.2 + SUSFS v2.3.0
- Dual Variant: Vol+ Root | Vol- Non-Root
- Fast Charging Floor: Prevent drop to 2W
- WALT Scheduler: Fix scrolling overheat
- Anti-Stutter memory tweaks
- Clang 22.0.2 r596125 Full LTO"""

release_url = f"https://github.com/hrihq/carbon-kernel-cupid/releases"
guide_url = "https://telegra.ph/Carbon-Kernel-v12-Cygnus-X1-Guide-and-Changelog-10-23"

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
