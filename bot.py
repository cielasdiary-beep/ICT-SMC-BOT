import os
import requests
import pandas as pd
import ta
import yfinance as yf

# --- CONFIGURATION DU BOT ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ticker Yahoo Finance pour la paire EUR/USD
SYMBOL = "EURUSD=X"

def send_telegram_message(message):
    """Envoie un message formaté sur Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Erreur : Identifiants Telegram non configurés.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def get_market_data():
    """Récupère l'historique horaire depuis Yahoo Finance"""
    ticker = yf.Ticker(SYMBOL)
    # Récupère 7 jours de données en intervalle 1 heure (1h)
    df = ticker.history(period="7d", interval="1h")
    
    if df.empty:
        raise ValueError(f"Impossible de récupérer les données yfinance pour {SYMBOL}.")

    # On nettoie le nom des colonnes en minuscules
    df.columns = [c.lower() for c in df.columns]
    
    return df

def analyze_market(df):
    """Calcule le RSI, la SMA50 et l'ATR pour évaluer le marché"""
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['sma50'] = ta.trend.sma_indicator(df['close'], window=50)
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    
    df_clean = df.dropna().copy()
    
    if len(df_clean) < 1:
        raise ValueError("Pas assez de données valides après le calcul des indicateurs.")

    last = df_clean.iloc[-1]
    entry_price = last['close']
    rsi = round(last['rsi'], 2)
    sma = round(last['sma50'], 5)
    atr = last['atr']
    
    signal_type = "NONE"
    sl = 0.0
    tp = 0.0
    
    # Logique de Signal + Calcul SL / TP avec Ratio 1:2
    if rsi < 35 and entry_price < sma:
        signal_type = "BUY 🟢"
        sl = entry_price - (1.5 * atr)
        tp = entry_price + (3.0 * atr)
        
    elif rsi > 65 and entry_price > sma:
        signal_type = "SELL 🔴"
        sl = entry_price + (1.5 * atr)
        tp = entry_price - (3.0 * atr)

    return entry_price, rsi, sma, signal_type, sl, tp

def main():
    try:
        df = get_market_data()
        entry, rsi, sma, signal, sl, tp = analyze_market(df)
        
        if signal != "NONE":
            message = (
                f"⚡ *NOUVEAU SIGNAL DE TRADING* ⚡\n\n"
                f"💱 **Paire :** `EUR/USD`\n"
                f"🎯 **Action :** *{signal}*\n\n"
                f"📌 **Prix d'entrée :** `{entry:.5f}`\n"
                f"🛑 **Stop Loss (SL) :** `{sl:.5f}`\n"
                f"🎯 **Take Profit (TP) :** `{tp:.5f}`\n\n"
                f"📊 *Indicateurs :*\n"
                f"• RSI (14) : `{rsi}`\n"
                f"• SMA (50) : `{sma:.5f}`"
            )
            send_telegram_message(message)
            print(f"Signal {signal} envoyé sur Telegram !")
        else:
            print(f"Analyse réussie via yfinance. Pas de signal actuellement (RSI: {rsi}, Prix: {entry:.5f}).")
            
    except Exception as e:
        error_msg = f"⚠️ Erreur lors de l'exécution du Bot : {e}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    main()
