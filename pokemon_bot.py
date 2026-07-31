import time
import requests
import os
from threading import Thread
from flask import Flask

# =========================================================================
# DINA VERIFIERADE OCH FUNGERANDE LÄNKAR:
WEBHOOK_ONLINE = "https://discord.com/api/webhooks/1532837528095293460/HiAJpmPbQW0D-jfjC0x2dg5uz1bdMuOkjyHFS3qjFgSffARfvpUkXCGJ-mC2ObTTecDu"
WEBHOOK_IRL = "https://discord.com/api/webhooks/1532837638690574507/VeIXPTzXenrGIOny_0TbNCBOvtZqw7wOHBCBXmi7mX0URwHvwxtjOPqGdvilDFnKrlr5"
FLARE_URL = "https://mitt-flaresolverr.onrender.com/"
INTERVALL_SEKUNDER = 60
# =========================================================================

SVARTLISTA = ["gosedjur", "plush", "mugg", "nyckelring", "pussel", "t-shirt", "keps", "ryggsäck", "bok", "figurer", "lampa"]
produkt_databas = {}

# En kontroll för att se till att testnotisen bara skickas EN gång per start
TEST_PRODUKT_TRIGGAD = False

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
    global TEST_PRODUKT_TRIGGAD
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

        # --- SKAPA EN FEJKAD PRODUKT FÖR ATT TESTA DESIGNEN ---
        # Vi lägger till en produkt som boten inte sett i minnet på förra sekunderna,
        # men vi tvingar databasen att låtsas att den var slutsåld (0) innan så den triggar notisen.
        fejk_id = 888888
        fejk_produkt = {
            "id": fejk_id,
            "name": "Pokémon TCG: Shrouded Fable - Booster Box (Förbeställning)",
            "price": {"current": 1649},
            "stock": {"web": 24, "shop": 0}
        }
        produkter.insert(0, fejk_produkt)
        
        if fejk_id not in produkt_databas and not TEST_PRODUKT_TRIGGAD:
            # Vi lurar botens minne att produkten fanns men hade 0 i lager nyss
            produkt_databas[fejk_id] = {"online": 0, "irl": 0}
            TEST_PRODUKT_TRIGGAD = True
        # ------------------------------------------------------

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
