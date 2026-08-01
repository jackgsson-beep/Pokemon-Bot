import time
import requests
import os
import json
from threading import Thread
from flask import Flask

# =========================================================================
# MILJÖVARIABLER (Hämtas säkert från Render!)
# =========================================================================
WEBHOOK_ONLINE = os.environ.get("WEBHOOK_ONLINE")
WEBHOOK_IRL = os.environ.get("WEBHOOK_IRL")
FLARE_URL = os.environ.get("FLARE_URL")

# ID på din Discord-roll för VIP-pings (Högerklicka på rollen i Discord -> Kopiera ID)
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
    print(f"[{time.strftime('%H:%M:%S')}] Söker på Webhallen via FlareSolverr...")
    
    # KORRIGERAD API-URL: Söker efter pokemon sorterat på de senaste nyheterna/restocksen
    API_URL = "https://webhallen.com"
    
    payload = {
        "cmd": "request.get",
        "url": API_URL,
        "maxTimeout": 15000
    }

    try:
        base_url = FLARE_URL.strip("/")
        print(f"[{time.strftime('%H:%M:%S')}] Skickar anrop till FlareSolverr på: {base_url}/v1")
        
        response = requests.post(f"{base_url}/v1", json=payload, timeout=30)
        print(f"[{time.strftime('%H:%M:%S')}] FlareSolverr svarade med status: {response.status_code}")
        
        if response.status_code != 200:
            return

        res_data = response.json()
        solution = res_data.get("solution", {})
        json_text = solution.get("response", "")
        
        if "<body>" in json_text:
            json_text = json_text.split("<body>").split("</body>")

        data = json.loads(json_text)
        
        # FIX: Läser från 'rows' istället för 'products' enligt Webhallens nya API-struktur
        produkter = data.get("rows", [])
        
        # Fallback om de skulle ändra tillbaka
        if not produkter:
            produkter = data.get("products", [])
            
        print(f"[{time.strftime('%H:%M:%S')}] Lyckades läsa API. Hittade {len(produkter)} produkter i listan.")

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

            # LIVE-TEST MED '>=', men kräver att det faktiskt finns minst 1 i lager
            if aktuellt_online > forra_online and aktuellt_online > 0:
                titel = "🌐 NYHET / RESTOCK ONLINE!"
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Lager på webben:** {aktuellt_online} st"
                skicka_till_discord(WEBHOOK_ONLINE, titel, text, lank, bild_url)

            if aktuellt_irl > forra_irl and aktuellt_irl > 0:
                titel = "🛒 RESTOCK I FYSISK BUTIK!"
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Totalt i butiker nu:** {aktuellt_irl} st\n🏃‍♂️ Kolla butikslager på hemsidan!"
                skicka_till_discord(WEBHOOK_IRL, titel, text, lank, bild_url)

            produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}

    except requests.exceptions.Timeout:
        print(f"[{time.strftime('%H:%M:%S')}] FEL: Timeout mot FlareSolverr.")
    except json.JSONDecodeError:
        print(f"[{time.strftime('%H:%M:%S')}] FEL: JSONDecodeError. Kunde inte tolka datan.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Fel i loopen: {e}")

def bot_loop():
    print("==================================================")
    print("   WEBHALLEN POKÉMON-BOT ÄR NU STARTAD (MOLN)     ")
    print("==================================================")

    while True:
        kolla_webhallen_pokemon()
        print(f"[{time.strftime('%H:%M:%S')}] Väntar {INTERVALL_SEKUNDER} sekunder till nästa sökning...")
        time.sleep(INTERVALL_SEKUNDER)

if __name__ == "__main__":
    t = Thread(target=bot_loop)
    t.daemon = True
    t.start()
    run_server()
