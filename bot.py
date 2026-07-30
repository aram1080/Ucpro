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

PROXY_LISTS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

cached_proxies = {"socks5": [], "http": []}

@app.route('/')
def home():
    return 'Bot is running!'

@app.route('/health')
def health():
    return 'OK', 200

def send_message(chat_id, text, reply_markup=None):
    try:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Send error: {e}")

def make_proxy_link(proxy, proxy_type):
    try:
        ip, port = proxy.split(":")
        port = int(port)
        if proxy_type == "socks5":
            return f"tg://proxy?server={ip}&port={port}"
        else:
            return f"http://t.me/proxy?server={ip}&port={port}"
    except:
        return None

def fetch_proxies():
    socks5 = []
    http = []
    for url in PROXY_LISTS:
        try:
            r = requests.get(url, timeout=10)
            lines = r.text.strip().split("\n")
            for line in lines:
                line = line.strip()
                if ":" in line and len(line) < 30:
                    parts = line.split(":")
                    if len(parts) == 2:
                        try:
                            int(parts[1])
                            if "socks5" in url:
                                socks5.append(line)
                            else:
                                http.append(line)
                        except:
                            continue
        except:
            continue
    cached_proxies["socks5"] = socks5[:200]
    cached_proxies["http"] = http[:200]
    logger.info(f"Loaded: {len(socks5)} socks5, {len(http)} http")
    return socks5, http

def test_proxy(proxy, proxy_type="socks5"):
    try:
        if proxy_type == "socks5":
            proxies = {"https": f"socks5://{proxy}", "http": f"socks5://{proxy}"}
        else:
            proxies = {"https": f"http://{proxy}", "http": f"http://{proxy}"}
        r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
        if r.status_code == 200:
            return True, r.json().get("origin", "")
    except:
        pass
    return False, None

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
            "🟢 ربات پروکسی UC\n\n"
            "دستورات:\n"
            "/socks5 - لیست SOCKS5\n"
            "/http - لیست HTTP\n"
            "/fast - سریع‌ترین پروکسی‌ها\n"
            "/refresh - بروزرسانی لیست\n"
            "/count - تعداد پروکسی‌ها"
        )

    elif text == "/socks5":
        if not cached_proxies["socks5"]:
            fetch_proxies()
        proxies = cached_proxies["socks5"][:10]
        if proxies:
            lines = "🟢 SOCKS5 Proxy:\n\n"
            for i, p in enumerate(proxies, 1):
                link = make_proxy_link(p, "socks5")
                if link:
                    lines += f'{i}. <a href="{link}">🟢 {p}</a> - اضافه کن ✅\n'
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ لیست خالیه. /refresh بزن.")

    elif text == "/http":
        if not cached_proxies["http"]:
            fetch_proxies()
        proxies = cached_proxies["http"][:10]
        if proxies:
            lines = "🔵 HTTP Proxy:\n\n"
            for i, p in enumerate(proxies, 1):
                link = make_proxy_link(p, "http")
                if link:
                    lines += f'{i}. <a href="{link}">🔵 {p}</a> - اضافه کن ✅\n'
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ لیست خالیه. /refresh بزن.")

    elif text == "/fast":
        send_message(chat_id, "⏳ در حال تست سرعت...")
        socks5, http = fetch_proxies()
        fast = []
        test_list = random.sample(socks5, min(20, len(socks5)))
        for proxy in test_list:
            ok, ip = test_proxy(proxy, "socks5")
            if ok:
                fast.append(proxy)
                if len(fast) >= 5:
                    break
        if fast:
            lines = "⚡ سریع‌ترین پروکسی‌ها:\n\n"
            for i, p in enumerate(fast, 1):
                link = make_proxy_link(p, "socks5")
                if link:
                    lines += f'{i}. <a href="{link}">⚡ {p}</a> ✅\n'
            send_message(chat_id, lines)
        else:
            send_message(chat_id, "❌ پروکسی سالمی پیدا نشد.")

    elif text == "/refresh":
        send_message(chat_id, "🔄 در حال بروزرسانی...")
        socks5, http = fetch_proxies()
        send_message(chat_id, f"✅ بروزرسانی شد!\n\n🟢 SOCKS5: {len(socks5)}\n🔵 HTTP: {len(http)}")

    elif text == "/count":
        if not cached_proxies["socks5"]:
            fetch_proxies()
        send_message(chat_id,
            f"📊 تعداد پروکسی‌ها:\n\n"
            f"🟢 SOCKS5: {len(cached_proxies['socks5'])}\n"
            f"🔵 HTTP: {len(cached_proxies['http'])}"
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
    logger.info("Starting UC Proxy Bot...")
    setup_webhook()
    fetch_proxies()
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Running on port {port}")
    app.run(host='0.0.0.0', port=port)
