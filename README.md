Tienes razón, perdón. Aquí va en inglés:

---

# anonQ

A Q&A board that runs in your terminal. Anonymous by default — if you want an account, you get a 16-digit number like Mullvad does. That's it.

```
 anonQ  anonymous Q&A
────────────────────────────────────────────────
  Welcome to anonQ
  Twitter-style anonymous Q&A board

────────────────────────────────────────────────
  [1] Browse anonymously   [2] Create account   [3] Login   [q] quit
```

---

## Features

- Browse and post without an account
- If you create one, you get a 16-digit number (`1234-5678-9012-3456`) — that's your login, no email or password involved
- Like and unlike any post (♥ / ♡)
- Replies with inline threads
- View and delete your own posts when logged in
- Shared Firebase backend — posts are live, no setup needed on your end
- If Firebase is unreachable, the app keeps working locally for the session

---

## Requirements

- Python 3.11+
- Firebase is already configured, nothing to set up

---

## Setup

```bash
git clone https://github.com/your-username/anonq.git
cd anonq
pip install -r requirements.txt
python main.py
```

---

## How login works

When you create an account, anonQ generates a random 16-digit number:

```
1234-5678-9012-3456
```

That number is your only credential. It gets hashed with SHA-256 before being stored — the plain number is never saved anywhere.

Write it down. There's no recovery if you lose it.

---

## Project structure

```
anonq/
├── main.py             # Entry point and screen state machine
├── ui.py               # Terminal UI rendering (blessed)
├── posts.py            # Post/reply/like logic
├── auth.py             # Account generation and login
├── firebase_client.py  # Firestore REST API client (public key, safe to commit)
├── requirements.txt
└── README.md
```

---

## Firestore data model

```
posts/
  {post_id}/
    content       string
    created_at    timestamp
    likes         number
    account_hash  string | null   ← SHA-256 of account number, or null for anon

    replies/
      {reply_id}/
        content       string
        created_at    timestamp
        account_hash  string | null

accounts/
  {account_hash}/
    created_at    timestamp
```

---

## License

MIT
