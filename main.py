import sys
import ui
import auth
import posts


def screen_welcome(session):
    while True:
        ui.clear()
        ui.header("Welcome", "Twitter-style anonymous Q&A")
        print()
        print(f"  {ui.BLUE}{ui.BOLD}anonQ{ui.term.normal} is a minimal, private social space.")
        print(f"  {ui.MUTED}Made by jzadl{ui.term.normal}")
        print()
        ui.footer([("1", "Browse"), ("2", "Register"), ("3", "Login"), ("q", "quit")])
        
        choice = ui.wait_for_input()
        if choice == "resize":
            continue
        elif choice == "1":
            session["account_hash"] = None
            return "feed"
        elif choice == "2":
            return "create_account"
        elif choice == "3":
            return "login"
        elif choice == "q":
            return "quit"


def screen_create_account(session):
    ui.clear()
    ui.header("Create Account")
    print()
    print("  Your account number is like a password.")
    print(ui.MUTED + "  Write it down — there's no recovery." + ui.term.normal)
    print()
    number = auth.create_account()
    print(ui.GREEN + ui.BOLD + f"  Your account number:" + ui.term.normal)
    print()
    print(ui.ACCENT + ui.BOLD + f"    {number}" + ui.term.normal)
    print()
    print(ui.MUTED + "  Keep this safe. It's the only way to log in." + ui.term.normal)
    print()
    input("  Press Enter to continue...")
    session["account_hash"] = auth.hash_account(number)
    return "feed"


def screen_login(session):
    ui.clear()
    ui.header("Login")
    print()
    number = ui.prompt("Enter your account number").strip()
    if not number:
        return "welcome"
    hashed = auth.login(number)
    if hashed:
        session["account_hash"] = hashed
        ui.status("Logged in!", "ok")
        import time; time.sleep(0.8)
        return "feed"
    else:
        ui.status("Account not found. Check your number.", "err")
        input("  Press Enter to go back...")
        return "welcome"


def screen_feed(session):
    account_hash = session.get("account_hash")
    session_likes = session.setdefault("liked_posts", set())
    while True:
        ui.clear()
        ui.header("Loading feed...")
        try:
            all_posts = posts.get_posts(50)
        except Exception as e:
            ui.status(f"Error loading posts: {e}", "err")
            input("  Press Enter to go back...")
            return "welcome"

        action, post = ui.paginate_posts(all_posts, account_hash=account_hash, session_likes=session_likes)

        if action is None:
            return "menu"
        elif action == "toggle_like":
            did_like = posts.toggle_like(post["id"], session_likes)
            if did_like:
                ui.status("Liked! ♥", "ok")
            else:
                ui.status("Unliked.", "info")
            import time; time.sleep(0.5)
        elif action == "delete":
            is_admin = auth.is_admin(account_hash)
            mine = post.get("account_hash") == account_hash
            if is_admin or mine:
                confirm = ui.prompt(f"Type 'yes' to delete post #{post['id'][:8]}").strip().lower()
                if confirm == "yes":
                    ok = posts.delete_post(post["id"], account_hash)
                    if ok:
                        ui.status("Deleted successfully.", "ok")
                    else:
                        ui.status("Error: Could not delete from server.", "err")
                else:
                    ui.status("Deletion cancelled.", "info")
            else:
                ui.status("You don't have permission to delete this.", "err")
            import time; time.sleep(0.8)
        elif action == "reply":
            return "reply", post


def screen_new_post(session):
    account_hash = session.get("account_hash")
    ui.clear()
    ui.header("New Post")
    print()
    print(ui.MUTED + "  Write your post (max 280 chars). Empty line to cancel." + ui.term.normal)
    print()
    content = ui.prompt("Post content").strip()
    if not content:
        return "feed"
    if len(content) > 280:
        ui.status("Too long! Max 280 characters.", "err")
        input("  Press Enter...")
        return "new_post"
    posts.create_post(content, account_hash=account_hash)
    ui.status("Posted!", "ok")
    import time; time.sleep(0.8)
    return "feed"


