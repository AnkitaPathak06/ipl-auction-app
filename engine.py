"""All the maths and rules. No screens here.

Data files are SAMPLE (invented). Replace them with real data later.
"""

import re

import numpy as np
import pandas as pd

ROLES = ["Batter", "Wicketkeeper", "All-rounder", "Fast bowler", "Spin bowler"]
ROLE_COLUMN = {
    "Batter": "have_batter",
    "Wicketkeeper": "have_wicketkeeper",
    "All-rounder": "have_allrounder",
    "Fast bowler": "have_fast_bowler",
    "Spin bowler": "have_spin_bowler",
}
DEFAULT_TARGET = {"Batter": 6, "Wicketkeeper": 2, "All-rounder": 5, "Fast bowler": 6, "Spin bowler": 4}
DEFAULT_SPLIT = {"Batter": 25, "Wicketkeeper": 10, "All-rounder": 25, "Fast bowler": 25, "Spin bowler": 15}


def fmt(x) -> str:
    """Money in crore: 4.5 -> '4.5', 4.0 -> '4'."""
    s = f"{float(x):.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


# ---------- data ----------
def add_scores(players: pd.DataFrame) -> pd.DataFrame:
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
    slope, intercept = np.polyfit(p["score"], p["last_year_price_cr"], 1)
    return float(slope), float(intercept)


# ---------- team states ----------
def _blank_have():
    return {r: 0 for r in ROLES}


def my_state(setup: dict, players: pd.DataFrame, sales: list) -> dict:
    """My team: starts from the plan (budget and retained players), then applies my purchases."""
    have = _blank_have()
    overseas = 0
    squad = []
    for r in setup.get("retained", []):
        have[r["role"]] += 1
        overseas += 1 if r["nationality"] == "Overseas" else 0
        squad.append({"player": r["name"], "role": r["role"], "nationality": r["nationality"],
                      "price": float(r["price"]), "how": "Retained"})
    purse = float(setup["budget"])
    lookup = players.set_index("player")
    for s in sales:
        if s["buyer"] != setup["team"]:
            continue
        row = lookup.loc[s["player"]]
        have[row["role"]] += 1
        overseas += 1 if row["nationality"] == "Overseas" else 0
        purse -= float(s["price"])
        squad.append({"player": s["player"], "role": row["role"], "nationality": row["nationality"],
                      "price": float(s["price"]), "how": "Bought"})
    count = len(squad)
    return {
        "purse": round(purse, 2),
        "count": count,
        "slots": setup["squad_max"] - count,
        "must_fill": max(setup["squad_min"] - count, 0),
        "overseas_slots": setup["overseas_max"] - overseas,
        "have": have,
        "squad": squad,
    }


def rival_state(teams: pd.DataFrame, players: pd.DataFrame, sales: list, team: str) -> dict:
    row = teams[teams["team"] == team].iloc[0]
    st_ = {
        "purse": float(row["purse_left_cr"]),
        "slots": int(row["slots_left"]),
        "must_fill": int(row["slots_left"]),
        "overseas_slots": int(row["overseas_slots_left"]),
        "have": {r: int(row[ROLE_COLUMN[r]]) for r in ROLES},
    }
    lookup = players.set_index("player")
    for s in sales:
        if s["buyer"] == team:
            r = lookup.loc[s["player"]]
            st_["purse"] -= float(s["price"])
            st_["slots"] -= 1
            st_["must_fill"] = max(st_["must_fill"] - 1, 0)
            st_["have"][r["role"]] += 1
            if r["nationality"] == "Overseas":
                st_["overseas_slots"] -= 1
    st_["purse"] = round(st_["purse"], 2)
    return st_


def safe_max_bid(state: dict, min_base: float) -> float:
    """Most a team can pay for one player and still fill the rest of the squad at the lowest price."""
    if state["slots"] <= 0:
        return 0.0
    keep_aside = max(state["must_fill"] - 1, 0) * min_base
    return round(max(state["purse"] - keep_aside, 0.0), 2)


def team_weights(position: int):
    """Last season's table position changes how much a needed role is pushed.
    Weak team: push weak areas hard. Strong team: keep the winning mix."""
    if position >= 7:
        return 1.5, 0.7
    if position <= 4:
        return 1.2, 1.0
    return 1.3, 0.8


def role_plan(setup: dict, players: pd.DataFrame, sales: list) -> dict:
    lookup = players.set_index("player")
    out = {}
    for r in ROLES:
        planned = setup["budget"] * setup["split"][r] / 100.0
        spent = sum(float(s["price"]) for s in sales
                    if s["buyer"] == setup["team"] and lookup.loc[s["player"]]["role"] == r)
        out[r] = {"planned": round(planned, 2), "spent": round(spent, 2), "left": round(planned - spent, 2)}
    return out


