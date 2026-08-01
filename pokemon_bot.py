import time
import requests
import os
from flask import Flask

# =========================================================================
# CONFIG
# =========================================================================
WEBHOOK_ONLINE = os.environ.get("WEBHOOK_ONLINE")
WEBHOOK_IRL = os.environ.get("WEBHOOK_IRL")
VIP_ROLE_ID = "" 
# =========================================================================

set_databas = set()
app = Flask('')

def skicka_till_discord(webhook_url, titel, text, lank, bild_url):
    content_ping = f"<@&{VIP_ROLE_ID}>" if VIP_ROLE_ID else ""
    payload = {
        "content": content_ping,
        "embeds": [
            {
                "title": titel,
                "description": text,
                "url": lank,
                "color": 16711680, # Röd Pokémon-färg
                "image": {"url": bild_url} if bild_url else None,
                "footer": {"text": "Pokémon TCG Live Set Monitor"}
            }
        ]
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Fel vid sändning till Discord: {e}")

def kolla_pokemon_sets():
    print(f"[{time.strftime('%H('%M:%S')}] UptimeRobot triggade sökning mot Pokémon TCG API...")
    
    # Officiellt, öppet API för Pokémon-kort och set (Sorterat på releasedatum)
    API_URL = "https://pokemontcg.io"
    
    try:
        response = requests.get(API_URL, timeout=15)
        if response.status_code != 200:
            return f"Pokémon API svarade med felkod: {response.status_code}"

        data = response.json()
        sets = data.get("data", [])
        
        hittade_nya = 0
        # Vi kollar de 15 senaste releaserna på marknaden
        for poke_set in sets[:15]:
            set_id = poke_set.get("id")
            namn = poke_set.get("name")
            serie = poke_set.get("series")
            slapp_datum = poke_set.get("releaseDate")
            totalt_kort = poke_set.get("total")
            
            # Hämtar officiell logotyp för setet
            bild_url = poke_set.get("images", {}).get("logo", "")
            
            # Skapar en direktlänk till Cardmarket för priskoll
            lank = f"https://cardmarket.com{namn.replace(' ', '+')}"

            # TESTLÄGE: Bortkommenterat så att du direkt ser att din Discord tar emot datan!
            # if set_id not in set_databas:
            #     set_databas.add(set_id)
            #     continue

            titel = f"🔥 NYTT POKÉMON SET DETEKTERAT: {namn.upper()}!"
            text = f"**Serie:** {serie}\n**Officiellt släpp:** {slapp_datum}\n**Antal kort i setet:** {totalt_kort} st\n\nDetta set är nu officiellt live i databasen för preorders och kortvärdering!"
            
            skicka_till_discord(WEBHOOK_ONLINE, titel, text, lank, bild_url)
            set_databas.add(set_id)
            hittade_nya += 1

        return f"Sökning klar. Hittade {len(sets)} set. Skickade {hittade_nya} till Discord."

    except Exception as e:
        return f"Fel vid API-läsning: {e}"

@app.route('/')
def home():
    resultat = kolla_pokemon_sets()
    return f"Status: {resultat} - Tid: {time.strftime('%H:%M:%S')}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
