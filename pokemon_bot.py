import time
import requests
import json
import os
from threading import Thread
from flask import Flask

# =========================================================================
# CONFIG (HÄR LÄGGER DU IN DINA EGNA LÄNKAR OCH NYCKLAR)
# =========================================================================
# 1. Klistra in dina riktiga Discord-webhooks här:
WEBHOOK_ONLINE = "https://discord.com"
WEBHOOK_IRL = "https://discord.com"

# 2. Skapa ett gratis konto på scraperapi.com och klistra in din nyckel här:
SCRAPER_API_KEY = "e663a9e31555f82cc560704a70652f92"

# 3. ID på din Discord-roll för VIP-pings (Frivilligt, annars lämna tom "")
VIP_ROLE_ID = "" 

INTERVALL_SEKUNDER = 60
# =========================================================================

# Flask-app för att göra Render nöjd på gratisnivån
app = Flask('')

@app.route('/')
def home():
    return "Pokémon Monitor är vid liv och körs dygnet runt!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

SVARTLISTA = ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck", "bok", "figurer", "lampa", "sleeves", "kortfickor", "tärningar"]
produkt_databas = {}

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
                "footer": {"text": "Webhallen Pokémon Monitor V1.0"}
            }
        ]
    }
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        requests.post(webhook_url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Fel vid sändning till Discord: {e}", flush=True)

def kolla_webhallen_pokemon():
    print(f"[{time.strftime('%H:%M:%S')}] Söker mot Webhallens dolda API...", flush=True)
    TARGET_URL = "https://webhallen.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        # Om du har lagt in en nyckel används ScraperAPI för att runda Cloudflare
        if SCRAPER_API_KEY:
            proxy_url = f"http://scraperapi.com?api_key={SCRAPER_API_KEY}&url={TARGET_URL}"
            response = requests.get(proxy_url, timeout=30)
        else:
            # Annars körs det direkt (vilket blir blockerat på Render)
            response = requests.get(TARGET_URL, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] Felkod från Webhallen: {response.status_code}. (Kräver ScraperAPI-nyckel)", flush=True)
            return

        data = response.json()
        produkter = data.get("products", [])
        print(f"[{time.strftime('%H:%M:%S')}] SUCCÉ! Analyserar {len(produkter)} produkter.", flush=True)

        for prod in produkter:
            prod_id = str(prod.get("id"))
            namn = prod.get("name", "")
            namn_lower = namn.lower()

            if any(skrap_ord in namn_lower for skrap_ord in SVARTLISTA):
                continue 

            pris = prod.get("price", {}).get("current", "Okänt")
            lank = f"https://webhallen.com{prod_id}"
            
            # Hantering av Webhallens bilder
            bilder = prod.get("images", [])
            bild_url = ""
            if isinstance(bilder, list) and len(bilder) > 0:
                forsta_bilden = bilder[0]
                if isinstance(forsta_bilden, dict):
                    bild_url = forsta_bilden.get("large", "")
            
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
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Totalt i butiker nu:** {aktuellt_irl} st"
                skicka_till_discord(WEBHOOK_IRL, titel, text, lank, bild_url)

            produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}

    except Exception as e:
        print(f"Fel vid anrop: {e}", flush=True)

if __name__ == "__main__":
    print("==================================================")
    print("   WEBHALLEN POKÉMON-BOT KÖRS PÅ RENDER (FLASK)   ")
    print("==================================================")
    
    # Starta den fejkade webbservern i en egen tråd så Render blir nöjd
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Starta din vanliga Pokémon-övervakningsloop
    while True:
        kolla_webhallen_pokemon()
        time.sleep(INTERVALL_SEKUNDER)
