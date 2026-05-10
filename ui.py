import blessed
import textwrap
import datetime
import os
import sys
import auth

term = blessed.Terminal()

BRAND = "anonQ"
BLUE = term.blue
ACCENT = term.cyan
MUTED = term.bright_black
BOLD = term.bold
DIM = term.dim
RED = term.red
GREEN = term.green
YELLOW = term.yellow
WHITE = term.white
ORANGE = term.color(208)
FIREBASE_RED = term.color(196)

# Mouse hitboxes for footer buttons: (x1, x2, y, command)
_HITBOXES = []
_LAST_OPTIONS = []

def clear():
    if sys.platform == "win32":
        os.system("cls")
    else:
        print(term.clear, end="", flush=True)

def draw_firebase_badge():
    text = "Firebase"
    gradient = ORANGE + text[:4] + FIREBASE_RED + text[4:]
    badge = f"{MUTED}Powered by {term.normal}{gradient}"
    w = term.width or 80
    h = term.height or 24
    print(term.save + term.move_xy(w - len("Powered by Firebase") - 2, h - 1) + badge + term.normal + term.restore, end="", flush=True)

def header(title="", subtitle=""):
    w = term.width or 80
    print(term.clear_eol + BLUE + BOLD + BRAND + term.normal + (f" {MUTED}│{term.normal} {BOLD}{title}" if title else ""))
    if subtitle:
        print(term.clear_eol + MUTED + subtitle + term.normal)
    print(MUTED + "─" * w + term.normal)

def footer(options):
    global _HITBOXES, _LAST_OPTIONS
    _LAST_OPTIONS = options
    render_footer_line(None) # Initial render without hover

def render_footer_line(hover_key=None):
    global _HITBOXES
    _HITBOXES = []
    w = term.width or 80
    y = term.height - 2
    
    parts = []
    current_x = 2
    
    for key, label in _LAST_OPTIONS:
        is_hovered = (key.lower() == hover_key)
        key_styled = (term.reverse + term.bold if is_hovered else ACCENT + BOLD) + key.upper() + term.normal
        label_styled = (term.underline if is_hovered else "") + label + term.normal
        
        part = f"{key_styled} {label_styled}"
        parts.append(part)
        
        p_len = len(key) + 1 + len(label)
        _HITBOXES.append((current_x, current_x + p_len, y, key.lower()))
        current_x += p_len + 4
    
    footer_text = f" {MUTED}│{term.normal} ".join(parts)
    print(term.save + term.move_xy(2, y) + term.clear_eol + footer_text + term.restore, end="", flush=True)
    draw_firebase_badge()

def wait_for_input():
    with term.cbreak(), term.keypad():
        print(term.hide_cursor + term.mouse_button_pressed, end="", flush=True)
        try:
            last_hover = None
            while True:
                val = term.inkey(timeout=0.05)
                
                if val.code == term.KEY_MOUSE:
                    if hasattr(val, 'x') and hasattr(val, 'y'):
                        current_hover = None
                        for x1, x2, y, cmd in _HITBOXES:
                            if x1 <= val.x <= x2 and val.y == y:
                                current_hover = cmd
                                break
                        
                        if current_hover != last_hover:
                            render_footer_line(current_hover)
                            last_hover = current_hover
                        
                        if current_hover:
                            # We check for button press (left click usually 0)
                            # val[0] or similar, but for simplicity: click = interaction
                            return current_hover
                
                if val:
                    if val.is_sequence:
                        if val.code == term.KEY_RESIZE: return "resize"
                    else:
                        k = str(val).lower()
                        if k: return k
        finally:
            print(term.normal_cursor + term.mouse_button_released, end="", flush=True)

def prompt(msg, secret=False):
    print(term.normal_cursor + term.move_xy(2, term.height - 2) + term.clear_eol + ACCENT + "> " + term.normal + msg + ": ", end="", flush=True)
    if secret:
        import getpass
        res = getpass.getpass("")
    else:
        res = input()
    print(term.move_xy(0, term.height - 2) + term.clear_eol, end="", flush=True)
    return res

