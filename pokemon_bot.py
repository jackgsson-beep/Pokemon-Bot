import time
import requests
import os
import xml.etree.ElementTree as ET
from flask import Flask
from threading import Thread

# =========================================================================
# CONFIG
# =========================================================================
WEBHOOK_ONLINE = os.environ.get("WEBHOOK_ONLINE")
WEBHOOK_IRL = os.environ.get("WEBHOOK_IRL")
VIP_ROLE_ID = "" 
INTERVALL_SEKUNDER = 60
# =========================================================================

produkt_databas = set()  # Sparar produkt-IDn vi redan sett
app = Flask('')

@app.route('/')
def home():
    return f"Boten rullar! Aktiv och bevakar RSS."

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
    print(f"[{time.strftime('%H:%M:%S')}] Söker efter Pokémon-nyheter via Webhallen RSS...")
    
    # Officiell RSS-feed för Webhallens sökningar (Går förbi all Cloudflare)
    RSS_URL = "https://webhallen.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] RSS svarade med felkod: {response.status_code}")
            return

        # Tolka XML-datan från RSS-flödet
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        print(f"[{time.strftime('%H:%M:%S')}] RSS-avläsning klar. Hittade {len(items)} produkter.")

        for item in items:
            titel_raw = item.find("title").text if item.find("title") is not None else ""
            lank = item.find("link").text if item.find("link") is not None else ""
            
            # Extrahera ID från länken (t.ex. från https://webhallen.com)
            prod_id = lank.split("/")[-1] if lank else ""

            # Svartlista direkt i RSS-titeln
            namn_lower = titel_raw.lower()
            if any(x in namn_lower for x in ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck"]):
                continue

            # Första körningen: fyll databasen så den inte spammar gamla produkter
            if prod_id not in produkt_databas:
                produkt_databas.add(prod_id)
                continue

            # OM PRODUKTEN ÄR HELT NY I RSS-FLÖDET (Preorder / Nytt släpp / Stor Restock)
            titel = "🚨 NY POKÉMON-PRODUKT HITTAD!"
            text = f"**Produkt:** {titel_raw}\n\nEn ny produkt eller stor restock har dykt upp i Webhallens nyhetsflöde!"
            
            # Skickar till online-kanalen som standard för nya släpp
            skicka_till_discord(WEBHOOK_ONLINE, titel, text, lank)
            
            produkt_databas.add(prod_id)

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Fel vid RSS-läsning: {e}")

def bot_loop():
    # Låt servern starta upp i 5 sekunder först så Render hinner bli grönt
    time.sleep(5)
    while True:
        kolla_webhallen_rss()
        time.sleep(INTERVALL_SEKUNDER)

if __name__ == "__main__":
    # Starta loopen i en enkel, ren bakgrundstråd efter att Flask har initierats
    t = Thread(target=bot_loop)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
