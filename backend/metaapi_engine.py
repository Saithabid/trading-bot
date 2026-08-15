"""
METAAPI_ENGINE.PY
------------------
MetaApi SDK ke zariye Cloud Trade Execution Engine.
Yeh file background mein bina Windows terminal ke Exness par trade lagayegi.

Is version mein shamil hai:
- Multiple trading strategies (Moving Average Crossover, RSI Reversal, Auto)
- Risk % aur Reward Ratio se automatic SL/TP calculation
- Optional custom lot size (na diya jaye to risk % se auto-calculate hota hai)
- Disconnect par MetaApi account ko bhi undeploy karna (taake billing na lage)

NOTE: MetaApi khud koi "trading intelligence" nahi rakhta - ye sirf order
execute karne wala cloud bridge hai. Market analysis (BUY/SELL decide karna)
hamesha humein khud karna hota hai - isi liye "Auto" strategy neeche
Moving Average Crossover use karti hai (hardcoded hamesha-BUY ki jagah,
jo pehle tha aur khatarnak tha).
"""
import os
import asyncio
from metaapi_cloud_sdk import MetaApi

META_API_TOKEN = os.environ.get("META_API_TOKEN")


# ============================================================
# STRATEGIES - candles se BUY / SELL / None (no signal) decide karti hain
# ============================================================

def _closes_from_candles(candles):
    return [c["close"] for c in candles if "close" in c]


def decide_ma_crossover(candles, fast_period=9, slow_period=21):
    """
    Simple Moving Average Crossover:
    Fast MA (9) > Slow MA (21) -> BUY trend
    Fast MA (9) < Slow MA (21) -> SELL trend
    """
    closes = _closes_from_candles(candles)
    if len(closes) < slow_period:
        # Kaafi data nahi hai - safe side, trade skip
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
    gains = []
    losses = []
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
    """
    RSI Reversal:
    RSI < 30 (oversold) -> BUY
    RSI > 70 (overbought) -> SELL
    Beech mein -> No signal (trade skip)
    """
    closes = _closes_from_candles(candles)
    rsi = _calculate_rsi(closes)
    if rsi is None:
        return None
    if rsi < 30:
        return "BUY"
    elif rsi > 70:
        return "SELL"
    return None


STRATEGIES = {
    "auto": decide_ma_crossover,          # default / safe fallback
    "ma_crossover": decide_ma_crossover,
    "rsi": decide_rsi,
}


async def _get_candles_safe(account, symbol, timeframe="15m", limit=50):
    """Candles fetch karta hai, fail hone par empty list return karta hai
    (taake calling strategy gracefully 'no signal' de de, crash na ho)."""
    try:
        candles = await account.get_historical_candles(symbol, timeframe, None, limit)
        return candles or []
    except Exception as e:
        print(f"[{symbol}] Candle fetch error: {str(e)}")
        return []


def _price_decimals(symbol):
    """Symbol ke hisaab se rounding ka andaza - exact broker digits nahi
    maloom hote is layer par, isliye ye ek reasonable approximation hai."""
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

    try:
        # 1. Account MetaApi par maujood hai ya nahi check karein
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

        # 2. Deploy (agar nahi hai)
        if account.state != 'DEPLOYED':
            print(f"[{login}] Account deploy ho raha hai...")
            await account.deploy()

        print(f"[{login}] Connection ka intezar...")
        await account.wait_connected()

        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        # 3. Signal decide karein (agar bahar se explicitly nahi diya gaya)
        if signal_type is None:
            strategy_func = STRATEGIES.get(strategy_name, decide_ma_crossover)
            candles = await _get_candles_safe(account, symbol)
            signal_type = strategy_func(candles)

        if signal_type is None:
            return {
                "success": True,
                "message": f"'{strategy_name}' strategy ne is waqt koi clear signal nahi diya, trade skip ki gayi.",
                "skipped": True
            }

        # 4. Current price maloom karein (SL/TP calculate karne ke liye)
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

        # 5. Lot size - agar user ne khud diya hai to wahi use karein, warna auto
        if custom_lot not in (None, "", 0):
            lot_size = float(custom_lot)
        else:
            lot_size = round(0.01 * risk_percent, 2)
        if lot_size < 0.01:
            lot_size = 0.01

        print(f"[{login}] Trade execution: {signal_type} {lot_size} lot on {symbol} "
              f"(SL={stop_loss}, TP={take_profit}, strategy={strategy_name})")

        if signal_type == "BUY":
            result = await connection.create_market_buy_order(symbol, lot_size, stop_loss, take_profit)
        else:
            result = await connection.create_market_sell_order(symbol, lot_size, stop_loss, take_profit)

        return {
            "success": True,
            "message": f"{signal_type} trade successfully lag gayi! (strategy: {strategy_name})",
            "order_id": result.get('orderId'),
            "sl": stop_loss,
            "tp": take_profit,
            "lot_size": lot_size
        }

    except Exception as e:
        print(f"[{login}] MetaApi Error: {str(e)}")
        return {"success": False, "error": str(e)}


def run_for_user(user_data, signal_type=None):
    """
    Synchronous wrapper function:
    Isay app.py ka /api/run-cycle use karega.
    signal_type na diya jaye to user ki chuni hui strategy khud decide karegi.
    """
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
