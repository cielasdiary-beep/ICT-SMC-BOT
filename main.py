import os
import requests
from datetime import datetime, timedelta
import pytz

# Configuration des variables d'environnement
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Erreur: Tokens Telegram non configurés.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Message envoyé sur Telegram avec succès.")
    else:
        print(f"❌ Échec de l'envoi: {response.text}")

def get_economic_news():
    """
    Récupère les événements économiques majeurs du jour (USD & EUR)
    """
    try:
        # Source calendrier économique léger et gratuit
        url = "https://nws.s3-us-west-2.amazonaws.com/economic_calendar.json"
        response = requests.get(url, timeout=10)
        
        # Formatage par défaut si indisponible ou simplifié
        today_str = datetime.now(pytz.timezone('Africa/Nairobi')).strftime("%Y-%d-%m")
        return "📅 *Pensez à vérifier Forex Factory / TradingView Calendar pour les dossiers Rouges (USD/EUR) de la journée.*"
    except Exception as e:
        return "⚠️ *Calendrier Economic non disponible à cette heure. Vérifiez ForexFactory.com.*"

def build_session_alert(event_type):
    mada_tz = pytz.timezone('Africa/Nairobi')
    now_mada = datetime.now(mada_tz)
    date_str = now_mada.strftime("%d/%m/%Y")
    time_str = now_mada.strftime("%H:%M")

    if event_type == "morning":
        msg = (
            f"🌅 *BONJOUR & BRIEFING DU MATIN* — {date_str}\n"
            f"───────────────\n"
            f"⏰ *Heure Mada :* {time_str} EAT\n\n"
            f"📊 *Objectif du Jour :*\n"
            f"• Analyse uniquement sur TradingView (UTC+3)\n"
            f"• Attendre la création de FVG / Liquidity Sweep\n"
            f"• Respecter scrupuleusement la règle No-News!\n\n"
            f"⚠️ *RAPPEL NEWS DU JOUR :*\n"
            f"Vérifiez vos dossiers Rouges 🔴 (USD / EUR) sur Forex Factory avant de prendre toute position."
        )
    elif event_type == "london_open":
        msg = (
            f"🔔 *KILLZONE : LONDON OPEN (11:00 EAT)*\n"
            f"───────────────\n"
            f"🏛️ *Market Status :* Ouverture de Londres\n"
            f"🎯 *Actifs cibles :* EUR/USD & XAU/USD\n\n"
            f"📋 *Checklist ICT/SMC :*\n"
            f"1️⃣ Prise de liquidité d'Asie (Asian High/Low) ?\n"
            f"2️⃣ Displacements M5/M15 détectés ?\n"
            f"3️⃣ FVG / Order Block clair pour l'entrée ?\n"
            f"4️⃣ Pas de news Majeure EUR à venir dans les 15 min ?"
        )
    elif event_type == "ny_open":
        msg = (
            f"🔔 *KILLZONE : NEW YORK OPEN (16:30 EAT)*\n"
            f"───────────────\n"
            f"🗽 *Market Status :* Ouverture Wall Street & Session US\n"
            f"🎯 *Actifs cibles :* EUR/USD & XAU/USD\n\n"
            f"⚠️ *ATTENTION VOLATILITÉ :*\n"
            f"• La session NY génère les plus gros mouvements sur le GOLD.\n"
            f"• Vérifiez impérativement les News US de 08:30 AM EST (15:30/16:30 Mada) !\n"
            f"• Si pas de configuration SMC propre ➔ Ne pas forcer."
        )
    elif event_type == "london_close":
        msg = (
            f"🔔 *KILLZONE : LONDON CLOSE / NY PM (19:00 EAT)*\n"
            f"───────────────\n"
            f"📉 *Market Status :* Clôture de Londres & Continuation US\n"
            f"⚠️ *Prudence :* Volume en baisse sur EUR/USD.\n"
            f"• Préférez sécuriser vos positions en cours (BE / Partial TP)."
        )
    else:
        msg = f"ℹ️ *Alerte Session ICT* - {time_str} EAT"

    return msg

if __name__ == "__main__":
    import sys
    # On passe le type d'événement en argument lors de l'exécution
    event_type = sys.argv[1] if len(sys.argv) > 1 else "morning"
    
    alert_message = build_session_alert(event_type)
    send_telegram_message(alert_message)
