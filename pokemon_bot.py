import time
import requests
import os
from threading import Thread
from flask import Flask

# =========================================================================
# DINA VERIFIERADE OCH FUNGERANDE LÄNKAR:
WEBHOOK_ONLINE = "https://discord.com/api/webhooks/1532837528095293460/HiAJpmPbQW0D-jfjC0x2dg5uz1bdMuOkjyHFS3qjFgSffARfvpUkXCGJ-mC2ObTTecDu"
WEBHOOK_IRL = "https://discord.com/api/webhooks/1532837638690574507/VeIXPTzXenrGIOny_0TbNCBOvtZqw7wOHBCBXmi7mX0URwHvwxtjOPqGdvilDFnKrlr5"
FLARE_URL = "https://mitt-flaresolverr.onrender.com"
INTERVALL_SEKUNDER = 60
# =========================================================================

app = Flask('')

@app.route('/')
def home():
    return "Boten är vid liv!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def skicka_till_discord(webhook_url, meddelande):
    try:
        requests.post(webhook_url, json={"content": meddelande})
    except Exception as e:
        print(f"Fel vid sändning: {e}")

def kolla_webhallen_pokemon():
    print(f"[{time.strftime('%H:%M:%S')}] Startar sökning...")
    
    # --- DET ULTIMATA DIREKT-TESTET ---
    # Vi skickar en äkta formaterad Pokémon-notis DIREKT på första sekunden!
    print("Tvingar fram en äkta produktnotis till Discord...")
    msg = "🌐 **LIVE-TEST: ÄKTA PRODUKT HITTAD!**\n**Produkt:** Pokémon TCG: Scarlet & Violet 8.5 Shrouded Fable - Elite Trainer Box\n**Pris:** 649 kr\n🔗 https://webhallen.com"
    skicka_till_discord(WEBHOOK_ONLINE, msg)
    # ----------------------------------
    
    # Pausa så den inte spammar
    time.sleep(INTERVALL_SEKUNDER)

if __name__ == "__main__":
    t = Thread(target=run_server)
    t.start()
    
    print("==================================================")
    print("   WEBHALLEN POKÉMON-BOT ÄR NU STARTAD (MOLN)     ")
    print("==================================================")
    
    # Kör direkt
    kolla_webhallen_pokemon()
