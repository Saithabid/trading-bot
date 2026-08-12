const firebaseConfig = {
  apiKey: "YAHAN_APNI_API_KEY_DALEIN",
  authDomain: "YAHAN_APNA_PROJECT.firebaseapp.com",
  projectId: "YAHAN_APNA_PROJECT_ID",
  appId: "YAHAN_APNA_APP_ID"
};

const BACKEND_URL = "https://trading-bot-se75.onrender.com";

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

function showDashboard() {
  document.getElementById("auth-screen").style.display = "none";
  document.getElementById("dashboard-screen").style.display = "block";
}

function showAuth() {
  document.getElementById("auth-screen").style.display = "block";
  document.getElementById("dashboard-screen").style.display = "none";
}

auth.onAuthStateChanged((user) => {
  if (user) {
    showDashboard();
  } else {
    showAuth();
  }
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
    .catch((error) => {
      document.getElementById("auth-error").innerText = error.message;
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
    } else {
      msgBox.style.color = "#ef4b6f";
      msgBox.innerText = data.error || "Kuch masla hua.";
    }
  } catch (err) {
    msgBox.style.color = "#ef4b6f";
    msgBox.innerText = "Backend se connect nahi ho saka.";
  }
}
