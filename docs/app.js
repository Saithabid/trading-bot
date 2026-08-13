// ================= FIREBASE CONFIG =================
const firebaseConfig = {
    apiKey: "AIzaSyDxMYG9Colp9lyF39hTlHMzZsVEhByB0i0",
    authDomain: "trading-bot-c8725.firebaseapp.com",
    databaseURL: "https://trading-bot-c8725-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "trading-bot-c8725",
    storageBucket: "trading-bot-c8725.firebasestorage.app",
    messagingSenderId: "390734533806",
    appId: "1:390734533806:web:656cb940ff6c0d496c493f"
};
firebase.initializeApp(firebaseConfig);

const BACKEND_URL = "https://trading-bot-se75.onrender.com";

// ================= SCREEN ELEMENTS =================
const authScreen = document.getElementById("auth-screen");
const verifyScreen = document.getElementById("verify-screen");
const dashboardScreen = document.getElementById("dashboard-screen");

function showScreen(name) {
    authScreen.style.display = name === "auth" ? "flex" : "none";
    verifyScreen.style.display = name === "verify" ? "flex" : "none";
    dashboardScreen.style.display = name === "dashboard" ? "block" : "none";
}

// ================= AUTH FUNCTIONS =================
function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorEl = document.getElementById("auth-error");
    errorEl.innerText = "";

    firebase.auth().signInWithEmailAndPassword(email, password)
        .catch((err) => {
            errorEl.innerText = err.message;
        });
}

function signup() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorEl = document.getElementById("auth-error");
    errorEl.innerText = "";

    firebase.auth().createUserWithEmailAndPassword(email, password)
        .then((cred) => {
            return cred.user.sendEmailVerification();
        })
        .catch((err) => {
            errorEl.innerText = err.message;
        });
}

function logout() {
    firebase.auth().signOut();
}

function checkVerified() {
    const user = firebase.auth().currentUser;
    const msgEl = document.getElementById("verify-message");
    if (!user) return;

    user.reload().then(() => {
        if (user.emailVerified) {
            showScreen("dashboard");
            initDashboard(user);
        } else {
            msgEl.innerText = "Abhi tak verify nahi hua. Email check karein.";
        }
    });
}

function resendVerification() {
    const user = firebase.auth().currentUser;
    const msgEl = document.getElementById("verify-message");
    if (!user) return;

    user.sendEmailVerification()
        .then(() => {
            msgEl.innerText = "Email dobara bhej diya gaya hai.";
        })
        .catch((err) => {
            msgEl.innerText = err.message;
        });
}

// ================= AUTH STATE WATCHER =================
firebase.auth().onAuthStateChanged((user) => {
    if (!user) {
        showScreen("auth");
        return;
    }
    if (!user.emailVerified) {
        document.getElementById("verify-email-text").innerText = user.email;
        showScreen("verify");
        return;
    }
    showScreen("dashboard");
    initDashboard(user);
});

// ================= DASHBOARD LOGIC =================
let dashboardInitialized = false;

function initDashboard(user) {
    const emailBadge = document.getElementById("user-email-display");
    if (emailBadge) emailBadge.innerText = user.email;

    if (dashboardInitialized) return;
    dashboardInitialized = true;

    loadTradingViewChart("XAUUSD");

    document.getElementById("symbol").addEventListener("change", (e) => {
        loadTradingViewChart(e.target.value);
    });

    document.getElementById("connectForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        await connectMT5();
    });
}

function loadTradingViewChart(symbol) {
    document.getElementById("tradingview_chart").innerHTML = "";
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

async function connectMT5() {
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");
    const connectMsg = document.getElementById("connect-message");
    const user = firebase.auth().currentUser;

    if (!user) {
        statusText.innerText = "Not Logged In";
        connectMsg.innerText = "Pehle login karein.";
        return;
    }

    const payload = {
        user_id: user.uid,
        mt5_login: document.getElementById("mt5_login").value,
        mt5_password: document.getElementById("mt5_password").value,
        mt5_server: document.getElementById("mt5_server").value,
        symbol: document.getElementById("symbol").value,
        risk_percent: document.getElementById("risk_percent").value
    };

    statusText.innerText = "Connecting...";
    connectMsg.innerText = "";

    try {
        const response = await fetch(BACKEND_URL + "/api/connect-mt5", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (response.ok) {
            statusDot.classList.add("active");
            statusText.innerText = "Connected & Active";
            connectMsg.style.color = "#00c853";
            connectMsg.innerText = result.message || "Account Connect ho gaya hai! Auto Trading active hai.";
        } else {
            statusText.innerText = "Connection Failed";
            connectMsg.style.color = "#ff5252";
            connectMsg.innerText = "Error: " + (result.error || "Unknown error");
        }
    } catch (err) {
        console.error("Fetch Error:", err);
        statusText.innerText = "Server Error";
        connectMsg.innerText = "Backend se connection fail ho gaya. Render active nahi hai ya internet issue hai.";
    }
}
