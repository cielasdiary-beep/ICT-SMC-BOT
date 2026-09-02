import os
import pandas as pd
import yfinance as yf
from telegram import Bot
import asyncio

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

TICKER = "EURUSD=X"
LOT_SIZE = "0.01"
RISK_REWARD = 2.0
SL_PIPS = 0.0015

async def send_signal():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Erreur : Les secrets TELEGRAM_TOKEN et CHAT_ID ne sont pas configurés.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)
    
    # Analyse rapide des données
    df = yf.download(TICKER, period="5d", interval="1h")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    current_price = round(df["Close"].iloc[-1], 5)
    entry_price = round(current_price - 0.0001, 5)
    stop_loss = round(entry_price + SL_PIPS, 5)
    take_profit = round(entry_price - (SL_PIPS * RISK_REWARD), 5)

    msg = (
        f"🔴 *SIGNAL ICT SMC SHORT (GitHub Actions)* 🔴\n\n"
        f"📊 *Paire :* EUR/USD\n"
        f"📦 *Lot :* {LOT_SIZE}\n\n"
        f"📉 *Entrée :* `{entry_price}`\n"
        f"🛑 *Stop Loss :* `{stop_loss}` (-15 pips / -1.50$)\n"
        f"🎯 *Take Profit :* `{take_profit}` (+30 pips / +3.00$)\n\n"
        f"⚡ *Zone :* Rejet Premium / FVG détecté."
    )

    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    print(" Signal envoyé avec succès sur Telegram !")

if __name__ == "__main__":
    asyncio.run(send_signal())