# ---------- advice ----------
def make_context(setup, players, teams, sales):
    sold_names = {s["player"] for s in sales}
    retained_names = {r["name"] for r in setup.get("retained", [])}
    pool = players[~players["player"].isin(sold_names | retained_names)].copy()
    slope, intercept = fit_price_line(players)
    mine = my_state(setup, players, sales)
    rivals = {t: rival_state(teams, players, sales, t) for t in teams["team"] if t != setup["team"]}
    my_row = teams[teams["team"] == setup["team"]].iloc[0]
    return {
        "setup": setup, "players": players, "teams": teams, "sales": sales, "pool": pool,
        "slope": slope, "intercept": intercept, "mine": mine, "rivals": rivals,
        "plan": role_plan(setup, players, sales),
        "position": int(my_row["last_position"]),
        "wins": int(my_row["last_wins"]), "losses": int(my_row["last_losses"]),
    }


def rival_demand(p, ctx):
    min_base = ctx["setup"]["min_base"]
    target = ctx["setup"]["target"]
    rows = []
    for t, rs in ctx["rivals"].items():
        cap = safe_max_bid(rs, min_base)
        can = cap >= p["base_price_cr"] and not (p["nationality"] == "Overseas" and rs["overseas_slots"] <= 0)
        needs = target[p["role"]] - rs["have"][p["role"]] > 0
        rows.append({"team": t, "can_afford": can, "needs_role": needs,
                     "likely": can and needs, "can_pay": cap})
    return rows


def advise(p, ctx) -> dict:
    s = ctx["setup"]
    st_ = ctx["mine"]
    role = p["role"]
    gap = s["target"][role] - st_["have"][role]
    need_w, fill_w = team_weights(ctx["position"])
    fair = max(float(p["base_price_cr"]), ctx["slope"] * float(p["score"]) + ctx["intercept"])
    safe = safe_max_bid(st_, s["min_base"])
    max_bid = round(min(safe, fair * 1.15), 2)
    plan_left = ctx["plan"][role]["left"]
    pos = ctx["position"]

    skip_reason = None
    if st_["slots"] <= 0:
        skip_reason = f"Your squad is full ({s['squad_max']} players)."
    elif p["nationality"] == "Overseas" and st_["overseas_slots"] <= 0:
        skip_reason = f"You have no overseas spot left (max {s['overseas_max']})."
    elif safe < p["base_price_cr"]:
        skip_reason = (f"You cannot afford the starting price of {fmt(p['base_price_cr'])} cr "
                       f"and still fill your squad.")
    elif max_bid < p["base_price_cr"]:
        skip_reason = "Fair value is below the starting price. Not worth it."
    elif plan_left < p["base_price_cr"]:
        skip_reason = f"Your {role.lower()} budget in the plan is used up."
    elif gap <= 0 and float(p["score"]) < 70:
        skip_reason = f"You already have enough {role.lower()}s and his score ({p['score']}) is not top class."
    signal = "skip" if skip_reason else "bid"

    # fit text
    if gap > 0:
        fit = f"You need {gap} more {role.lower()}{'s' if gap > 1 else ''}. "
        fit += f"Plan budget left for this role: {fmt(max(plan_left, 0))} cr."
    else:
        fit = f"Role already full ({st_['have'][role]} of {s['target'][role]}). He would be an extra."
    if pos >= 7:
        fit += f" Your team finished {pos}th last season, so weak areas get extra push."
    elif pos <= 4:
        fit += f" Your team finished {pos}th last season, so keep the winning mix."

    # risk
    risks = []
    age = int(p["age"])
    if age >= 34:
        risks.append(f"Age {age}: form may drop")
    elif age <= 21:
        risks.append(f"Age {age}: less proven")
    if float(p["score"]) < 50:
        risks.append(f"Low score ({p['score']})")
    if safe < fair:
        risks.append("Safe limit is below fair price")
    if fair > float(p["last_year_price_cr"]) * 1.3:
        risks.append("Fair price is well above last year's price")
    risk_level = "High" if len(risks) >= 2 else ("Medium" if len(risks) == 1 else "Low")

    # rivals
    riv = rival_demand(p, ctx)
    likely = sorted([r for r in riv if r["likely"]], key=lambda r: -r["can_pay"])
    can_n = sum(1 for r in riv if r["can_afford"])

    # alternatives: same role, cheaper fair price, good score
    pool = ctx["pool"]
    alts = pool[(pool["role"] == role) & (pool["player"] != p["player"])].copy()
    alts["fair"] = np.maximum(alts["base_price_cr"], ctx["slope"] * alts["score"] + ctx["intercept"])
    alts = alts[alts["fair"] < fair].sort_values("score", ascending=False).head(3)
    alternatives = [{"player": r["player"], "score": r["score"], "fair": round(float(r["fair"]), 2)}
                    for _, r in alts.iterrows()]

    # one line reason
    if signal == "skip":
        reason = skip_reason
    else:
        reason = (f"{'Good fit' if gap > 0 else 'Extra pick'}: score {p['score']}, fair price {fmt(fair)} cr. "
                  f"{len(likely)} rival{'s' if len(likely) != 1 else ''} likely to bid. Stop at {fmt(max_bid)} cr.")
        if gap > 0:
            reason = f"Needed {role.lower()}. " + reason

    priority = float(p["score"]) * (need_w if gap > 0 else fill_w)
    if plan_left < p["base_price_cr"]:
        priority *= 0.5
    if signal == "skip":
        priority *= 0.2

    return {
        "signal": signal, "max_bid": max_bid if signal == "bid" else 0.0, "fair": round(fair, 2),
        "reason": reason, "fit": fit, "gap": gap, "risks": risks, "risk_level": risk_level,
        "rivals": riv, "likely": likely, "can_n": can_n, "alternatives": alternatives,
        "priority": round(priority, 1), "safe": safe,
    }


