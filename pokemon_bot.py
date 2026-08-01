import time
import requests
import os
import json
from threading import Thread
from flask import Flask

# =========================================================================
# MILJÖVARIABLER (Sätt dessa under "Environment Variables" i Render!)
# =========================================================================
WEBHOOK_ONLINE = os.environ.get("WEBHOOK_ONLINE", "DIN_DEFAULT_OM_DU_KÖR_LOKALT")
WEBHOOK_IRL = os.environ.get("WEBHOOK_IRL", "DIN_DEFAULT_OM_DU_KÖR_LOKALT")
FLARE_URL = os.environ.get("FLARE_URL", "https://mitt-flaresolverr.onrender.com")

# ID på dina Discord-roller för pings (Högerklicka på rollen i Discord -> Kopiera ID)
VIP_ROLE_ID = "123456789012345678" 

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
    # Inkludera roll-ping högst upp i meddelandet så att medlemmar får notis
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
    print(f"[{time.strftime('%H:%M:%S')}] Söker på Webhallen via FlareSolverr...")
    
    # KORREKTION: Vi anropar Webhallens sök-API direkt och filtrerar på 'pokemon' sorterat på nyheter
    API_URL = "https://webhallen.com"
    
    payload = {
        "cmd": "request.get",
        "url": API_URL,
        "maxTimeout": 60000
    }

    try:
        base_url = FLARE_URL.strip("/")
        response = requests.post(f"{base_url}/v1", json=payload, timeout=70)
        
        if response.status_code != 200:
            print(f"FlareSolverr returnerade statuskod: {response.status_code}")
            return

        res_data = response.json()
        solution = res_data.get("solution", {})
        
        # FlareSolverr skickar tillbaka HTML/Text i 'response'
        json_text = solution.get("response", "")
        
        # Eftersom vi anropade API:et måste vi rensa bort eventuell HTML-tagg 
        # som FlareSolverr kan ha svept runt JSON-svaret (händer ibland)
        if "<body>" in json_text:
            json_text = json_text.split("<body>")[1].split("</body>")[0]

        data = json.loads(json_text)
        produkter = data.get("products", [])

        for prod in produkter:
            prod_id = str(prod.get("id"))
            namn = prod.get("name", "")
            namn_lower = namn.lower()

            if any(skrap_ord in namn_lower for skrap_ord in SVARTLISTA):
                continue 

            pris = prod.get("price", {}).get("current", "Okänt")
            lank = f"https://webhallen.com{prod_id}"
            
            bilder = prod.get("images", [])
            bild_url = bilder[0].get("large", "") if bilder else ""
            
            stock_info = prod.get("stock", {})
            aktuellt_online = int(stock_info.get("web", 0))
            aktuellt_irl = int(stock_info.get("shop", 0))

            # Första körningen: Spara bara lagret och hoppa över ping
            if prod_id not in produkt_databas:
                produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}
                continue

            forra_online = produkt_databas[prod_id]["online"]
            forra_irl = produkt_databas[prod_id]["irl"]

            # Koll för ONLINE RESTOCK
            if aktuellt_online > forra_online:
                titel = "🌐 NYHET / RESTOCK ONLINE!"
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Nytt lager på webben:** {aktuellt_online} st"
                skicka_till_discord(WEBHOOK_ONLINE, titel, text, lank, bild_url)

            # Koll för IRL RESTOCK
            if aktuellt_irl > forra_irl:
                titel = "🛒 RESTOCK I FYSISK BUTIK!"
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Totalt i butiker nu:** {aktuellt_irl} st\n🏃‍♂️ Kolla butikslager på hemsidan!"
                skicka_till_discord(WEBHOOK_IRL, titel, text, lank, bild_url)

            # Uppdatera databasen med det nya saldot
            produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}

    except json.JSONDecodeError:
        print("Kunde inte tolka svaret som JSON. Webhallen kan ha ändrat struktur eller blockerat.")
    except Exception as e:
        print(f"Fel i bot-loopen: {e}")

def bot_loop():
    print("==================================================")
    print("   WEBHALLEN POKÉMON-BOT ÄR NU STARTAD (MOLN)     ")
    print("==================================================")
    while True:
        kolla_webhallen_pokemon()
        time.sleep(INTERVALL_SEKUNDER)

if __name__ == "__main__":
    t = Thread(target=run_server)
    t.start()
    bot_loop()
