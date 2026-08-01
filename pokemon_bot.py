import time
import requests
import os
import json
from threading import Thread
from flask import Flask

# =========================================================================
# CONFIG
# =========================================================================
WEBHOOK_ONLINE = os.environ.get("WEBHOOK_ONLINE")
WEBHOOK_IRL = os.environ.get("WEBHOOK_IRL")
VIP_ROLE_ID = "" 
INTERVALL_SEKUNDER = 60
# =========================================================================

SVARTLISTA = ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck", "bok", "figurer", "lampa"]
produkt_databas = {}

app = Flask('')

@app.route('/')
def home():
    return "Boten rullar!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def skicka_till_discord(webhook_url, titel, text, lank, bild_url):
    content_ping = f"<@&{VIP_ROLE_ID}>" if VIP_ROLE_ID else ""
    payload = {
        "content": content_ping,
        "embeds": [
            {
                "title": titel,
                "description": text,
                "url": lank,
                "color": 5814783,
                "image": {"url": bild_url} if bild_url else None,
                "footer": {"text": "Webhallen Pokémon Monitor"}
            }
        ]
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Fel vid sändning till Discord: {e}")

def kolla_webhallen_pokemon():
    print(f"[{time.strftime('%H:%M:%S')}] Söker DIREKT mot Webhallen API...")
    
    API_URL = "https://webhallen.com"
    
    # Låtsas vara en vanlig webbläsare så att Webhallen släpper igenom oss direkt
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        # Anropa Webhallen direkt – tar under 1 sekund istället för 30 sekunder via FlareSolverr
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] Webhallen API svarade med felkod: {response.status_code}")
            return

        data = response.json()
        produkter = data.get("rows", [])
        
        if not produkter:
            produkter = data.get("products", [])
            
        print(f"[{time.strftime('%H:%M:%S')}] SUCCÉ! Hittade {len(produkter)} produkter i Webhallens live-lager.")

        for prod in produkter:
            prod_id = str(prod.get("id"))
            namn = prod.get("name", "")
            namn_lower = namn.lower()

            if any(skrap_ord in namn_lower for skrap_ord in SVARTLISTA):
                continue 

            pris = prod.get("price", {}).get("current", "Okänt")
            lank = f"https://webhallen.com{prod_id}"
            
            bilder = prod.get("images", [])
            bild_url = bilder.get("large", "") if bilder and isinstance(bilder, list) else ""
            
            stock_info = prod.get("stock", {})
            aktuellt_online = int(stock_info.get("web", 0))
            aktuellt_irl = int(stock_info.get("shop", 0))

            if prod_id not in produkt_databas:
                produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}
                continue

            forra_online = produkt_databas[prod_id]["online"]
            forra_irl = produkt_databas[prod_id]["irl"]

            if aktuellt_online > forra_online:
                titel = "🌐 NYHET / RESTOCK ONLINE!"
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Nytt lager på webben:** {aktuellt_online} st"
                skicka_till_discord(WEBHOOK_ONLINE, titel, text, lank, bild_url)

            if aktuellt_irl > forra_irl:
                titel = "🛒 RESTOCK I FYSISK BUTIK!"
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Totalt i butiker nu:** {aktuellt_irl} st\n🏃‍♂️ Kolla din lokala butik snabbt!"
                skicka_till_discord(WEBHOOK_IRL, titel, text, lank, bild_url)

            produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Fel vid direktanrop: {e}")

def bot_loop():
    print("==================================================")
    print("   WEBHALLEN POKÉMON-BOT ÄR NU STARTAD (MOLN)     ")
    print("==================================================")
    while True:
        kolla_webhallen_pokemon()
        time.sleep(INTERVALL_SEKUNDER)

if __name__ == "__main__":
    t = Thread(target=bot_loop)
    t.daemon = True
    t.start()
    run_server()
