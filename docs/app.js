const firebaseConfig = {
  apiKey: "AIzaSyDxMYG9Colp9lyF39hTlHMzZsVEhByB0i0",
  authDomain: "trading-bot-c8725.firebaseapp.com",
  projectId: "trading-bot-c8725",
  appId: "1:390734533806:web:656cb940ff6c0d496c493f"
};

const BACKEND_URL = "https://trading-bot-se75.onrender.com";

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

function showScreen(id) {
  ["auth-screen", "verify-screen", "dashboard-screen"].forEach(s => {
    document.getElementById(s).style.display = (s === id) ? "block" : "none";
  });
}

auth.onAuthStateChanged((user) => {
  if (!user) {
    showScreen("auth-screen");
    return;
  }
  if (!user.emailVerified) {
    document.getElementById("verify-email-text").innerText = user.email;
    showScreen("verify-screen");
    return;
  }
  document.getElementById("user-email-display").innerText = user.email;
  showScreen("dashboard-screen");
  loadUserStatus();
  loadTrades();
});

function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  auth.signInWithEmailAndPassword(email, password)
    .catch((error) => {
      document.getElementById("auth-error").innerText = error.message;
    });
}

function signup() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  auth.createUserWithEmailAndPassword(email, password)
    .then((cred) => {
      return cred.user.sendEmailVerification();
    })
    .catch((error) => {
      document.getElementById("auth-error").innerText = error.message;
    });
}

function resendVerification() {
  const user = auth.currentUser;
  if (!user) return;
  const msg = document.getElementById("verify-message");
  user.sendEmailVerification()
    .then(() => { msg.style.color = "#22b07d"; msg.innerText = "Email dobara bhej diya gaya."; })
    .catch((error) => { msg.style.color = "#ef4b6f"; msg.innerText = error.message; });
}

function checkVerified() {
  const user = auth.currentUser;
  if (!user) return;
  const msg = document.getElementById("verify-message");
  user.reload().then(() => {
    if (user.emailVerified) {
      window.location.reload();
    } else {
      msg.style.color = "#ef4b6f";
      msg.innerText = "Abhi tak verify nahi hua. Email check karein.";
    }
  });
}

function logout() {
  auth.signOut();
}

async function connectMT5() {
  const user = auth.currentUser;
  if (!user) return;

  const payload = {
    user_id: user.uid,
    mt5_login: document.getElementById("mt5_login").value,
    mt5_password: document.getElementById("mt5_password").value,
    mt5_server: document.getElementById("mt5_server").value,
    symbol: document.getElementById("symbol").value,
    risk_percent: parseFloat(document.getElementById("risk_percent").value)
  };

  const msgBox = document.getElementById("connect-message");
  msgBox.style.color = "#22b07d";
  msgBox.innerText = "Bhej rahe hain...";

  try {
    const response = await fetch(`${BACKEND_URL}/api/connect-mt5`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();

    if (response.ok) {
      msgBox.style.color = "#22b07d";
      msgBox.innerText = "MT5 account jorh diya gaya!";
      loadUserStatus();
    } else {
      msgBox.style.color = "#ef4b6f";
      msgBox.innerText = data.error || "Kuch masla hua.";
    }
  } catch (err) {
    msgBox.style.color = "#ef4b6f";
    msgBox.innerText = "Backend se connect nahi ho saka.";
  }
}

async function loadUserStatus() {
  const user = auth.currentUser;
  if (!user) return;
  const box = document.getElementById("mt5-status-box");
  box.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch(`${BACKEND_URL}/api/user-status?user_id=${user.uid}`);
    const data = await response.json();

    if (data.connected) {
      box.classList.add("connected");
      box.innerHTML = `
        <p class="status-title">✅ MT5 Connected <span class="status-badge">${data.active ? 'Active' : 'Paused'}</span></p>
        <p>Account: ${data.mt5_login_masked}</p>
        <p>Server: ${data.mt5_server}</p>
        <p>Symbol: ${data.symbol} | Risk: ${data.risk_percent}%</p>
      `;
    } else {
      box.classList.remove("connected");
      box.innerHTML = `<p class="status-title">⚠️ Koi MT5 account nahi jura</p><p>Neeche form se add karein.</p>`;
    }
  } catch (err) {
    box.innerHTML = "<p>Status load nahi ho saka.</p>";
  }
}

async function loadTrades() {
  const user = auth.currentUser;
  if (!user) return;
  const list = document.getElementById("trades-list");

  try {
    const response = await fetch(`${BACKEND_URL}/api/trades?user_id=${user.uid}`);
    const data = await response.json();

    if (!data.trades || data.trades.length === 0) {
      list.innerHTML = `<p class="empty-note">Abhi tak koi trade nahi hui.</p>`;
      return;
    }

    list.innerHTML = data.trades.map(t => `
      <div class="trade-item">
        <span class="trade-signal ${t.signal === 'BUY' ? 'buy' : 'sell'}">${t.signal}</span>
        <span>${t.symbol} @ ${t.price}</span>
        <span>${t.lot} lot</span>
      </div>
    `).join("");
  } catch (err) {
    list.innerHTML = `<p class="empty-note">Trades load nahi ho sake.</p>`;
  }
}
