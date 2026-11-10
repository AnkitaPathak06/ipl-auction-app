"""Login and saving. Uses Supabase when keys are set. Otherwise runs in demo mode (nothing is saved)."""

import streamlit as st


def has_supabase() -> bool:
    try:
        return bool(st.secrets["SUPABASE_URL"]) and bool(st.secrets["SUPABASE_KEY"])
    except Exception:
        return False


def _client():
    if "sb" not in st.session_state:
        from supabase import create_client

        st.session_state.sb = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.sb


# ---------- login ----------
def sign_up(email: str, password: str):
    """Returns (ok, message)."""
    try:
        res = _client().auth.sign_up({"email": email, "password": password})
        if res.session is None:
            return False, "Account created. Check your email to confirm, then log in."
        st.session_state.user_id = res.user.id
        st.session_state.email = email
        return True, ""
    except Exception as e:
        return False, f"Could not create account: {e}"


def sign_in(email: str, password: str):
    try:
        res = _client().auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user_id = res.user.id
        st.session_state.email = email
        return True, ""
    except Exception as e:
        return False, f"Login failed: {e}"


def sign_out():
    try:
        if has_supabase() and "sb" in st.session_state:
            st.session_state.sb.auth.sign_out()
    except Exception:
        pass
    for k in ["sb", "user_id", "email", "setup", "sales", "demo", "chat"]:
        st.session_state.pop(k, None)


def start_demo():
    st.session_state.user_id = "demo"
    st.session_state.email = "Demo mode (not saved)"
    st.session_state.demo = True


# ---------- setup ----------
def load_all():
    """Load my setup and sales once after login."""
    if st.session_state.get("demo"):
        st.session_state.setdefault("setup", None)
        st.session_state.setdefault("sales", [])
        return
    c = _client()
    r = c.table("setups").select("data").eq("user_id", st.session_state.user_id).execute()
    st.session_state.setup = r.data[0]["data"] if r.data else None
    s = c.table("sales").select("*").eq("user_id", st.session_state.user_id).order("id").execute()
    st.session_state.sales = [
        {"id": x["id"], "player": x["player"], "buyer": x["buyer"], "price": float(x["price"])} for x in s.data
    ]


def save_setup(data: dict):
    st.session_state.setup = data
    if st.session_state.get("demo"):
        return
    _client().table("setups").upsert({"user_id": st.session_state.user_id, "data": data}).execute()


# ---------- sales ----------
def add_sale(player: str, buyer: str, price: float):
    sale = {"player": player, "buyer": buyer, "price": float(price)}
    if not st.session_state.get("demo"):
        r = _client().table("sales").insert(sale).execute()
        sale["id"] = r.data[0]["id"]
    st.session_state.sales.append(sale)


def undo_sale():
    if not st.session_state.sales:
        return
    last = st.session_state.sales[-1]
    if not st.session_state.get("demo"):
        _client().table("sales").delete().eq("id", last["id"]).execute()
    st.session_state.sales.pop()


def clear_sales():
    if not st.session_state.get("demo"):
        _client().table("sales").delete().eq("user_id", st.session_state.user_id).execute()
    st.session_state.sales = []
