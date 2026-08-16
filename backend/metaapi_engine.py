"""
METAAPI_ENGINE.PY
------------------
MetaApi SDK ke zariye Cloud Trade Execution Engine.
Yeh file background mein bina Windows terminal ke Exness par trade lagayegi.

Is version mein shamil hai:
- Multiple trading strategies: Moving Average Crossover, RSI Reversal,
  ICT (Michael J. Huddleston), Wyckoff Method (Richard D. Wyckoff)
- User-selectable timeframe (1m se 4h tak) jo candle-fetch aur analysis
  dono mein use hoti hai
- Risk % aur Reward Ratio se automatic SL/TP calculation
- Optional custom lot size (na diya jaye to risk % se auto-calculate hota hai)
- Disconnect par MetaApi account ko bhi undeploy karna (taake billing na lage)

NOTE: MetaApi khud koi "trading intelligence" nahi rakhta - ye sirf order
execute karne wala cloud bridge hai. Market analysis (BUY/SELL decide karna)
hamesha humein khud karna hota hai.
"""
import os
import asyncio
from metaapi_cloud_sdk import MetaApi

META_API_TOKEN = os.environ.get("META_API_TOKEN")

# Website par dikhane/accept karne ke liye valid timeframes (1 minute se 4 ghante tak)
ALLOWED_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h"]
DEFAULT_TIMEFRAME = "15m"


def _closes_from_candles(candles):
    return [c["close"] for c in candles if "close" in c]


# ============================================================
# STRATEGY 1 & 2 - Simple indicator based (already existing)
# ============================================================

def decide_ma_crossover(candles):
    """Simple Moving Average Crossover (9 vs 21 period)."""
    closes = _closes_from_candles(candles)
    fast_period, slow_period = 9, 21
    if len(closes) < slow_period:
        return None
    fast_ma = sum(closes[-fast_period:]) / fast_period
    slow_ma = sum(closes[-slow_period:]) / slow_period
    if fast_ma > slow_ma:
        return "BUY"
    elif fast_ma < slow_ma:
        return "SELL"
    return None


def _calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[-i] - closes[-i - 1]
        if diff >= 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def decide_rsi(candles):
    """RSI Reversal: RSI<30 oversold -> BUY, RSI>70 overbought -> SELL."""
    closes = _closes_from_candles(candles)
    rsi = _calculate_rsi(closes)
    if rsi is None:
        return None
    if rsi < 30:
        return "BUY"
    elif rsi > 70:
        return "SELL"
    return None


# ============================================================
# STRATEGY 3 - ICT (Michael J. Huddleston / "Inner Circle Trader")
# Simplified version: liquidity sweep (stop hunt) + Fair Value Gap confluence
# ============================================================

def _find_fvg(candles):
    """Fair Value Gap dhoondta hai - 3-candle pattern jahan candle1 aur
    candle3 ke beech gap ho (candle2 body ko touch na kare).
    Returns 'bullish', 'bearish', ya None (recent-most FVG check karta hai)."""
    if len(candles) < 3:
        return None
    c1, c3 = candles[-3], candles[-1]
    if c1.get("high") is not None and c3.get("low") is not None and c1["high"] < c3["low"]:
        return "bullish"
    if c1.get("low") is not None and c3.get("high") is not None and c1["low"] > c3["high"]:
        return "bearish"
    return None


def decide_ict(candles, lookback=20):
    """
    ICT-style simplified logic (Michael J. Huddleston):
    1. Recent swing high/low (market structure) nikalte hain
    2. Liquidity sweep dhoondte hain: price swing low se neeche gaya phir
       band upar hua (bullish sweep / stop hunt) - ya ulta (bearish sweep)
    3. Agar sweep ke sath Fair Value Gap bhi usi direction mein mile,
       to confluence maan kar signal dete hain, warna skip
    """
    if len(candles) < lookback + 3:
        return None

    window = candles[-(lookback + 1):-1]
    swing_low = min(c["low"] for c in window if "low" in c)
    swing_high = max(c["high"] for c in window if "high" in c)

    last = candles[-1]
    fvg = _find_fvg(candles)

    bullish_sweep = last.get("low") is not None and last["low"] < swing_low and last.get("close", 0) > swing_low
    bearish_sweep = last.get("high") is not None and last["high"] > swing_high and last.get("close", 0) < swing_high

    if bullish_sweep and fvg == "bullish":
        return "BUY"
    if bearish_sweep and fvg == "bearish":
        return "SELL"
    return None