def recommendations(ctx) -> pd.DataFrame:
    rows = []
    for _, p in ctx["pool"].iterrows():
        a = advise(p, ctx)
        rows.append({
            "Player": p["player"], "Role": p["role"], "Nationality": p["nationality"], "Score": p["score"],
            "Needed": "Yes" if a["gap"] > 0 else "No", "Starting price (cr)": p["base_price_cr"],
            "Fair price (cr)": a["fair"], "Do not bid above (cr)": a["max_bid"],
            "Advice": "Bid" if a["signal"] == "bid" else "Skip", "Why": a["reason"], "_prio": a["priority"],
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("_prio", ascending=False).drop(columns="_prio").reset_index(drop=True)


# ---------- checks when recording a sale ----------
def check_sale(player, buyer, price, ctx):
    """Returns (errors, warnings). Errors block the save."""
    errors, warnings = [], []
    players, s = ctx["players"], ctx["setup"]
    p = players[players["player"] == player].iloc[0]
    if price < p["base_price_cr"]:
        errors.append(f"Price is below the starting price ({fmt(p['base_price_cr'])} cr).")
    state = ctx["mine"] if buyer == s["team"] else ctx["rivals"][buyer]
    if state["slots"] <= 0:
        errors.append(f"{buyer} has no squad spot left.")
    if p["nationality"] == "Overseas" and state["overseas_slots"] <= 0:
        errors.append(f"{buyer} has no overseas spot left.")
    if price > state["purse"]:
        errors.append(f"{buyer} only has {fmt(state['purse'])} cr left.")
    elif price > safe_max_bid(state, s["min_base"]):
        warnings.append(f"This leaves {buyer} too little money to fill the squad at the lowest price.")
    if buyer == s["team"]:
        a = advise(p, ctx)
        if a["signal"] == "bid" and price > a["max_bid"]:
            warnings.append(f"This is above your do-not-bid-above number ({fmt(a['max_bid'])} cr).")
        if ctx["plan"][p["role"]]["left"] < price:
            warnings.append(f"This goes over your plan budget for {p['role'].lower()}s.")
    return errors, warnings


# ---------- chatbot ----------
def answer_question(question: str, pool: pd.DataFrame) -> str:
    q = question.lower()
    df = pool.copy()
    filters = []
    if "indian" in q:
        df = df[df["nationality"] == "Indian"]
        filters.append("Indian")
    elif "overseas" in q or "foreign" in q:
        df = df[df["nationality"] == "Overseas"]
        filters.append("overseas")
    role_words = {
        "wicketkeeper": "Wicketkeeper", "keeper": "Wicketkeeper",
        "all-rounder": "All-rounder", "allrounder": "All-rounder", "all rounder": "All-rounder",
        "fast": "Fast bowler", "pace": "Fast bowler",
        "spin": "Spin bowler", "batter": "Batter", "batsman": "Batter",
    }
    for word, role in role_words.items():
        if word in q:
            df = df[df["role"] == role]
            filters.append(role.lower())
            break
    else:
        if "bowler" in q:
            df = df[df["role"].isin(["Fast bowler", "Spin bowler"])]
            filters.append("bowler")
    m = re.search(r"(?:under|below|less than|within)\s*(\d+(?:\.\d+)?)", q)
    if m:
        limit = float(m.group(1))
        df = df[df["base_price_cr"] <= limit]
        filters.append(f"starting price up to {fmt(limit)} cr")
    if not filters:
        return ("I can answer questions like 'best Indian fast bowlers under 2 crore' or "
                "'top overseas batters'. Please include a role, Indian or overseas, or a price limit.")
    if df.empty:
        return "No unsold player in my data matches that."
    top = df.sort_values("score", ascending=False).head(5)
    lines = [f"Top unsold players for: {', '.join(filters)}"]
    for i, (_, r) in enumerate(top.iterrows(), 1):
        lines.append(f"{i}. {r['player']} ({r['role']}, {r['nationality']}) score {r['score']}, "
                     f"starting price {fmt(r['base_price_cr'])} cr")
    return "\n".join(lines)
