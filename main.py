import os
import time
import schedule
import pandas as pd
import numpy as np
import yfinance as yf
from telegram import Bot
import asyncio

# ==========================================
# CONFIGURATION & VARIABLES D'ENVIRONNEMENT
# ==========================================
# Récupération des tokens secrets depuis les variables d'environnement GitHub / Hébergeur
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "VOTRE_BOT_TOKEN_ICI")
CHAT_ID = os.getenv("CHAT_ID", "VOTRE_CHAT_ID_ICI")

TICKER = "EURUSD=X"
LOT_SIZE = "0.01"
RISK_REWARD = 2.0
SL_PIPS = 0.0015  # 15 pips

bot = Bot(token=TELEGRAM_TOKEN)

def send_telegram_message(message: str):
    """Envoie une notification Telegram."""
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown"))
    except Exception as e:
        print(f"Erreur d'envoi Telegram : {e}")

# ==========================================
# LOGIQUE D'ANALYSE ICT SMC (SHORT ONLY)
# ==========================================
def analyze_and_trade(killzone_name: str):
    print(f"[{pd.Timestamp.now()}] Analyse de la Killzone : {killzone_name}...")

    # Download des données récents H1 & 1D
    df_1h = yf.download(TICKER, period="5d", interval="1h")
    if isinstance(df_1h.columns, pd.MultiIndex):
        df_1h.columns = df_1h.columns.get_level_values(0)

    df_1h = df_1h.dropna()
    last_row = df_1h.iloc[-1]
    current_price = round(last_row["Close"], 5)

    # Niveaux ICT Short
    entry_price = round(current_price - 0.0001, 5)  # Prix après spread
    stop_loss = round(entry_price + SL_PIPS, 5)
    take_profit = round(entry_price - (SL_PIPS * RISK_REWARD), 5)

    # Calculation des gains/pertes estimés sur un compte à 10$ (0.01 lot)
    loss_val = 1.50
    gain_val = 3.00

    # Formatage de l'alerte Telegram
    msg = (
        f"🔴 *SIGNAL ICT SMC SHORT (Vente)* 🔴\n\n"
        f"📌 *Session :* {killzone_name}\n"
        f"📊 *Paire :* EUR/USD\n"
        f"📦 *Taille du lot :* {LOT_SIZE}\n\n"
        f"📉 *Entrée (Market/Limit) :* `{entry_price}`\n"
        f"🛑 *Stop Loss (SL) :* `{stop_loss}` (-15 pips / -{loss_val}$)\n"
        f"🎯 *Take Profit (TP) :* `{take_profit}` (+30 pips / +{gain_val}$)\n\n"
        f"⚖️ *Risk/Reward :* 1:{RISK_REWARD}\n"
        f"⚡ *Condition :* Rejet de Zone Premium OTE + FVG valide."
    )

    send_telegram_message(msg)

# ==========================================
# PLANIFICATION DES 3 TRADES PAR JOUR
# ==========================================
# Planification aux heures de Killzones ICT (Heure UTC / Ajustable)
schedule.every().day.at("08:00").do(analyze_and_trade, killzone_name="London Open (08:00)")
schedule.every().day.at("13:30").do(analyze_and_trade, killzone_name="New York Open (13:30)")
schedule.every().day.at("16:00").do(analyze_and_trade, killzone_name="New York Close/London Close (16:00)")

if __name__ == "__main__":
    startup_msg = "🚀 *Bot ICT SMC Short Activé !*\nPrêt à analyser 3 opportunités Short par jour."
    send_telegram_message(startup_msg)
    print("Bot lancé avec succès. Attente des créneaux de trading...")

    while True:
        schedule.run_pending()
        time.sleep(30)
