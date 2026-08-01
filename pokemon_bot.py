import datetime
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
                "color": 16711680, 
                "image": {"url": bild_url} if bild_url else None,
                "footer": {"text": "Pokémon TCG Live Set Monitor"}
            }
        ]
    }
    try:
        # Säkerställ att även webhook-anropet har headers och timeout
        headers = {"User-Agent": "Mozilla/5.0"}
        requests.post(webhook_url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Fel vid sändning till Discord: {e}")

def kolla_pokemon_sets():
    nuvarande_tid = datetime.datetime.utcnow().strftime('%H:%M:%S')
    print(f"[{nuvarande_tid}] UptimeRobot triggade sökning mot Pokémon TCG API...")
    
    API_URL = "https://pokemontcg.io"
    
    # SÄKERHET: Lägg till kompletta headers så att Pokémon API tror att vi är en vanlig webbläsare
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(API_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"Brandvägg blockerad. Felkod: {response.status_code}"

        data = response.json()
        sets = data.get("data", [])
        
        if not sets:
            return "Lyckades anropa men fick en tom lista från API:et."

        hittade_nya = 0
        # Vi tvingar den att skicka de 3 översta/senaste seten direkt
        for poke_set in sets[:3]:
            set_id = poke_set.get("id")
            namn = poke_set.get("name")
            serie = poke_set.get("series")
            slapp_datum = poke_set.get("releaseDate")
            totalt_kort = poke_set.get("total")
            bild_url = poke_set.get("images", {}).get("logo", "")
            
            lank = f"https://cardmarket.com{namn.replace(' ', '+')}"

            titel = f"🔥 NYTT POKÉMON SET DETEKTERAT: {namn.upper()}!"
            text = f"**Serie:** {serie}\n**Officiellt släpp:** {slapp_datum}\n**Antal kort i setet:** {totalt_kort} st\n\nDetta set är nu live!"
            
            skicka_till_discord(WEBHOOK_ONLINE, titel, text, lank, bild_url)
            set_databas.add(set_id)
            hittade_nya += 1

        return f"SÖKNING LYCKADES! Skickade {hittade_nya} set till Discord."

    except Exception as e:
        return f"Fel vid API-läsning: {e}"

@app.route('/')
def home():
    resultat = kolla_pokemon_sets()
    tidsstampel = datetime.datetime.utcnow().strftime('%H:%M:%S')
    return f"Status: {resultat} - Tid UTC: {tidsstampel}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
