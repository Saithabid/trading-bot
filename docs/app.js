document.addEventListener("DOMContentLoaded", () => {
    loadTradingViewChart("XAUUSD");

    const connectForm = document.getElementById("connectForm");
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");

    // Live Chart Render Function
    function loadTradingViewChart(symbol) {
        new TradingView.widget({
            "autosize": true,
            "symbol": "OANDA:" + symbol,
            "interval": "15",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "container_id": "tradingview_chart"
        });
    }

    // Symbol change event
    document.getElementById("symbol").addEventListener("change", (e) => {
        loadTradingViewChart(e.target.value);
    });

    // Account Submit Handler
    connectForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            mt5_login: document.getElementById("mt5_login").value,
            mt5_password: document.getElementById("mt5_password").value,
            mt5_server: document.getElementById("mt5_server").value,
            symbol: document.getElementById("symbol").value,
            risk_percent: document.getElementById("risk_percent").value
        };

        statusText.innerText = "Connecting...";
        
        try {
            const response = await fetch("https://trading-bot-se76.onrender.com/api/connect-mt5", {

                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {
                statusDot.classList.add("active");
                statusText.innerText = "Connected & Active";
                alert("Account Connect ho gaya hai! Auto Trading active hai.");
            } else {
                statusText.innerText = "Connection Failed";
                alert("Error: " + result.error);
            }
        } catch (err) {
            console.error(err);
            statusText.innerText = "Server Error";
        }
    });
});