# ============================================================
# STRATEGY 4 - Wyckoff Method (Richard D. Wyckoff)
# Simplified version: trading range + Spring / Upthrust detection
# ============================================================

def decide_wyckoff(candles, range_lookback=25):
    """
    Wyckoff-style simplified logic (Richard D. Wyckoff):
    1. Ek trading range (accumulation/distribution zone) nikalte hain
       - range ki highest high aur lowest low
    2. 'Spring': price range low se neeche jhanke phir wapis range ke andar
       band ho -> smart money ne liquidity le li, accumulation complete -> BUY
    3. 'Upthrust': price range high se upar jhanke phir wapis andar band ho
       -> distribution complete -> SELL
    """
    if len(candles) < range_lookback + 1:
        return None

    window = candles[-(range_lookback + 1):-1]
    range_low = min(c["low"] for c in window if "low" in c)
    range_high = max(c["high"] for c in window if "high" in c)

    last = candles[-1]

    is_spring = last.get("low") is not None and last["low"] < range_low and last.get("close", 0) > range_low
    is_upthrust = last.get("high") is not None and last["high"] > range_high and last.get("close", 0) < range_high

    if is_spring:
        return "BUY"
    if is_upthrust:
        return "SELL"
    return None


STRATEGIES = {
    "auto": decide_ma_crossover,          # safe default
    "ma_crossover": decide_ma_crossover,
    "rsi": decide_rsi,
    "ict": decide_ict,                    # ICT - Michael J. Huddleston
    "wyckoff": decide_wyckoff,            # Wyckoff Method - Richard D. Wyckoff
}


async def _get_candles_safe(account, symbol, timeframe=DEFAULT_TIMEFRAME, limit=60):
    """Candles fetch karta hai, fail hone par empty list return karta hai
    (taake calling strategy gracefully 'no signal' de de, crash na ho)."""
    if timeframe not in ALLOWED_TIMEFRAMES:
        timeframe = DEFAULT_TIMEFRAME
    try:
        candles = await account.get_historical_candles(symbol, timeframe, None, limit)
        return candles or []
    except Exception as e:
        print(f"[{symbol}] Candle fetch error ({timeframe}): {str(e)}")
        return []


def _price_decimals(symbol):
    s = symbol.upper()
    if "XAU" in s or "BTC" in s:
        return 2
    return 5


# ============================================================
# MAIN TRADE EXECUTION
# ============================================================

