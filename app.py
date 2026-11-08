"""IPL Auction Assistant (first version).

All numbers in the data folder are SAMPLE (invented) so the app can be shown working.
Replace the two files in the data folder with real data when it is ready.
"""

import re

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="IPL Auction Assistant", layout="wide")

ROLES = ["Batter", "Wicketkeeper", "All-rounder", "Fast bowler", "Spin bowler"]
ROLE_COLUMN = {
    "Batter": "have_batter",
    "Wicketkeeper": "have_wicketkeeper",
    "All-rounder": "have_allrounder",
    "Fast bowler": "have_fast_bowler",
    "Spin bowler": "have_spin_bowler",
}
# How many players of each role a balanced squad would like to have.
ROLE_TARGET = {"Batter": 6, "Wicketkeeper": 2, "All-rounder": 5, "Fast bowler": 6, "Spin bowler": 4}


@st.cache_data
def load_data():
    players = pd.read_csv("sample_players.csv")
    teams = pd.read_csv("sample_teams.csv")
    return players, teams


def add_scores(players: pd.DataFrame) -> pd.DataFrame:
    """Give every player a score from 0 to 100 using simple, explainable rules."""
    p = players.copy()

    def scale(series, low, high):
        return ((series - low) / (high - low)).clip(0, 1) * 100

    bat = 0.6 * scale(p["runs"], 150, 650) + 0.4 * scale(p["strike_rate"], 120, 170)
    bowl = 0.6 * scale(p["wickets"], 5, 25) + 0.4 * (100 - scale(p["economy"], 7.0, 9.8))
    score = np.where(
        p["role"].isin(["Batter", "Wicketkeeper"]),
        bat,
        np.where(p["role"] == "All-rounder", (bat + bowl) / 2, bowl),
    )
    p["score"] = np.round(score, 1)
    return p


def fit_price_line(p: pd.DataFrame):
    """Draw a straight line through score versus last year's price."""
    slope, intercept = np.polyfit(p["score"], p["last_year_price_cr"], 1)
    return slope, intercept


def team_state(teams: pd.DataFrame, sales: list, team: str) -> dict:
    row = teams[teams["team"] == team].iloc[0]
    state = {
        "purse": float(row["purse_left_cr"]),
        "slots": int(row["slots_left"]),
        "overseas_slots": int(row["overseas_slots_left"]),
        "have": {r: int(row[ROLE_COLUMN[r]]) for r in ROLES},
    }
    for s in sales:
        if s["team"] == team:
            state["purse"] -= s["price"]
            state["slots"] -= 1
            state["have"][s["role"]] += 1
            if s["nationality"] == "Overseas":
                state["overseas_slots"] -= 1
    state["purse"] = round(state["purse"], 2)
    return state


def safe_max_bid(state: dict, min_base: float) -> float:
    """Most a team can pay for one player and still afford the rest of the squad at the lowest price."""
    if state["slots"] <= 0:
        return 0.0
    keep_aside = (state["slots"] - 1) * min_base
    return round(max(state["purse"] - keep_aside, 0.0), 2)