def screen_reply(session, post):
    account_hash = session.get("account_hash")
    is_admin = auth.is_admin(account_hash)
    while True:
        ui.clear()
        ui.header("Reply")
        print()
        print(ui.render_post(post, show_index=False))
        replies = posts.get_replies(post["id"])
        
        has_own_reply = False
        if replies:
            print(ui.MUTED + "  Replies:" + ui.term.normal)
            for i, r in enumerate(replies, 1):
                ts = ui.fmt_time(r.get("created_at"))
                mine = account_hash and r.get("account_hash") == account_hash
                if mine: has_own_reply = True
                tag = ui.GREEN + "[yours] " + ui.term.normal if mine else ""
                print(ui.MUTED + f"    {i}. └ " + ui.term.normal + tag + r.get("content", "") + ui.MUTED + f"  {ts}" + ui.term.normal)
            print()
        else:
            print(ui.MUTED + "  No replies yet." + ui.term.normal)
            print()

        nav = [("r", "reply"), ("b", "back")]
        if is_admin or has_own_reply:
            nav.insert(1, ("d", "delete"))
        ui.footer(nav)

        choice = ui.wait_for_input()
        if choice == "resize":
            continue
        elif choice == "b":
            return "feed"
        elif choice == "r":
            content = ui.prompt("Your reply (empty to cancel)").strip()
            if content:
                posts.add_reply(post["id"], content, account_hash=account_hash)
                ui.status("Reply posted!", "ok")
                import time; time.sleep(0.8)
        elif choice == "d" and (is_admin or has_own_reply):
            idx = ui.prompt("Reply number to delete").strip()
            try:
                target = replies[int(idx) - 1]
                target_mine = target.get("account_hash") == account_hash
                if is_admin or target_mine:
                    ok = posts.delete_reply(post["id"], target.get("id"), account_hash)
                    if ok:
                        ui.status("Reply deleted.", "ok")
                    else:
                        ui.status("Could not delete reply.", "err")
                else:
                    ui.status("You can only delete your own replies.", "err")
                import time; time.sleep(0.7)
            except Exception:
                ui.status("Invalid number", "err")
                import time; time.sleep(0.7)


def screen_my_posts(session):
    account_hash = session.get("account_hash")
    if not account_hash:
        ui.status("You must be logged in to view your posts.", "warn")
        input("  Press Enter...")
        return "menu"

    while True:
        ui.clear()
        ui.header("My Posts")
        try:
            my_posts = posts.get_my_posts(account_hash, 50)
        except Exception as e:
            ui.status(f"Error: {e}", "err")
            input("  Press Enter...")
            return "menu"

        if not my_posts:
            print(ui.MUTED + "  You haven't posted anything yet." + ui.term.normal)
            print()
            input("  Press Enter to go back...")
            return "menu"

        session_likes = session.setdefault("liked_posts", set())
        for i, post in enumerate(my_posts, 1):
            liked = post.get("id") in session_likes
            print(ui.render_post(post, i, mine=True, liked=liked))

        ui.footer([("d", "delete"), ("b", "back")])
        
        choice = ui.wait_for_input()
        if choice == "resize":
            continue
        elif choice == "b":
            return "menu"
        elif choice == "d":
            idx = ui.prompt("Post number to delete").strip()
            try:
                target = my_posts[int(idx) - 1]
                ok = posts.delete_post(target["id"], account_hash)
                if ok:
                    ui.status("Deleted.", "ok")
                else:
                    ui.status("Could not delete.", "err")
                import time; time.sleep(0.7)
            except Exception:
                ui.status("Invalid number", "err")
                import time; time.sleep(0.7)


def screen_menu(session):
    account_hash = session.get("account_hash")
    logged_in = account_hash is not None
    while True:
        ui.clear()
        ui.header("Menu", "logged in" if logged_in else "anonymous")
        print()
        opts = [("1", "Browse feed"), ("2", "New post")]
        if logged_in:
            opts.append(("3", "My posts"))
            opts.append(("4", "Logout"))
        else:
            opts.append(("3", "Login / Create account"))
        opts.append(("q", "Quit"))
        ui.footer(opts)

        choice = ui.wait_for_input()
        if choice == "resize":
            continue
        if choice == "1":
            return "feed"
        elif choice == "2":
            return "new_post"
        elif choice == "3" and logged_in:
            return "my_posts"
        elif choice == "4" and logged_in:
            session["account_hash"] = None
            session["liked_posts"] = set()
            logged_in = False
            ui.status("Logged out.", "ok")
            import time; time.sleep(0.7)
            return "welcome"
        elif choice == "3" and not logged_in:
            return "welcome"
        elif choice == "q":
            return "quit"


def run():
    session = {"account_hash": None, "liked_posts": set()}
    state = "welcome"
    extra = None

    while True:
        if state == "welcome":
            state = screen_welcome(session)
        elif state == "create_account":
            state = screen_create_account(session)
        elif state == "login":
            state = screen_login(session)
        elif state == "feed":
            result = screen_feed(session)
            if isinstance(result, tuple):
                state, extra = result
            else:
                state = result
        elif state == "new_post":
            state = screen_new_post(session)
        elif state == "reply":
            state = screen_reply(session, extra)
        elif state == "my_posts":
            state = screen_my_posts(session)
        elif state == "menu":
            state = screen_menu(session)
        elif state == "quit":
            ui.clear()
            print(ui.BLUE + ui.BOLD + "  Goodbye." + ui.term.normal)
            print()
            sys.exit(0)
        else:
            state = "welcome"


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        ui.clear()
        print(ui.BLUE + ui.BOLD + "  Goodbye." + ui.term.normal)
        print()
        sys.exit(0)
