"""
METAAPI_ENGINE.PY
------------------
MetaApi SDK ke zariye Cloud Trade Execution Engine.
Yeh file background mein bina Windows terminal ke Exness par trade lagayegi.
"""
import os
import asyncio
from metaapi_cloud_sdk import MetaApi
META_API_TOKEN = os.environ.get("META_API_TOKEN")
async def execute_trade(user_data, signal_type="BUY"):
    if not META_API_TOKEN:
        return {"success": False, "error": "META_API_TOKEN environment variable set nahi hai."}
    # MetaApi initialize karein
    api = MetaApi(META_API_TOKEN)

    login = str(user_data.get("mt5_login"))
    password = user_data.get("mt5_password")
    server = user_data.get("mt5_server")
    symbol = user_data.get("symbol", "XAUUSD")
    risk = float(user_data.get("risk_percent", 1.0))
    try:
        # 1. Check karein ke MetaApi par account pehle se maujood hai ya nahi
        # (naya SDK version: get_accounts() ki jagah ab
        #  get_accounts_with_infinite_scroll_pagination() use hota hai)
        existing = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination(
            accounts_filter={'limit': 1000}
        )
        accounts = existing['items'] if isinstance(existing, dict) else existing
        account = next((a for a in accounts if str(a.login) == login and a.server == server), None)
        # Agar nahi hai toh naya add karein
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
        # 2. Account deploy karein (agar nahi hai)
        if account.state != 'DEPLOYED':
            print(f"[{login}] Account deploy ho raha hai...")
            await account.deploy()

        print(f"[{login}] Connection ka intezar...")
        await account.wait_connected()

        # 3. Connection establish karein
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        # 4. Lot Size calculate aur Trade execute karein
        lot_size = round(0.01 * risk, 2)
        print(f"[{login}] Trade execution: {signal_type} {lot_size} lot on {symbol}")

        if signal_type == "BUY":
            result = await connection.create_market_buy_order(symbol, lot_size, 0, 0)
        else:
            result = await connection.create_market_sell_order(symbol, lot_size, 0, 0)

        return {
            "success": True,
            "message": f"{signal_type} trade successfully lag gayi!",
            "order_id": result.get('orderId')
        }
    except Exception as e:
        print(f"[{login}] MetaApi Error: {str(e)}")
        return {"success": False, "error": str(e)}
def run_for_user(user_data, signal_type="BUY"):
    """
    Synchronous wrapper function:
    Isay main.py (worker) use karega taake asynchronous code easily chal sake.
    """
    return asyncio.run(execute_trade(user_data, signal_type))
