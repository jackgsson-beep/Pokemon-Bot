import time
import requests
import xml.etree.ElementTree as ET
import os
from threading import Thread
from flask import Flask

# =========================================================================
# CONFIG
# =========================================================================
# Klistra in dina riktiga Discord-webhooks här:
WEBHOOK_ONLINE = "https://discord.com"
WEBHOOK_IRL = "https://discord.com"

VIP_ROLE_ID = "" 
INTERVALL_SEKUNDER = 60
# =========================================================================

app = Flask('')

@app.route('/')
def home():
    return "Pokémon RSS Monitor är vid liv dygnet runt!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

SVARTLISTA = ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck", "bok", "figurer", "lampa", "sleeves", "kortfickor", "tärningar"]
produkt_databas = set()  # Håller koll på vilka unika produkter vi redan sett

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
                "footer": {"text": "Webhallen Pokémon RSS Monitor V1.0"}
            }
        ]
    }
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        requests.post(webhook_url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Fel vid sändning till Discord: {e}", flush=True)

def kolla_webhallen_rss():
    print(f"[{time.strftime('%H:%M:%S')}] Läser av Webhallens officiella nyhetsflöde...", flush=True)
    
    # Webhallens öppna RSS-flöde för alla nya produkter (Cloudflare-fritt!)
    RSS_URL = "https://webhallen.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] Misslyckades med RSS. Status: {response.status_code}", flush=True)
            return

        # Tolka XML-flödet
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        antall_pokemon = 0
        
        for item in items:
            titel = item.find("title").text
            lank = item.find("link").text
            guid = item.find("guid").text if item.find("guid") is not None else lank
            
            titel_lower = titel.lower()
            
            # Sortera ut så vi BARA kollar på Pokémon TCG (men hoppar över svartlistat skräp)
            if "pokemon" in titel_lower or "pokémon" in titel_lower:
                if any(skrap_ord in titel_lower for skrap_ord in SVARTLISTA):
                    continue
                
                antall_pokemon += 1
                
                # Om det är en helt ny produkt i flödet som inte fanns i databasen innan
                if guid not in produkt_databas:
                    print(f"🚨 NY PRODUKT UPPTÄCKT: {titel}", flush=True)
                    
                    # Lägg till i databasen så vi inte pingar igen
                    produkt_databas.add(guid)
                    
                    # Skicka notis till Discord
                    discord_titel = "🌐 NY POKÉMON-PRODUKT UPPTÄCKT!"
                    text = f"**Produkt:** {titel}\n\n*Denna produkt har precis lagts till i Webhallens system!*"
                    skicka_till_discord(WEBHOOK_ONLINE, discord_titel, text, lank)
                    
        print(f"[{time.strftime('%H:%M:%S')}] Sökning klar! Hittade {antall_pokemon} aktiva Pokémon-produkter i nyhetsflödet.", flush=True)

    except Exception as e:
        print(f"Fel vid RSS-läsning: {e}", flush=True)

if __name__ == "__main__":
    print("==================================================")
    print("   WEBHALLEN POKÉMON-RSS KÖRS PÅ RENDER (FLASK)   ")
    print("==================================================")
    
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    while True:
        kolla_webhallen_rss()
        time.sleep(INTERVALL_SEKUNDER)