def status(msg, kind="info"):
    colors = {"info": ACCENT, "ok": GREEN, "err": RED, "warn": YELLOW}
    symbols = {"info": "ℹ", "ok": "✔", "err": "✖", "warn": "⚠"}
    c = colors.get(kind, WHITE)
    s = symbols.get(kind, "•")
    w = term.width or 80
    txt = f" {s} {msg} "
    padding = (w - len(txt)) // 2
    print(term.save + term.move_y(0) + term.on_black + c + " " * padding + txt + " " * (w - padding - len(txt)) + term.normal + term.restore, end="", flush=True)

def fmt_time(ts):
    if ts is None: return "just now"
    try:
        dt = ts if hasattr(ts, "timestamp") else None
        if not dt: return "just now"
        now = datetime.datetime.now(tz=dt.tzinfo)
        diff = now - dt
        s = int(diff.total_seconds())
        if s < 60: return f"{s}s ago"
        elif s < 3600: return f"{s // 60}m ago"
        elif s < 86400: return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception: return ""

def render_post(post, index=None, show_index=True, mine=False, liked=False):
    w = min(term.width or 80, 70)
    content = post.get("content", "")
    likes = post.get("likes", 0)
    ts = fmt_time(post.get("created_at"))
    post_id = post.get("id", "")[:8]

    idx = f"{BOLD}{index}.{term.normal} " if show_index and index else ""
    tag = f"{MUTED}#{post_id}{term.normal}"
    if mine: tag = f"{GREEN}[yours]{term.normal} {tag}"
    
    header_line = f" {idx}{tag}"
    wrapped = textwrap.wrap(content, width=w - 4)
    content_lines = [f"  {line}" for line in wrapped]
    
    heart = RED + "♥" + term.normal if liked else MUTED + "♡" + term.normal
    footer_line = f"  {heart} {likes}  ·  {ts}"
    
    return f"{header_line}\n" + "\n".join(content_lines) + f"\n{footer_line}\n"

def paginate_posts(posts_list, account_hash=None, session_likes=None, page_size=4):
    if session_likes is None: session_likes = set()
    total = len(posts_list)
    page = 0
    is_admin = auth.is_admin(account_hash)
    while True:
        clear()
        header("Feed", f"{total} posts")
        start = page * page_size
        end = min(start + page_size, total)
        chunk = posts_list[start:end]

        has_own_post = False
        for i, post in enumerate(chunk, start=start + 1):
            mine = account_hash and post.get("account_hash") == account_hash
            if mine: has_own_post = True
            liked = post.get("id") in session_likes
            print(render_post(post, i, mine=mine, liked=liked))

        nav = []
        if page > 0: nav.append(("p", "prev"))
        if end < total: nav.append(("n", "next"))
        nav += [("r", "reply"), ("l", "like/unlike")]
        if is_admin or (account_hash and has_own_post):
            nav.append(("d", "delete"))
        nav.append(("b", "back"))
        footer(nav)

        choice = wait_for_input()
        if choice == "resize": continue
        if choice == "n" and end < total: page += 1
        elif choice == "p" and page > 0: page -= 1
        elif choice == "b": return None, None
        elif choice == "r":
            idx = prompt("Post number to reply to").strip()
            try: return "reply", posts_list[int(idx) - 1]
            except Exception: pass
        elif choice == "l":
            idx = prompt("Post number to like/unlike").strip()
            try: return "toggle_like", posts_list[int(idx) - 1]
            except Exception: pass
        elif choice == "d" and (is_admin or (account_hash and has_own_post)):
            idx = prompt("Post number to delete").strip()
            try: return "delete", posts_list[int(idx) - 1]
            except Exception: pass
