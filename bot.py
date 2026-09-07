import os
import requests
import pandas as pd
import ta

# --- CONFIGURATION DU BOT ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Sur OKX, la paire s'écrit EUR-USDT
SYMBOL = "EUR-USDT"  
INTERVAL = "1H"     # 1 heure sur OKX
LIMIT = 100         # Nombre de bougies

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
    """Récupère les données OHLCV publiques depuis l'API Spot de OKX"""
    url = f"https://www.okx.com/api/v5/market/candles?instId={SYMBOL}&bar={INTERVAL}&limit={LIMIT}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code != 200:
        raise ValueError(f"Erreur API OKX (Code {response.status_code}) : {response.text}")
        
    data = response.json()
    
    if data.get("code") != "0" or not data.get("data"):
        raise ValueError(f"Impossible de récupérer les données OKX pour {SYMBOL} : {data.get('msg')}")

    # OKX renvoie les données sous forme: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
    raw_list = data["data"]
    
    # Inverser la liste pour remettre dans l'ordre chronologique
    raw_list.reverse()

    df = pd.DataFrame(raw_list, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'
    ])
    
    # Conversion des colonnes financières en float
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)
        
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
                f"💱 **Paire :** `EUR/USDT`\n"
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
            print(f"Analyse réussie via OKX. Pas de signal actuellement (RSI: {rsi}, Prix: {entry:.5f}).")
            
    except Exception as e:
        error_msg = f"⚠️ Erreur lors de l'exécution du Bot : {e}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    main()
