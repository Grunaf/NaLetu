import json
import os

USER_SESSIONS_FILE = "planner/user_sessions.json"
user_sessions = {}

# === Загрузка при старте ===
def load_user_sessions():
    global user_sessions
    if os.path.exists(USER_SESSIONS_FILE):
        try:
            with open(USER_SESSIONS_FILE, "r", encoding="utf-8") as f:
                user_sessions = json.load(f)
                print("✅ Пользовательские сессии загружены.")
        except Exception as e:
            print(f"⚠️ Ошибка при загрузке user_sessions: {e}")

def update_session(user_id, key, value):
    session = user_sessions.setdefault(str(user_id), {})
    session[key] = value
    user_sessions[str(user_id)] = session
    save_user_sessions()

def mark_used_clusters(user_id, cluster_ids: list[int]):
    sess = user_sessions.setdefault(str(user_id), {})
    # Старый список (или пустой)
    prev = sess.get("used_clusters", [])
    # Новые кластеры, приведенные к int
    new_ids = [int(cid) for cid in cluster_ids]

    # Объединяем и сразу удаляем дубли, сохраняя порядок:
    combined = list(dict.fromkeys(prev + new_ids))

    sess["used_clusters"] = combined
    user_sessions[str(user_id)] = sess
    save_user_sessions()

def update_filters(user_id, exclude_names=None, exclude_categories=None, exclude_tags=None):
    sess = user_sessions.setdefault(str(user_id), {})
    filters = sess.setdefault("filters", {})
    if exclude_names   is not None: filters["exclude_names"]      = exclude_names
    if exclude_categories is not None: filters["exclude_categories"] = exclude_categories
    if exclude_tags    is not None: filters["exclude_tags"]       = exclude_tags
    user_sessions[str(user_id)] = sess
    save_user_sessions()

def save_user_sessions():
    try:
        with open(USER_SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                user_sessions,
                f,
                indent=2,
                ensure_ascii=False,
                default=int        # <- вот эта строчка!
            )
            print("💾 Сессии сохранены.")
    except Exception as e:
        print(f"❌ Ошибка при сохранении user_sessions: {e}")