async def execute_trade(user_data, signal_type=None):
    if not META_API_TOKEN:
        return {"success": False, "error": "META_API_TOKEN environment variable set nahi hai."}

    api = MetaApi(META_API_TOKEN)

    login = str(user_data.get("mt5_login"))
    password = user_data.get("mt5_password")
    server = user_data.get("mt5_server")
    symbol = user_data.get("symbol", "XAUUSD")
    risk_percent = float(user_data.get("risk_percent", 1.0))
    reward_ratio = float(user_data.get("reward_ratio", 2.0))
    custom_lot = user_data.get("lot_size")
    strategy_name = (user_data.get("strategy") or "auto").lower()
    timeframe = user_data.get("timeframe") or DEFAULT_TIMEFRAME
    if timeframe not in ALLOWED_TIMEFRAMES:
        timeframe = DEFAULT_TIMEFRAME

    try:
        existing = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination(
            accounts_filter={'limit': 1000}
        )
        accounts = existing['items'] if isinstance(existing, dict) else existing
        account = next((a for a in accounts if str(a.login) == login and a.server == server), None)

        if not account:
            print(f"[{login}] MetaApi par naya account configure ho raha hai...")
            account = await api.metatrader_account_api.create_account({
                'name': f'User_{login}',
                'type': 'cloud',
                'login': login,
                'password': password,
                'server': server,
                'platform': 'mt5',
                'magic': 1000
            })

        if account.state != 'DEPLOYED':
            print(f"[{login}] Account deploy ho raha hai...")
            await account.deploy()

        print(f"[{login}] Connection ka intezar...")
        await account.wait_connected()

        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        if signal_type is None:
            strategy_func = STRATEGIES.get(strategy_name, decide_ma_crossover)
            candles = await _get_candles_safe(account, symbol, timeframe)
            signal_type = strategy_func(candles)

        if signal_type is None:
            return {
                "success": True,
                "message": f"'{strategy_name}' strategy ({timeframe}) ne is waqt koi clear signal nahi diya, trade skip ki gayi.",
                "skipped": True
            }

        price_data = await connection.get_symbol_price(symbol)
        ask = price_data.get("ask")
        bid = price_data.get("bid")

        sl_fraction = risk_percent / 100.0
        tp_fraction = sl_fraction * reward_ratio
        digits = _price_decimals(symbol)

        if signal_type == "BUY":
            entry_price = ask
            stop_loss = round(entry_price * (1 - sl_fraction), digits)
            take_profit = round(entry_price * (1 + tp_fraction), digits)
        else:
            entry_price = bid
            stop_loss = round(entry_price * (1 + sl_fraction), digits)
            take_profit = round(entry_price * (1 - tp_fraction), digits)

        if custom_lot not in (None, "", 0):
            lot_size = float(custom_lot)
        else:
            lot_size = round(0.01 * risk_percent, 2)
        if lot_size < 0.01:
            lot_size = 0.01

        print(f"[{login}] Trade execution: {signal_type} {lot_size} lot on {symbol} "
              f"(SL={stop_loss}, TP={take_profit}, strategy={strategy_name}, timeframe={timeframe})")

        if signal_type == "BUY":
            result = await connection.create_market_buy_order(symbol, lot_size, stop_loss, take_profit)
        else:
            result = await connection.create_market_sell_order(symbol, lot_size, stop_loss, take_profit)

        return {
            "success": True,
            "message": f"{signal_type} trade successfully lag gayi! (strategy: {strategy_name}, timeframe: {timeframe})",
            "order_id": result.get('orderId'),
            "sl": stop_loss,
            "tp": take_profit,
            "lot_size": lot_size
        }

    except Exception as e:
        print(f"[{login}] MetaApi Error: {str(e)}")
        return {"success": False, "error": str(e)}


def run_for_user(user_data, signal_type=None):
    """Synchronous wrapper - app.py ka /api/run-cycle use karega."""
    return asyncio.run(execute_trade(user_data, signal_type))


# ============================================================
# DISCONNECT / UNDEPLOY - taake MetaApi credits waste na hon
# ============================================================

async def disconnect_account(login, server):
    if not META_API_TOKEN:
        return {"success": False, "error": "META_API_TOKEN environment variable set nahi hai."}

    api = MetaApi(META_API_TOKEN)
    try:
        existing = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination(
            accounts_filter={'limit': 1000}
        )
        accounts = existing['items'] if isinstance(existing, dict) else existing
        account = next((a for a in accounts if str(a.login) == str(login) and a.server == server), None)

        if not account:
            return {"success": True, "message": "MetaApi par account pehle se maujood nahi tha."}

        if account.state == 'DEPLOYED':
            print(f"[{login}] MetaApi account undeploy ho raha hai...")
            await account.undeploy()
            return {"success": True, "message": "MetaApi account undeploy ho gaya, ab billing nahi lagegi."}

        return {"success": True, "message": "MetaApi account pehle se hi undeployed tha."}

    except Exception as e:
        print(f"[{login}] MetaApi Disconnect Error: {str(e)}")
        return {"success": False, "error": str(e)}


def run_disconnect(login, server):
    """Synchronous wrapper - app.py ka /api/disconnect-mt5 use karega."""
    return asyncio.run(disconnect_account(login, server))
