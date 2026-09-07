import os
import requests
import pandas as pd
import ta

# --- CONFIGURATION DU BOT ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOL = "EURUSDT"  # Paire Euro / Tether USD
INTERVAL = "1h"     # Graphique 1 heure
LIMIT = 200         # Augmenté à 200 pour s'assurer d'avoir assez d'historique

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
    """Récupère les données OHLCV de Binance pour la paire EURUSDT"""
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit={LIMIT}"
    response = requests.get(url)
    data = response.json()
    
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Réponse API invalide ou vide de Binance pour {SYMBOL}.")

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
    ])
    
    # Conversion des colonnes financières en float
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)
        
    return df

def analyze_market(df):
    """Calcule le RSI, la SMA50 et l'ATR pour évaluer le marché"""
    # 1. Calcul des indicateurs
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['sma50'] = ta.trend.sma_indicator(df['close'], window=50)
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    
    # Supression des lignes avec des valeurs non calculables (NaN)
    df_clean = df.dropna().copy()
    
    # Sécurité : vérifier qu'il reste suffisamment de données
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
    
    # 2. Logique de Signal + Calcul SL / TP avec Ratio 1:2
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
        
        # Si un signal BUY ou SELL est généré
        if signal != "NONE":
            message = (
                f"⚡ *NOUVEAU SIGNAL DE TRADING* ⚡\n\n"
                f"💱 **Paire :** `{SYMBOL}`\n"
                f"🎯 **Action :** *{signal}*\n\n"
                f"📌 **Prix d'entrée :** `{entry:.5f}` USDT\n"
                f"🛑 **Stop Loss (SL) :** `{sl:.5f}` USDT\n"
                f"🎯 **Take Profit (TP) :** `{tp:.5f}` USDT\n\n"
                f"📊 *Indicateurs :*\n"
                f"• RSI (14) : `{rsi}`\n"
                f"• SMA (50) : `{sma:.5f}`"
            )
            send_telegram_message(message)
            print(f"Signal {signal} envoyé sur Telegram !")
        else:
            print(f"Analyse réussie. Pas de signal fort détecté (RSI: {rsi}, Prix: {entry:.5f}).")
            
    except Exception as e:
        error_msg = f"⚠️ Erreur lors de l'exécution du Bot : {e}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    main()
