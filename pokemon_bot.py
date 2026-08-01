import time
import requests
import os
import json
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

# =========================================================================
# CONFIG
# =========================================================================
WEBHOOK_ONLINE = os.environ.get("WEBHOOK_ONLINE")
WEBHOOK_IRL = os.environ.get("WEBHOOK_IRL")
FLARE_URL = os.environ.get("FLARE_URL")
VIP_ROLE_ID = "" 
# =========================================================================

SVARTLISTA = ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck", "bok", "figurer", "lampa"]
produkt_databas = {}

app = Flask('')

@app.route('/')
def home():
    return f"Boten rullar! Senaste koll: {time.strftime('%H:%M:%S')}"

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
    print(f"[{time.strftime('%H:%M:%S')}] --- STARTAR SÖKNING VIA FLARESOLVERR ---")
    
    API_URL = "https://webhallen.com"
    
    payload = {
        "cmd": "request.get",
        "url": API_URL,
        "maxTimeout": 60000  # Ger FlareSolverr upp till 60 sekunder att lösa Cloudflare
    }

    try:
        base_url = FLARE_URL.strip("/")
        # Vi skickar förfrågan via FlareSolverr-instansen
        response = requests.post(f"{base_url}/v1", json=payload, timeout=70)
        
        if response.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] FlareSolverr svarade med felkod: {response.status_code}")
            return

        res_data = response.json()
        solution = res_data.get("solution", {})
        json_text = solution.get("response", "")
        
        # Rensa bort eventuella HTML-taggar om FlareSolverr bäddat in JSON-svaret i en body-tagg
        if "<body>" in json_text:
            try:
                json_text = json_text.split("<body>")[1].split("</body>")[0]
            except Exception:
                pass

        # Försök tolka svaret som ren JSON från Webhallen
        try:
            data = json.loads(json_text)
        except Exception:
            print(f"[{time.strftime('%H:%M:%S')}] FEL: FlareSolverr returnerade inte giltig JSON. Webhallen blockerade.")
            return

        produkter = data.get("rows", [])
        if not produkter:
            produkter = data.get("products", [])
            
        print(f"[{time.strftime('%H:%M:%S')}] SUCCÉ! Sökning klar via FlareSolverr. Hittade {len(produkter)} produkter.")

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
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Totalt i butiker nu:** {aktuellt_irl} st"
                skicka_till_discord(WEBHOOK_IRL, titel, text, lank, bild_url)

            produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Fel under FlareSolverr-sökning: {e}")

# Starta den stabila schemaläggaren
scheduler = BackgroundScheduler()
scheduler.add_job(func=kolla_webhallen_pokemon, trigger="interval", seconds=60)
scheduler.start()

if __name__ == "__main__":
    print("==================================================")
    print("   WEBHALLEN POKÉMON-BOT LIVE VIA FLARESOLVERR    ")
    print("==================================================")
    # Kör första varvet direkt vid start
    kolla_webhallen_pokemon()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
