import datetime
import firebase_client as db
import auth

LOCAL_POSTS = []
LOCAL_REPLIES = {}


def _now():
    return datetime.datetime.now(tz=datetime.timezone.utc)


def create_post(content: str, account_hash: str = None) -> str:
    local_id = f"local-{len(LOCAL_POSTS) + 1}"
    post_data = {
        "content": content,
        "created_at": _now(),
        "likes": 0,
        "account_hash": account_hash,
        "id": local_id,
    }
    LOCAL_POSTS.insert(0, post_data)
    try:
        doc_id = db.create_document("posts", {
            "content": content,
            "created_at": _now(),
            "likes": 0,
            "account_hash": account_hash,
        })
        post_data["id"] = doc_id
    except Exception:
        pass
    return post_data["id"]


def get_posts(limit: int = 50) -> list[dict]:
    try:
        results = db.query_collection("posts", order_by="created_at",
                                      direction="DESCENDING", limit=limit)
        if results:
            return results
    except Exception:
        pass
    return LOCAL_POSTS[:limit]


def get_my_posts(account_hash: str, limit: int = 50) -> list[dict]:
    try:
        results = db.query_collection(
            "posts",
            where_field="account_hash",
            where_value=account_hash,
            limit=limit,
        )
        results.sort(key=lambda p: p.get("created_at") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
        if results:
            return results
    except Exception:
        pass
    return [p for p in LOCAL_POSTS if p.get("account_hash") == account_hash][:limit]


def toggle_like(post_id: str, session_likes: set) -> bool:
    already_liked = post_id in session_likes
    delta = -1 if already_liked else 1

    for post in LOCAL_POSTS:
        if post.get("id") == post_id:
            post["likes"] = max(0, post.get("likes", 0) + delta)
            break

    try:
        db.increment_field("posts", post_id, "likes", delta)
    except Exception:
        pass

    if already_liked:
        session_likes.discard(post_id)
        return False
    else:
        session_likes.add(post_id)
        return True


def delete_post(post_id: str, account_hash: str) -> bool:
    is_admin = auth.is_admin(account_hash)
    for i, post in enumerate(list(LOCAL_POSTS)):
        if post.get("id") == post_id:
            if is_admin or post.get("account_hash") == account_hash:
                del LOCAL_POSTS[i]
                break
    try:
        doc = db.get_document("posts", post_id)
        if doc and (is_admin or doc.get("account_hash") == account_hash):
            db.delete_document("posts", post_id)
            return True
    except Exception:
        pass
    return False


def add_reply(post_id: str, content: str, account_hash: str = None):
    entry = {"content": content, "created_at": _now(), "account_hash": account_hash}
    LOCAL_REPLIES.setdefault(post_id, []).append(entry)
    try:
        db.add_to_subcollection("posts", post_id, "replies", {
            "content": content,
            "created_at": _now(),
            "account_hash": account_hash,
        })
    except Exception:
        pass


def get_replies(post_id: str) -> list[dict]:
    try:
        results = db.query_subcollection("posts", post_id, "replies", order_by="created_at")
        if results:
            return results
    except Exception:
        pass
    return LOCAL_REPLIES.get(post_id, [])


def delete_reply(post_id: str, reply_id: str, account_hash: str) -> bool:
    is_admin = auth.is_admin(account_hash)
    
    # Handle local replies
    if post_id in LOCAL_REPLIES:
        for i, reply in enumerate(list(LOCAL_REPLIES[post_id])):
            if reply.get("id") == reply_id:
                 if is_admin or reply.get("account_hash") == account_hash:
                    del LOCAL_REPLIES[post_id][i]
                    break

    try:
        # We need to verify the reply exists and get its account_hash
        doc = db.get_document(f"posts/{post_id}/replies", reply_id)
        if doc and (is_admin or doc.get("account_hash") == account_hash):
            db.delete_document(f"posts/{post_id}/replies", reply_id)
            return True
    except Exception:
        pass
    return False