def recommend(available, state, slope, intercept, min_base):
    safe = safe_max_bid(state, min_base)
    rows = []
    for _, r in available.iterrows():
        if r["nationality"] == "Overseas" and state["overseas_slots"] <= 0:
            continue
        gap = ROLE_TARGET[r["role"]] - state["have"][r["role"]]
        need_weight = 1.3 if gap > 0 else 0.8
        fair = max(float(r["base_price_cr"]), slope * r["score"] + intercept)
        max_bid = min(safe, fair * 1.15)
        if max_bid < r["base_price_cr"]:
            continue  # the team cannot afford even the starting price safely
        rows.append(
            {
                "player": r["player"],
                "role": r["role"],
                "nationality": r["nationality"],
                "score": r["score"],
                "need": "Yes" if gap > 0 else "No",
                "starting_price_cr": r["base_price_cr"],
                "estimated_fair_price_cr": round(fair, 2),
                "do_not_bid_above_cr": round(max_bid, 2),
                "priority": round(r["score"] * need_weight, 1),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("priority", ascending=False).reset_index(drop=True)


def answer_question(question: str, available: pd.DataFrame) -> str:
    """A simple question answerer that only reads the table. No guessing."""
    q = question.lower()
    df = available.copy()
    filters = []

    if "indian" in q:
        df = df[df["nationality"] == "Indian"]; filters.append("Indian")
    elif "overseas" in q or "foreign" in q:
        df = df[df["nationality"] == "Overseas"]; filters.append("overseas")

    role_words = {
        "wicketkeeper": "Wicketkeeper", "keeper": "Wicketkeeper",
        "all-rounder": "All-rounder", "allrounder": "All-rounder", "all rounder": "All-rounder",
        "fast": "Fast bowler", "pace": "Fast bowler",
        "spin": "Spin bowler", "batter": "Batter", "batsman": "Batter",
    }
    for word, role in role_words.items():
        if word in q:
            df = df[df["role"] == role]; filters.append(role.lower()); break
    else:
        if "bowler" in q:
            df = df[df["role"].isin(["Fast bowler", "Spin bowler"])]; filters.append("bowler")

    m = re.search(r"(?:under|below|less than|within)\s*(\d+(?:\.\d+)?)", q)
    if m:
        limit = float(m.group(1))
        df = df[df["base_price_cr"] <= limit]; filters.append(f"starting price up to {limit} crore")

    if not filters:
        return ("I can answer questions like: 'best Indian fast bowlers under 2 crore' or "
                "'top overseas batters'. Please include a role, Indian or overseas, or a price limit.")
    if df.empty:
        return "No unsold player in my data matches that."
    top = df.sort_values("score", ascending=False).head(5)
    lines = [f"Top matches ({', '.join(filters)}), from my table only:"]
    for _, r in top.iterrows():
        lines.append(f"- {r['player']}: {r['role']}, {r['nationality']}, score {r['score']}, starts at {r['base_price_cr']} crore")
    return "\n".join(lines)


# ---------------------------------------------------------------- app
players_raw, teams = load_data()
players = add_scores(players_raw)
slope, intercept = fit_price_line(players)

if "sales" not in st.session_state:
    st.session_state.sales = []

sold_names = [s["player"] for s in st.session_state.sales]
available = players[~players["player"].isin(sold_names)]

st.title("IPL Auction Assistant")
st.warning("This first version uses SAMPLE data that is invented. It shows how the app works. Real data comes next.")

with st.sidebar:
    st.header("Settings")
    my_team = st.selectbox("Your team", teams["team"].tolist())
    min_base = st.number_input("Lowest starting price in the auction (crore)", 0.1, 2.0, 0.3, 0.05,
                               help="Used to keep money aside for the players you still need. Please confirm this number for your auction.")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Recommendations", "Record a sale", "Ask the chatbot"])

with tab1:
    st.subheader("All teams right now")
    rows = []
    for t in teams["team"]:
        s = team_state(teams, st.session_state.sales, t)
        rows.append({"team": t, "money_left_cr": s["purse"], "spots_left": s["slots"],
                     "overseas_spots_left": s["overseas_slots"]})
    board = pd.DataFrame(rows)
    st.dataframe(board, width="stretch", hide_index=True)
    st.bar_chart(board.set_index("team")["money_left_cr"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Players sold so far", len(st.session_state.sales))
    c2.metric("Players still unsold", len(available))
    spent = sum(s["price"] for s in st.session_state.sales)
    c3.metric("Total money spent (crore)", round(spent, 2))
    st.caption(f"Price estimate line: price = {slope:.3f} x score + {intercept:.2f} (made from the sample 'last year price' column).")

with tab2:
    state = team_state(teams, st.session_state.sales, my_team)
    st.subheader(f"Advice for {my_team}")
    a, b, c = st.columns(3)
    a.metric("Money left (crore)", state["purse"])
    b.metric("Spots left", state["slots"])
    c.metric("Overseas spots left", state["overseas_slots"])
    st.info(f"Safe limit for one player: {safe_max_bid(state, min_base)} crore. "
            f"This keeps enough money to fill the other {max(state['slots'] - 1, 0)} spots at the lowest price.")
    missing = [f"{r} (have {state['have'][r]}, want {ROLE_TARGET[r]})" for r in ROLES if state["have"][r] < ROLE_TARGET[r]]
    st.write("Roles still needed: " + (", ".join(missing) if missing else "none"))
    recs = recommend(available, state, slope, intercept, min_base)
    if recs.empty:
        st.write("No player fits right now.")
    else:
        st.dataframe(recs.head(10), width="stretch", hide_index=True)
        st.caption("Priority = player score, raised if your team needs that role. 'Do not bid above' is the lower of your safe limit and about 15 percent over the estimated fair price.")

with tab3:
    st.subheader("Record a sale as it happens")
    if len(available) == 0:
        st.write("All players are sold.")
    else:
        who = st.selectbox("Player sold", available["player"].tolist())
        buyer = st.selectbox("Bought by", teams["team"].tolist())
        price = st.number_input("Final price (crore)", 0.1, 50.0, 1.0, 0.05)
        if st.button("Save sale"):
            r = players[players["player"] == who].iloc[0]
            st.session_state.sales.append({"player": who, "team": buyer, "price": price,
                                           "role": r["role"], "nationality": r["nationality"]})
            st.rerun()
    if st.session_state.sales:
        st.write("Sales so far")
        st.dataframe(pd.DataFrame(st.session_state.sales), width="stretch", hide_index=True)
        if st.button("Undo last sale"):
            st.session_state.sales.pop()
            st.rerun()
    st.caption("In this version sales are kept only while the page stays open. The database step will save them permanently.")

with tab4:
    st.subheader("Ask about unsold players")
    st.caption("Example: best Indian fast bowlers under 2 crore")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for who, text in st.session_state.chat:
        st.chat_message(who).write(text)
    q = st.chat_input("Type your question")
    if q:
        st.session_state.chat.append(("user", q))
        st.session_state.chat.append(("assistant", answer_question(q, available)))
        st.rerun()
