import time
import requests
import json

# =========================================================================
# CONFIG
# =========================================================================
# Klistra in dina riktiga Discord-webhooks här
WEBHOOK_ONLINE = "https://discord.com"
WEBHOOK_IRL = "https://discord.com"

# ID på din Discord-roll för VIP-pings (Frivilligt, t.ex. "123456789012345678")
VIP_ROLE_ID = "" 

INTERVALL_SEKUNDER = 60

# OM DU KÖPER SCRAPERAPI / ZENROWS: Lägg din API-nyckel här (Annars lämna tom för lokal VPN)
SCRAPER_API_KEY = "" 
# =========================================================================

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
        print(f"Fel vid sändning till Discord: {e}")

def kolla_webhallen_pokemon():
    print(f"[{time.strftime('%H:%M:%S')}] Söker mot Webhallens dolda API...")
    
    # KORREKT API-LÄNK: Söker på "Pokemon TCG" sorterat på nyast först (24 produkter per sida)
    TARGET_URL = "https://webhallen.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        # Om du använder ett Scraping API för att runda Cloudflare
        if SCRAPER_API_KEY:
            proxy_url = f"http://scraperapi?api_key={SCRAPER_API_KEY}&url={TARGET_URL}"
            response = requests.get(proxy_url, timeout=30)
        else:
            # Kör lokalt (Kräver bra VPN för att inte bli blockerad över tid)
            response = requests.get(TARGET_URL, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] Felkod från Webhallen: {response.status_code} (Cloudflare blockering troligtvis)")
            return

        data = response.json()
        produkter = data.get("products", [])
            
        print(f"[{time.strftime('%H:%M:%S')}] SUCCÉ! Sökning klar. Analyserar {len(produkter)} produkter.")

        for prod in produkter:
            prod_id = str(prod.get("id"))
            namn = prod.get("name", "")
            namn_lower = namn.lower()

            # Svartlistefilter
            if any(skrap_ord in namn_lower for skrap_ord in SVARTLISTA):
                continue 

            pris = prod.get("price", {}).get("current", "Okänt")
            lank = f"https://webhallen.com{prod_id}"
            
            # Korrigerad bildhantering för Webhallens API-struktur
            bilder = prod.get("images", [])
            bild_url = ""
            if bilde_list := bilder:
                if isinstance(bilde_list, list) and len(bilde_list) > 0:
                    bild_url = bilde_list[0].get("large", "")
            
            stock_info = prod.get("stock", {})
            aktuellt_online = int(stock_info.get("web", 0))
            aktuellt_irl = int(stock_info.get("shop", 0))

            # FIX: Ändrat stavfel från Hatton_online till aktuellt_online
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
                text = f"**Produkt:** {namn}\n**Pris:** {pris} kr\n**Totalt i butiker nu:** {aktuellt_irl} st"
                skicka_till_discord(WEBHOOK_IRL, titel, text, lank, bild_url)

            # Uppdatera databasen med det nya lagersaldot
            produkt_databas[prod_id] = {"online": aktuellt_online, "irl": aktuellt_irl}

    except Exception as e:
        print(f"Fel vid anrop: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("   WEBHALLEN POKÉMON-BOT KÖRS MED NYTT API        ")
    print("==================================================")
    while True:
        kolla_webhallen_pokemon()
        time.sleep(INTERVALL_SEKUNDER)
