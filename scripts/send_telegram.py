import urllib.request, json, os

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")
rel_tag = os.environ.get("REL_TAG", "v1.6-Cupid")

# Get changelog from CHANGELOG.md
changelog = ""
try:
    with open("CHANGELOG.md") as f:
        changelog = f.read().strip()
except:
    changelog = "Carbon Kernel v1.6-Cupid for Xiaomi 12 (cupid)"

caption = "Carbon Kernel v1.6-Cupid\nDevice: Xiaomi 12 (cupid)\nMaintainer: @kuroya14\n\nNew in v1.6:\n" + changelog + "\n\nDownload: https://github.com/hrihq/carbon-kernel-cupid/releases/tag/" + rel_tag

release_url = "https://github.com/hrihq/carbon-kernel-cupid/releases/tag/" + rel_tag

reply_markup = {
    "inline_keyboard": [
        [{"text": "Download", "url": release_url}]
    ]
}

if not bot_token or not chat_id:
    print("Telegram secrets missing. Skipping notification.")
    exit(0)

payload = json.dumps({"chat_id": chat_id, "text": caption, "reply_markup": reply_markup}).encode()
req = urllib.request.Request("https://api.telegram.org/bot" + bot_token + "/sendMessage", data=payload, headers={"Content-Type": "application/json"})

try:
    res = json.loads(urllib.request.urlopen(req).read().decode())
    print("Telegram notification sent successfully!", res.get("ok"))
except Exception as e:
    print("Failed to send Telegram notification:", e)
