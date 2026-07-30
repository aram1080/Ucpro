import os
import random
import requests
import logging
from flask import Flask, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# معتبرترین منابع کانفیگ VPN
V2RAY_SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_raw.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub_Combine.txt",
]

# منابع پروکسی تلگرام
TG_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/mtproto",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/socks",
]

cached_configs = {"vless": [], "vmess": [], "trojan": [], "ss": [], "tg_proxy": []}

@app.route('/')
def home():
    return 'Bot is running!'

@app.route('/health')
def health():
    return 'OK', 200

def send_message(chat_id, text):
    try:
        requests.post(f"{TG_API}/sendMessage", json={
            "chat_id": chat_id, "text": text, "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        logger.error(f"Send error: {e}")

def fetch_configs():
    all_lines = []
    for url in V2RAY_SOURCES:
        try:
            r = requests.get(url, timeout=15)
            for line in r.text.strip().split("\n"):
                line = line.strip()
                if line.startswith(("vless://", "vmess://", "trojan://", "ss://")):
                    all_lines.append(line)
        except Exception as e:
            logger.error(f"Error: {url} - {e}")

    # حذف تکراری و دسته‌بندی
    seen = set()
    cached_configs["vless"] = []
    cached_configs["vmess"] = []
    cached_configs["trojan"] = []
    cached_configs["ss"] = []

    for line in all_lines:
        if line in seen:
            continue
        seen.add(line)
        if line.startswith("vless://"):
            cached_configs["vless"].append(line)
        elif line.startswith("vmess://"):
            cached_configs["vmess"].append(line)
        elif line.startswith("trojan://"):
            cached_configs["trojan"].append(line)
        elif line.startswith("ss://"):
            cached_configs["ss"].append(line)

    # پروکسی تلگرام
    cached_configs["tg_proxy"] = []
    for url in TG_PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            for line in r.text.strip().split("\n"):
                line = line.strip()
                if line.startswith("tg://proxy"):
                    cached_configs["tg_proxy"].append(line)
        except:
            pass

    total = sum(len(v) for v in cached_configs.values())
    logger.info(f"Loaded: VLESS={len(cached_configs['vless'])} VMess={len(cached_configs['vmess'])} "
                f"Trojan={len(cached_configs['trojan'])} SS={len(cached_configs['ss'])} "
                f"TG_Proxy={len(cached_configs['tg_proxy'])} Total={total}")
    return total

def get_random(count, config_type=None):
    if config_type:
        pool = cached_configs.get(config_type, [])
    else:
        pool = []
        for v in cached_configs.values():
            pool.extend(v)
    if not pool:
        return []
    return random.sample(pool, min(count, len(pool)))

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return 'OK', 200

    msg = data["message"]
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")

    if not chat_id or not text:
        return 'OK', 200

    logger.info(f"{text} from {chat_id}")

    if text == "/start":
        send_message(chat_id,
            "🟢 ربات VPN UC\n"
            "کانفیگ‌های رایگان مخصوص ایران\n\n"
            "📡 V2Ray:\n"
            "/vless - کانفیگ VLESS\n"
            "/vmess - کانفیگ VMESS\n"
            "/trojan - کانفیگ Trojan\n"
            "/ss - کانفیگ Shadowsocks\n\n"
            "🔗 پروکسی تلگرام:\n"
            "/tgproxy - پروکسی تلگرام\n\n"
            "🎲 سایر:\n"
            "/random - کانفیگ تصادفی\n"
            "/fast ۵ - چند کانفیگ\n"
            "/refresh - بروزرسانی\n"
            "/count - تعداد\n\n"
            "📌 نحوه استفاده:\n"
            "۱. کانفیگ رو کپی کن\n"
            "۲. در v2rayNG یا Hiddify اضافه کن\n"
            "۳. وصل شو! ✅"
        )

    elif text == "/vless":
        if not cached_configs["vless"]:
            fetch_configs()
        items = get_random(5, "vless")
        if items:
            lines = f"🟢 VLESS ({len(cached_configs['vless'])} کانفیگ موجود):\n\n"
            for i, c in enumerate(items, 1):
                lines += f"📌 {i}:\n<code>{c}</code>\n\n"
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ کانفیگی پیدا نشد. /refresh بزن.")

    elif text == "/vmess":
        if not cached_configs["vmess"]:
            fetch_configs()
        items = get_random(5, "vmess")
        if items:
            lines = f"🔵 VMESS ({len(cached_configs['vmess'])} کانفیگ موجود):\n\n"
            for i, c in enumerate(items, 1):
                lines += f"📌 {i}:\n<code>{c}</code>\n\n"
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ کانفیگی پیدا نشد. /refresh بزن.")

    elif text == "/trojan":
        if not cached_configs["trojan"]:
            fetch_configs()
        items = get_random(5, "trojan")
        if items:
            lines = f"🔴 Trojan ({len(cached_configs['trojan'])} کانفیگ موجود):\n\n"
            for i, c in enumerate(items, 1):
                lines += f"📌 {i}:\n<code>{c}</code>\n\n"
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ کانفیگی پیدا نشد. /refresh بزن.")

    elif text == "/ss":
        if not cached_configs["ss"]:
            fetch_configs()
        items = get_random(5, "ss")
        if items:
            lines = f"🟡 Shadowsocks ({len(cached_configs['ss'])} کانفیگ موجود):\n\n"
            for i, c in enumerate(items, 1):
                lines += f"📌 {i}:\n<code>{c}</code>\n\n"
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ کانفیگی پیدا نشد. /refresh بزن.")

    elif text == "/tgproxy":
        if not cached_configs["tg_proxy"]:
            fetch_configs()
        items = get_random(5, "tg_proxy")
        if items:
            lines = f"🔗 پروکسی تلگرام ({len(cached_configs['tg_proxy'])} موجود):\n\n"
            for i, c in enumerate(items, 1):
                lines += f'{i}. <a href="{c}">🔗 اضافه کن</a>\n'
            lines += "\n👆 روی لینک بزن تا مستقیم اضافه بشه"
            send_message(chat_id, lines)
        else:
            send_message(chat_id,
                "❌ پروکسی تلگرام پیدا نشد.\n"
                "از /vless یا /vmess استفاده کن\n"
                "و در v2rayNG اضافه کن."
            )

    elif text == "/random":
        items = get_random(3)
        if items:
            lines = "🎲 کانفیگ تصادفی:\n\n"
            for i, c in enumerate(items, 1):
                if c.startswith("vless://"):
                    t = "VLESS"
                elif c.startswith("vmess://"):
                    t = "VMESS"
                elif c.startswith("trojan://"):
                    t = "Trojan"
                else:
                    t = "SS"
                lines += f"📌 {i} ({t}):\n<code>{c}</code>\n\n"
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ لیست خالیه. /refresh بزن.")

    elif text.startswith("/fast"):
        parts = text.split()
        count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
        count = min(count, 10)
        items = get_random(count)
        if items:
            lines = f"⚡ {count} کانفیگ:\n\n"
            for i, c in enumerate(items, 1):
                if c.startswith("vless://"):
                    t = "VLESS"
                elif c.startswith("vmess://"):
                    t = "VMESS"
                elif c.startswith("trojan://"):
                    t = "Trojan"
                else:
                    t = "SS"
                lines += f"📌 {i} ({t}):\n<code>{c}</code>\n\n"
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ لیست خالیه. /refresh بزن.")

    elif text == "/refresh":
        send_message(chat_id, "🔄 در حال بروزرسانی...")
        total = fetch_configs()
        send_message(chat_id,
            f"✅ بروزرسانی شد!\n\n"
            f"🟢 VLESS: {len(cached_configs['vless'])}\n"
            f"🔵 VMESS: {len(cached_configs['vmess'])}\n"
            f"🔴 Trojan: {len(cached_configs['trojan'])}\n"
            f"🟡 SS: {len(cached_configs['ss'])}\n"
            f"🔗 TG Proxy: {len(cached_configs['tg_proxy'])}\n"
            f"📊 کل: {total}"
        )

    elif text == "/count":
        total = sum(len(v) for v in cached_configs.values())
        send_message(chat_id,
            f"📊 تعداد کانفیگ‌ها:\n\n"
            f"🟢 VLESS: {len(cached_configs['vless'])}\n"
            f"🔵 VMESS: {len(cached_configs['vmess'])}\n"
            f"🔴 Trojan: {len(cached_configs['trojan'])}\n"
            f"🟡 SS: {len(cached_configs['ss'])}\n"
            f"🔗 TG Proxy: {len(cached_configs['tg_proxy'])}\n"
            f"📊 کل: {total}"
        )

    return 'OK', 200

def setup_webhook():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        return
    railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    if railway_url:
        webhook_url = f"https://{railway_url}/webhook"
        try:
            r = requests.get(f"{TG_API}/setWebhook?url={webhook_url}", timeout=10)
            logger.info(f"Webhook set: {r.json()}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")

if __name__ == "__main__":
    logger.info("Starting UC VPN Bot...")
    setup_webhook()
    fetch_configs()
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Running on port {port}")
    app.run(host='0.0.0.0', port=port)
