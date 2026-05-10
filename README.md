# anonQ

A Twitter-style anonymous Q&A board that runs in your terminal (TUI).  
No usernames. No passwords. Just a number, like [Mullvad VPN](https://mullvad.net).

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

- **Fully anonymous** — browse and post without any account
- **Account-number login** — get a 16-digit number like `1234-5678-9012-3456` to log in (no email, no username, no password)
- **Like / unlike** — toggle likes on any post (♥ / ♡), tracked per session
- **Replies** — reply to any post and view threads inline
- **My posts** — when logged in, view and delete your own posts
- **Shared Firebase backend** — all posts are live and shared with everyone, no setup needed
- **Graceful offline mode** — if Firebase is unreachable, the app still works locally for the session

---

## Requirements

- Python 3.11+
- That's it — Firebase is already configured and shared

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

This number is your only credential. It is **hashed with SHA-256** before being stored — the plain number is never saved anywhere.

Write it down. There is no recovery if you lose it.

---

## Project structure

```
anonq/
├── main.py             # App entry point and screen state machine
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
