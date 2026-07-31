import time
import requests
import os
from threading import Thread
from flask import Flask

WEBHOOK_ONLINE = "https://discord.com"
WEBHOOK_IRL = "https://discord.com"
FLARE_URL = "https://onrender.com"
INTERVALL_SEKUNDER = 60

SVARTLISTA = ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck", "bok", "figurer", "lampa"]
produkt_databas = {}

app = Flask('')

@app.route('/')
def home():
    return "Boten är vid liv och rullar!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def skicka_till_discord(webhook_url, meddelande):
    try:
        requests.post(webhook_url, json={"content": meddelande})
    except Exception as e:
        print(f"Fel vid sändning till Discord: {e}")

def kolla_webhallen_pokemon():
    print(f"[{time.strftime('%H:%M:%S')}] Söker på Webhallen via FlareSolverr...")
    payload = {
        "cmd": "request.get",
        "url": "https://webhallen.com",
        "maxTimeout": 60000
    }
    try:
        base_url = FLARE_URL.strip("/")
        response = requests.post(f"{base_url}/v1", json=payload, timeout=70)
        if response.status_code != 200:
            print(f"FlareSolverr svarade med felkod: {response.status_code}")
            return
        res_data = response.json()
        solution = res_data.get("solution", {})
        json_text = solution.get("response", "")
        if "products" not in json_text:
            print("Kunde inte hitta produktdata i svaret. Dörrvakten kan ha blockerat.")
            return
        import json
        data = json.loads(json_text)
        produkter = data.get("products", [])
        
        # --- TEST-KOD INBÄDDAD EXAKT RÄTT ---
        fejk_produkt = {
            "id": 999999,
            "name": "TEST: Pokémon Scarlet & Violet Booster Box Restock",
            "price": {"current": 1499},
            "stock": {"web": 5, "shop": 0}
        }
        produkter.insert(0, fejk_produkt)
        # ------------------------------------

        for prod in produkter:
            prod_id = prod.get("id")
            namn = prod.get("name", "")
            namn_lower = namn.lower()
            if any(skrap_ord in namn_lower for skrap_ord in SVARTLISTA):
                continue 
            pris = prod.get("price", {}).get("current", "Okänt pris")
            lank = f"https://webhallen.com{prod_id}"
            stock_info = prod.get("stock", {})
            aktuellt_online = stock_info.get("web", 0)
            aktuellt_irl = stock_info.get("shop", 0)
            if prod_id not in produkt_databas:
                produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}
                continue
            forra_online = produkt_databas[prod_id]["online"]
            forra_irl = produkt_databas[prod_id]["irl"]
            if aktuellt_online > 0 and forra_online == 0:
                msg = f"🌐 **NYHET ONLINE!**\n**Produkt:** {namn}\n**Pris:** {pris} kr\n🔗 {lank}"
                skicka_till_discord(WEBHOOK_ONLINE, msg)
            if aktuellt_irl > 0 and forra_irl == 0:
                msg = f"🛒 **RESTOCK IRL-BUTIK!**\n**Produkt:** {namn}\n**Pris:** {pris} kr\n🏃‍♂️ Kolla butik: {lank}"
                skicka_till_discord(WEBHOOK_IRL, msg)
            produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}
    except Exception as e:
        print(f"Ett fel uppstod: {e}")

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
