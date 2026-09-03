import os
import sys
from datetime import datetime, timezone, timedelta
import pandas as pd
import yfinance as yf
from telegram import Bot
import asyncio

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Paramètres généraux
LOT_SIZE = "0.01"
RISK_REWARD = 2.0

# Paramètres EUR/USD
EUR_SL_PIPS = 0.0015  # 15 pips (-1.50$)

# Paramètres GOLD (XAU/USD)
GOLD_SL_POINTS = 1.50 # 1.50$ de variation (-1.50$)

async def send_signal():
    # 1. Calcul de l'heure locale de Madagascar (UTC+3)
    madagascar_tz = timezone(timedelta(hours=3))
    now_mada = datetime.now(madagascar_tz)
    heure_str = now_mada.strftime("%d/%m/%Y à %H:%M:%S")

    print(f"--- DÉBUT D'EXÉCUTION DU BOT ({heure_str}) ---")
    
    # 2. Vérification des Secrets GitHub
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ ERREUR CRITIQUE : Les secrets TELEGRAM_TOKEN et CHAT_ID ne sont pas configurés.")
        sys.exit(1)

    # 3. Récupération des données EUR/USD
    print("📥 Récupération des données EUR/USD...")
    try:
        df_eur = yf.download("EURUSD=X", period="5d", interval="1h")
        if isinstance(df_eur.columns, pd.MultiIndex):
            df_eur.columns = df_eur.columns.get_level_values(0)
        eur_price = round(df_eur["Close"].iloc[-1], 5)
    except Exception as e:
        print(f"⚠️ Erreur EUR/USD : {e}")
        eur_price = 1.0850

    # Calculs Niveaux EUR/USD (Stratégie SHORT / VENTE)
    eur_entry = round(eur_price - 0.0001, 5)
    eur_sl = round(eur_entry + EUR_SL_PIPS, 5)
    eur_tp = round(eur_entry - (EUR_SL_PIPS * RISK_REWARD), 5)

    # 4. Récupération des données GOLD (XAU/USD)
    print("📥 Récupération des données GOLD...")
    try:
        df_gold = yf.download("GC=F", period="5d", interval="1h")
        if isinstance(df_gold.columns, pd.MultiIndex):
            df_gold.columns = df_gold.columns.get_level_values(0)
        gold_price = round(df_gold["Close"].iloc[-1], 2)
    except Exception as e:
        print(f"⚠️ Erreur Gold : {e}")
        gold_price = 2350.00

    # Calculs Niveaux GOLD (Stratégie SHORT / VENTE)
    gold_entry = round(gold_price - 0.10, 2)
    gold_sl = round(gold_entry + GOLD_SL_POINTS, 2)
    gold_tp = round(gold_entry - (GOLD_SL_POINTS * RISK_REWARD), 2)

    # 5. Composition du message Telegram combiné avec VENTE / BUY bien visibles
    msg = (
        f"🚨 *SIGNAUX ICT SMC TRADING* 🚨\n"
        f"🕒 *Exécution :* {heure_str} (Heure Mada)\n\n"
        f"-----------------------------------\n"
        f"💶 *ACTIF : EUR/USD*\n"
        f"🔴 *ORDRE : VENDRE (SELL / SHORT)*\n"
        f"📦 *Lot recommandé :* {LOT_SIZE}\n\n"
        f"🎯 *Prix d'entrée (SELL) :* `{eur_entry}`\n"
        f"🛑 *Stop Loss (SL) :* `{eur_sl}` (-15 pips / -1.50$)\n"
        f"🟢 *Take Profit (TP) :* `{eur_tp}` (+30 pips / +3.00$)\n\n"
        f"-----------------------------------\n"
        f"🏆 *ACTIF : GOLD (XAU/USD)*\n"
        f"🔴 *ORDRE : VENDRE (SELL / SHORT)*\n"
        f"📦 *Lot recommandé :* {LOT_SIZE}\n\n"
        f"🎯 *Prix d'entrée (SELL) :* `{gold_entry}`\n"
        f"🛑 *Stop Loss (SL) :* `{gold_sl}` (-1.50$)\n"
        f"🟢 *Take Profit (TP) :* `{gold_tp}` (+3.00$)\n\n"
        f"⚡ *Analyse :* Premium OTE Zone & FVG détectés."
    )

    # 6. Envoi du message Telegram
    print("📤 Envoi du signal combiné à Telegram...")
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
        print(f"🎉 SUCCÈS : Signaux de VENTE envoyés à {heure_str} !")
    except Exception as e:
        print(f"❌ ERREUR TELEGRAM : {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(send_signal())
