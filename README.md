# Trading Bot - Multi-User (Exness MT5)

## GitHub par folder tarteeb (structure)

trading-bot/
├── .gitignore
├── README.md
├── backend/
│   ├── app.py
│   ├── mt5_engine.py
│   ├── strategy.py
│   ├── firebase_client.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── README.md

Koi bhi password/login is code mein kahin nahi hai. Har user ka MT5 data
Firebase database mein save hota hai, backend runtime par wahan se uthata hai.

## Firebase setup (ek dafa karna hai)

1. firebase.google.com par apne existing account se login karein
2. Naya project banayein
3. "Firestore Database" enable karein (test mode mein shuru kar sakte hain)
4. "Authentication" enable karein, "Email/Password" method on karein
5. Project Settings > Service Accounts > "Generate new private key" - ek .json file
   download hogi. Iska poora content hi wo FIREBASE_SERVICE_ACCOUNT value hai jo
   Render ke Environment Variables mein jayegi

## Render par deploy karna

1. Render dashboard > "New" > "Web Service"
2. GitHub repo select karein (trading-bot)
3. Root Directory: backend
4. Build Command: pip install -r requirements.txt
5. Start Command: python app.py
6. Environment > Add Environment Variable:
   Key: FIREBASE_SERVICE_ACCOUNT
   Value: (Firebase se mila poora JSON, ek line mein)
7. Deploy karein

## Zaroori: MT5 wala hissa

MT5 terminal sirf Windows par chalta hai. Render Linux hai - is liye asal trading
engine (mt5_engine.py) Windows laptop/VPS par hi chalegi, jahan MT5 terminal
khula/logged-in ho. Render par sirf website ka backend (login, MT5 details save
karna, dashboard data) chalega.
