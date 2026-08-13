document.addEventListener("DOMContentLoaded", () => {

    // 1. Chart Load Karne Ka Function
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

    // 2. Default Chart Load Karein (Gold)
    loadTradingViewChart("XAUUSD");

    const connectForm = document.getElementById("connectForm");
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");

    // 3. Jab User Coin Change Kare Toh Chart Update Ho
    document.getElementById("symbol").addEventListener("change", (e) => {
        loadTradingViewChart(e.target.value);
    });

    // 4. Form Submit Handler (Aapka Render URL Yahan Hai)
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
            // Aapka exact Render backend URL
            const response = await fetch("https://trading-bot-se75.onrender.com/api/connect-mt5", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (response.ok) {
                statusDot.classList.add("active");
                statusText.innerText = "Connected & Active";
                alert("Account Connect ho gaya hai! Auto Trading active hai.");
            } else {
                statusText.innerText = "Connection Failed";
                alert("Error: " + (result.error || "Kuch ghalat hua"));
            }
        } catch (err) {
            console.error("Fetch Error:", err);
            statusText.innerText = "Server Error";
            alert("Backend se connection fail ho gaya. Render active nahi hai ya internet issue hai.");
        }
    });
});
