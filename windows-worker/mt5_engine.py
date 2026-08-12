"""
MT5_ENGINE.PY
--------------
Kisi bhi user ke (Firebase se aaye) credentials le kar:
connect -> analyze -> trade -> disconnect.
"""

import MetaTrader5 as mt5
import logging
from firebase_client import log_trade

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def connect_user(login, password, server):
    mt5.shutdown()
    initialized = mt5.initialize(login=int(login), password=password, server=server)
    if not initialized:
        logging.error(f"Connect FAIL for login {login} - {mt5.last_error()}")
        return False
    return True


def calculate_lot_size(balance, risk_percent, sl_distance_price, symbol_info):
    risk_amount = balance * (risk_percent / 100)
    contract_size = symbol_info.trade_contract_size
    if sl_distance_price <= 0 or contract_size <= 0:
        return 0.01
    lot = risk_amount / (sl_distance_price * contract_size)
    return max(0.01, round(lot, 2))


def place_trade(symbol, signal, atr, risk_percent):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return None
    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)

    tick = mt5.symbol_info_tick(symbol)
    account = mt5.account_info()
    if tick is None or account is None:
        return None

    sl_distance = atr * 1.5
    tp_distance = atr * 2.5

    if signal == "BUY":
        price = tick.ask
        sl, tp = price - sl_distance, price + tp_distance
        order_type = mt5.ORDER_TYPE_BUY
    else:
        price = tick.bid
        sl, tp = price + sl_distance, price - tp_distance
        order_type = mt5.ORDER_TYPE_SELL

    lot = calculate_lot_size(account.balance, risk_percent, sl_distance, symbol_info)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 123456,
        "comment": "auto-bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Trade FAIL - retcode {result.retcode} - {result.comment}")
        return None

    return {"signal": signal, "symbol": symbol, "lot": lot, "price": price, "sl": sl, "tp": tp}


def run_for_user(user):
    from strategy import analyze_market
    import datetime

    user_id = user["user_id"]
    connected = connect_user(user["mt5_login"], user["mt5_password"], user["mt5_server"])
    if not connected:
        return {"user_id": user_id, "status": "connect_failed"}

    result = analyze_market(user["symbol"])

    trade_result = None
    if result["signal"] in ("BUY", "SELL"):
        trade_result = place_trade(user["symbol"], result["signal"], result["atr"], user["risk_percent"])
        if trade_result:
            log_trade(user_id, {
                **trade_result,
                "reason": result["reason"],
                "timestamp": datetime.datetime.utcnow().isoformat(),
            })

    mt5.shutdown()
    return {"user_id": user_id, "status": "ok", "signal": result["signal"], "trade": trade_result}
