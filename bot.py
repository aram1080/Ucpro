import os
import random
import requests
import logging
from flask import Flask, request
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

TG_PROXY_SOURCES = {
    "mtproto_iran": "https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_ru.txt",
    "mtproto_eu": "https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_eu.txt",
    "socks5": "https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/socks5.txt",
}

V2RAY_SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_raw.txt",
]

SUB_LINKS = {
    "V2Ray Aggregator": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "Epodonios": "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "Shadowsocks": "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",
    "NoMoreWalls": "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_raw.txt",
}

cached = {
    "mtproto_iran": [], "mtproto_eu": [], "socks5": [],
    "vless": [], "vmess": [], "trojan": [], "ss": []
}

@app.route('/')
def home():
    return 'Bot is running!'

@app.route('/health')
def health():
    return 'OK', 200

def api(method, data):
    try:
        r = requests.post(f"{TG_API}/{method}", json=data, timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return {}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        data["reply_markup"] = reply_markup
    return api("sendMessage", data)

def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        data["reply_markup"] = reply_markup
    return api("editMessageText", data)

def answer_callback(callback_id):
    api("answerCallbackQuery", {"callback_query_id": callback_id})

def build_keyboard(rows):
    return {"inline_keyboard": rows}

def btn(text, callback_data):
    return {"text": text, "callback_data": callback_data}

# === MENU KEYBOARDS ===

def main_menu():
    return build_keyboard([
        [btn("🔗 پروکسی تلگرام", "menu_proxy"), btn("📡 کانفیگ VPN", "menu_vpn")],
        [btn("📋 لینک ساب", "menu_sub"), btn("📊 تعداد", "count")],
        [btn("🔄 بروزرسانی", "refresh")],
    ])

def proxy_menu():
    return build_keyboard([
        [btn("🇮🇷 MTProto ایران", "proxy_iran"), btn("🇪🇺 MTProto اروپا", "proxy_eu")],
        [btn("🔌 SOCKS5", "proxy_socks")],
        [btn("🎲 تصادفی", "proxy_random")],
        [btn("⬅️ بازگشت", "back")],
    ])

def vpn_menu():
    return build_keyboard([
        [btn("🟢 VLESS", "vpn_vless"), btn("🔵 VMESS", "vpn_vmess")],
        [btn("🔴 Trojan", "vpn_trojan"), btn("🟡 SS", "vpn_ss")],
        [btn("🎲 تصادفی", "vpn_random")],
        [btn("⬅️ بازگشت", "back")],
    ])

# === FETCH FUNCTIONS ===

def fetch_tg_proxies():
    for name, url in TG_PROXY_SOURCES.items():
        try:
            r = requests.get(url, timeout=10)
            cached[name] = [l.strip() for l in r.text.strip().split("\n") if l.strip().startswith("tg://")]
            logger.info(f"TG {name}: {len(cached[name])}")
        except:
            pass

def fetch_v2ray():
    all_lines = []
    for url in V2RAY_SOURCES:
        try:
            r = requests.get(url, timeout=15)
            for line in r.text.strip().split("\n"):
                line = line.strip()
                if line.startswith(("vless://", "vmess://", "trojan://", "ss://")):
                    all_lines.append(line)
        except:
            continue
    seen = set()
    for key in ["vless", "vmess", "trojan", "ss"]:
        cached[key] = []
    for line in all_lines:
        if line in seen:
            continue
        seen.add(line)
        for key in ["vless", "vmess", "trojan", "ss"]:
            prefixes = {"vless": "vless://", "vmess": "vmess://", "trojan": "trojan://", "ss": "ss://"}
            if line.startswith(prefixes[key]):
                cached[key].append(line)
                break

def fetch_all():
    fetch_tg_proxies()
    fetch_v2ray()
    return sum(len(v) for v in cached.values())

# === PROXY HANDLERS ===

def show_proxy(chat_id, message_id, proxy_type, label):
    items = cached.get(proxy_type, [])
    if not items:
        fetch_tg_proxies()
        items = cached.get(proxy_type, [])

    if items:
        picks = random.sample(items, min(10, len(items)))
        lines = f"🔗 {label} ({len(items)} موجود):\n\n"
        for i, c in enumerate(picks, 1):
            lines += f'{i}. <a href="{c}">🔗 اضافه کن</a>\n'
        lines += "\n👆 روی لینک بزن"
    else:
        lines = "❌ پروکسی پیدا نشد. دوباره تلاش کن."

    kb = build_keyboard([[btn("🔄 بروزرسانی", f"proxy_{proxy_type}")], [btn("⬅️ بازگشت", "back")]])
    edit_message(chat_id, message_id, lines, kb)

def show_vpn(chat_id, message_id, config_type, label):
    items = cached.get(config_type, [])
    if not items:
        fetch_v2ray()
        items = cached.get(config_type, [])

    if items:
        picks = random.sample(items, min(5, len(items)))
        lines = f"📌 {label} ({len(items)} موجود):\n\n"
        for i, c in enumerate(picks, 1):
            lines += f"{i}.\n<code>{c}</code>\n\n"
    else:
        lines = "❌ کانفیگی پیدا نشد."

    kb = build_keyboard([[btn("🔄 بروزرسانی", f"vpn_{config_type}")], [btn("⬅️ بازگشت", "back")]])
    edit_message(chat_id, message_id, lines, kb)

# === CALLBACK HANDLER ===

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # Callback Query (دکمه)
    if data and "callback_query" in data:
        cq = data["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        msg_id = cq["message"]["message_id"]
        call_data = cq["data"]
        answer_callback(cq["id"])

        if call_data == "back":
            edit_message(chat_id, msg_id, "🟢 ربات VPN UC\n\nیکی رو انتخاب کن:", main_menu())

        elif call_data == "menu_proxy":
            edit_message(chat_id, msg_id, "🔗 پروکسی تلگرام\n\nیکی رو انتخاب کن:", proxy_menu())

        elif call_data == "menu_vpn":
            edit_message(chat_id, msg_id, "📡 کانفیگ VPN\n\nیکی رو انتخاب کن:", vpn_menu())

        elif call_data == "menu_sub":
            lines = "📋 لینک ساب:\n\n"
            for name, link in SUB_LINKS.items():
                lines += f"🔗 {name}:\n<code>{link}</code>\n\n"
            lines += "📌 کپی کن در v2rayNG یا Hiddify"
            edit_message(chat_id, msg_id, lines, build_keyboard([[btn("⬅️ بازگشت", "back")]]))

        elif call_data.startswith("proxy_"):
            ptype = call_data.replace("proxy_", "")
            labels = {"mtproto_iran": "MTProto ایران", "mtproto_eu": "MTProto اروپا", "socks5": "SOCKS5", "random": "تصادفی"}
            if ptype == "random":
                all_p = cached["mtproto_iran"] + cached["mtproto_eu"] + cached["socks5"]
                if all_p:
                    picks = random.sample(all_p, min(10, len(all_p)))
                    lines = "🔗 پروکسی تصادفی:\n\n"
                    for i, c in enumerate(picks, 1):
                        lines += f'{i}. <a href="{c}">🔗 اضافه کن</a>\n'
                    edit_message(chat_id, msg_id, lines, build_keyboard([[btn("🔄 بروزرسانی", "proxy_random")], [btn("⬅️ بازگشت", "back")]]))
            else:
                show_proxy(chat_id, msg_id, ptype, labels.get(ptype, ptype))

        elif call_data.startswith("vpn_"):
            vtype = call_data.replace("vpn_", "")
            labels = {"vless": "VLESS", "vmess": "VMESS", "trojan": "Trojan", "ss": "Shadowsocks"}
            if vtype == "random":
                all_v = cached["vless"] + cached["vmess"] + cached["trojan"] + cached["ss"]
                if all_v:
                    picks = random.sample(all_v, min(3, len(all_v)))
                    lines = "🎲 کانفیگ تصادفی:\n\n"
                    for i, c in enumerate(picks, 1):
                        t = "VLESS" if c.startswith("vless") else "VMESS" if c.startswith("vmess") else "Trojan" if c.startswith("trojan") else "SS"
                        lines += f"📌 {i} ({t}):\n<code>{c}</code>\n\n"
                    edit_message(chat_id, msg_id, lines, build_keyboard([[btn("🔄 بروزرسانی", "vpn_random")], [btn("⬅️ بازگشت", "back")]]))
            else:
                show_vpn(chat_id, msg_id, vtype, labels.get(vtype, vtype))

        elif call_data == "count":
            total = sum(len(v) for v in cached.values())
            lines = (
                f"📊 تعداد:\n\n"
                f"🔗 MTProto ایران: {len(cached['mtproto_iran'])}\n"
                f"🔗 MTProto اروپا: {len(cached['mtproto_eu'])}\n"
                f"🔗 SOCKS5: {len(cached['socks5'])}\n"
                f"🟢 VLESS: {len(cached['vless'])}\n"
                f"🔵 VMESS: {len(cached['vmess'])}\n"
                f"🔴 Trojan: {len(cached['trojan'])}\n"
                f"🟡 SS: {len(cached['ss'])}\n"
                f"📊 کل: {total}"
            )
            edit_message(chat_id, msg_id, lines, build_keyboard([[btn("⬅️ بازگشت", "back")]]))

        elif call_data == "refresh":
            edit_message(chat_id, msg_id, "🔄 در حال بروزرسانی...", None)
            total = fetch_all()
            lines = (
                f"✅ بروزرسانی شد!\n\n"
                f"🔗 MTProto ایران: {len(cached['mtproto_iran'])}\n"
                f"🔗 MTProto اروپا: {len(cached['mtproto_eu'])}\n"
                f"🔗 SOCKS5: {len(cached['socks5'])}\n"
                f"🟢 VLESS: {len(cached['vless'])}\n"
                f"🔵 VMESS: {len(cached['vmess'])}\n"
                f"🔴 Trojan: {len(cached['trojan'])}\n"
                f"🟡 SS: {len(cached['ss'])}\n"
                f"📊 کل: {total}"
            )
            edit_message(chat_id, msg_id, lines, main_menu())

        return 'OK', 200

    # پیام متنی
    if data and "message" in data:
        msg = data["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")

        if text in ["/start", "/menu"]:
            send_message(chat_id, "🟢 ربات VPN UC\n\nیکی رو انتخاب کن:", main_menu())

        elif text == "/refresh":
            send_message(chat_id, "🔄 در حال بروزرسانی...")
            total = fetch_all()
            send_message(chat_id, f"✅ بروزرسانی شد! کل: {total}", main_menu())

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
    fetch_all()
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Running on port {port}")
    app.run(host='0.0.0.0', port=port)
