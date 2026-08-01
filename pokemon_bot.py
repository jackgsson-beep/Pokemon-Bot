import time
import requests
import os
import xml.etree.ElementTree as ET
from flask import Flask

# =========================================================================
# CONFIG
# =========================================================================
WEBHOOK_ONLINE = os.environ.get("WEBHOOK_ONLINE")
WEBHOOK_IRL = os.environ.get("WEBHOOK_IRL")
VIP_ROLE_ID = "" 
# =========================================================================

# Vi sparar IDn i en fil eller lokalt minne
produkt_databas = set()
app = Flask('')

def skicka_till_discord(webhook_url, titel, text, lank):
    content_ping = f"<@&{VIP_ROLE_ID}>" if VIP_ROLE_ID else ""
    payload = {
        "content": content_ping,
        "embeds": [
            {
                "title": titel,
                "description": text,
                "url": lank,
                "color": 5814783,
                "footer": {"text": "Webhallen Pokémon RSS Monitor"}
            }
        ]
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Fel vid sändning till Discord: {e}")

def kolla_webhallen_rss():
    print(f"[{time.strftime('%H:%M:%S')}] UptimeRobot triggade sökning via Webhallen RSS...")
    RSS_URL = "https://webhallen.com"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"RSS Felkod: {response.status_code}"

        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        hittade_nya = 0
        for item in items:
            titel_raw = item.find("title").text if item.find("title") is not None else ""
            lank = item.find("link").text if item.find("link") is not None else ""
            prod_id = lank.split("/")[-1] if lank else ""

            if not prod_id or not titel_raw:
                continue

            namn_lower = titel_raw.lower()
            if any(x in namn_lower for x in ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck"]):
                continue

            # Ta bort/kommentera bort dessa tre rader sen när du ser att det funkar!
            # if prod_id not in produkt_databas:
            #     produkt_databas.add(prod_id)
            #     continue

            titel = "🚨 NY POKÉMON-PRODUKT HITTAD!"
            text = f"**Produkt:** {titel_raw}\n\nEn ny produkt eller stor restock har dykt upp i Webhallens nyhetsflöde!"
            skicka_till_discord(WEBHOOK_ONLINE, titel, text, lank)
            produkt_databas.add(prod_id)
            hittade_nya += 1

        return f"Sökning klar. Hittade {len(items)} produkter. Skickade {hittade_nya} till Discord."

    except Exception as e:
        return f"Fel vid RSS-läsning: {e}"

# VARJE GÅNG UPTIMEROBOT BESÖKER DIN HEMSIDA KÖRS SÖKNINGEN DIREKT!
@app.route('/')
def home():
    resultat = kolla_webhallen_rss()
    return f"Status: {resultat} - Tid: {time.strftime('%H:%M:%S')}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
