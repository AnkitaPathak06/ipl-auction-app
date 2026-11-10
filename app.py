"""IPL Auction Assistant. All data files are SAMPLE (invented) until real data is added."""

import html

import pandas as pd
import streamlit as st

import db
import engine as E
from engine import ROLES, fmt

st.set_page_config(page_title="IPL Auction Assistant", page_icon="🏏", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
:root{--ink:#15122E;--mu:#5E5A7A;--ac:#4F2FE0;--acs:#ECE8FF;--gr:#0F8A43;--grs:#E1F5E8;--rd:#C8202A;
--rds:#FDE8E9;--am:#FFD23F;--ams:#FFF3C4;--bg:#F3F2FA;--bd:#E3E0F3}
html,body,[class*="css"],.stApp{font-family:'Plus Jakarta Sans',system-ui,sans-serif !important}
.stApp{background:var(--bg);color:var(--ink)}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1rem;max-width:1400px}
.stButton>button,.stFormSubmitButton>button{border-radius:14px;font-weight:800;min-height:46px;border:2px solid #C9C4E8}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:var(--ac);border-color:var(--ac);color:#fff}
.banner{background:var(--am);text-align:center;padding:5px 10px;font-size:12px;font-weight:800;border-radius:10px;margin-bottom:8px}
.top{background:var(--ink);color:#fff;border-radius:16px;padding:10px 14px;margin-bottom:12px}
.top .nm{font-weight:800;margin-bottom:8px}.top .nm i{font-style:normal;color:var(--am)}
.pills{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:8px}
.pill{background:#2A2458;border-radius:12px;padding:6px 12px}
.pill small{display:block;font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#C9C3F0}
.pill b{font-size:24px;line-height:1.1;font-weight:800}.pill.m b{color:var(--am)}
.card{background:#fff;border:1px solid var(--bd);border-radius:18px;padding:14px;margin-bottom:12px}
.card h4{margin:0 0 8px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.07em;color:var(--mu)}
.hero{border-radius:22px;padding:16px 18px 20px;color:#fff;margin-bottom:12px}
.hero.bid{background:var(--gr)}.hero.skip{background:var(--rd)}
.hero .hr{display:flex;justify-content:space-between;align-items:center;gap:8px}
.hero .on{font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;opacity:.95}
.hero .badge{background:#fff;border-radius:999px;padding:3px 16px;font-weight:800;letter-spacing:.08em}
.hero.bid .badge{color:var(--gr)}.hero.skip .badge{color:var(--rd)}
.hero .lab{margin-top:10px;font-size:13px;font-weight:700;opacity:.95}
.hero .big{font-size:68px;font-weight:800;line-height:1;letter-spacing:-.03em}
.hero .big small{font-size:28px;font-weight:700;margin-left:6px}
.hero .why{margin-top:10px;font-size:16px;font-weight:600;line-height:1.35}
.chip{display:inline-block;border-radius:999px;padding:3px 10px;font-weight:700;font-size:12px;margin:2px 4px 2px 0}
.chip.in{background:var(--acs);color:var(--ac)}.chip.ov{background:var(--ams);color:#7A5200}
.chip.ok{background:var(--grs);color:var(--gr)}.chip.no{background:#EEEDF5;color:#8D89A8;text-decoration:line-through}
.chip.hot{background:var(--rds);color:var(--rd)}.chip.mid{background:var(--ams);color:#7A5200}
.kv{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #EFEDF8;font-size:14px}
.kv:last-child{border-bottom:0}.kv span{color:var(--mu)}.kv b{font-weight:800}
.bar{height:8px;background:#E7E3F7;border-radius:4px;overflow:hidden;margin:4px 0 10px}
.bar>div{height:100%;background:var(--ac);border-radius:4px}.bar.over>div{background:var(--rd)}
.al{border-radius:10px;padding:8px 12px;font-weight:600;font-size:14px;margin-bottom:6px}
.al.ok{background:var(--grs)}.al.warn{background:var(--ams);border:1px solid #D9A800}
.al.bad{background:var(--rds);border:1px solid var(--rd)}
.small{color:var(--mu);font-size:13px}
.login{max-width:440px;margin:30px auto 0}
.logo{font-size:30px;font-weight:800;letter-spacing:-.02em}.logo i{font-style:normal;color:var(--ac)}
@media (max-width:700px){.hero .big{font-size:52px}.pill b{font-size:20px}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

esc = html.escape


@st.cache_data
def load_data():
    players = E.add_scores(pd.read_csv("sample_players.csv"))
    teams = pd.read_csv("sample_teams.csv")
    return players, teams


def banner():
    st.markdown('<div class="banner">SAMPLE DATA. NOT REAL IPL DATA.</div>', unsafe_allow_html=True)


def card(title, body_html):
    st.markdown(f'<div class="card"><h4>{esc(title)}</h4>{body_html}</div>', unsafe_allow_html=True)


def kv(rows):
    return "".join(f"<div class='kv'><span>{esc(str(k))}</span><b>{esc(str(v))}</b></div>" for k, v in rows)


def alert(kind, text):
    label = {"ok": "OK", "warn": "WATCH", "bad": "STOP"}[kind]
    st.markdown(f'<div class="al {kind}"><b>{label}</b> {esc(text)}</div>', unsafe_allow_html=True)


# =====================================================================
# LOGIN
# =====================================================================
def login_screen():
    banner()
    st.markdown('<div class="login"><div class="logo">IPL <i>Auction</i> Assistant</div>'
                '<p class="small">Know when to bid, and when to stop.</p></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if not db.has_supabase():
            st.info("Database not connected yet. You can try the app in demo mode (nothing is saved).")
            if st.button("Start demo mode", type="primary", width="stretch"):
                db.start_demo()
                st.rerun()
            return
        t1, t2 = st.tabs(["Log in", "Create account"])
        with t1:
            e = st.text_input("Email", key="li_e")
            p = st.text_input("Password", type="password", key="li_p")
            if st.button("Log in", type="primary", width="stretch", key="li_b"):
                ok, msg = db.sign_in(e.strip(), p)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
        with t2:
            e2 = st.text_input("Email", key="su_e")
            p2 = st.text_input("Password (6+ characters)", type="password", key="su_p")
            if st.button("Create account", type="primary", width="stretch", key="su_b"):
                ok, msg = db.sign_up(e2.strip(), p2)
                if ok:
                    st.rerun()
                else:
                    st.warning(msg)
        with st.expander("Just looking? Try demo mode"):
            if st.button("Start demo mode", width="stretch"):
                db.start_demo()
                st.rerun()


# =====================================================================
# SETUP
# =====================================================================
def setup_screen(players, teams, existing):
    st.markdown("### Set up your auction plan")
    st.caption("Do this once before bidding. You can edit it any time in the Plan tab.")
    ex = existing or {}
    team_list = list(teams["team"])

    c1, c2 = st.columns(2)
    team = c1.selectbox("Your team", team_list,
                        index=team_list.index(ex["team"]) if ex.get("team") in team_list else 0)
    kinds = ["Mega auction", "Mini auction"]
    atype = c2.radio("Auction type", kinds, horizontal=True,
                     index=kinds.index(ex["auction_type"]) if ex.get("auction_type") in kinds else 0)

    st.markdown("**Rules** (change them if the auction rules are different)")
    r1, r2, r3, r4, r5 = st.columns(5)
    default_purse = 120.0 if atype == "Mega auction" else 50.0
    purse = r1.number_input("Total purse (cr)", 1.0, 500.0, float(ex.get("purse", default_purse)), 0.5)
    squad_min = r2.number_input("Squad min", 1, 30, int(ex.get("squad_min", 18)))
    squad_max = r3.number_input("Squad max", 1, 30, int(ex.get("squad_max", 25)))
    overseas_max = r4.number_input("Overseas max", 0, 15, int(ex.get("overseas_max", 8)))
    min_base = r5.number_input("Lowest starting price (cr)", 0.05, 5.0, float(ex.get("min_base", 0.3)), 0.05)

    st.markdown("**Retained players** (add one row per player)")
    ret_df = pd.DataFrame(ex.get("retained", []) or [], columns=["name", "role", "nationality", "price"])
    if ret_df.empty:
        ret_df = pd.DataFrame({"name": pd.Series(dtype="str"), "role": pd.Series(dtype="str"),
                               "nationality": pd.Series(dtype="str"), "price": pd.Series(dtype="float")})
    edited = st.data_editor(
        ret_df, num_rows="dynamic", width="stretch", key="ret_editor",
        column_config={
            "name": st.column_config.TextColumn("Player name"),
            "role": st.column_config.SelectboxColumn("Role", options=ROLES),
            "nationality": st.column_config.SelectboxColumn("Nationality", options=["Indian", "Overseas"]),
            "price": st.column_config.NumberColumn("Price (cr)", min_value=0.0, step=0.25),
        },
    )
    clean = edited.dropna(subset=["name", "role", "nationality", "price"])
    clean = clean[clean["name"].astype(str).str.strip() != ""]
    retained = [{"name": str(r["name"]).strip(), "role": r["role"], "nationality": r["nationality"],
                 "price": float(r["price"])} for _, r in clean.iterrows()]
    retained_cost = sum(r["price"] for r in retained)
    budget = round(purse - retained_cost, 2)
    st.markdown(f"Retained: **{len(retained)}** players, **{fmt(retained_cost)} cr**. "
                f"Budget to spend: **{fmt(budget)} cr**.")

    st.markdown("**What players do you want?** Number of each role in the final squad.")
    tcols = st.columns(5)
    target = {}
    for i, r in enumerate(ROLES):
        target[r] = tcols[i].number_input(r, 0, 15, int(ex.get("target", E.DEFAULT_TARGET)[r]), key=f"t_{r}")

    st.markdown("**How should the budget be split?** Percent per role. Must add up to 100.")
    scols = st.columns(5)
    split = {}
    for i, r in enumerate(ROLES):
        split[r] = scols[i].number_input(f"{r} %", 0, 100, int(ex.get("split", E.DEFAULT_SPLIT)[r]), key=f"s_{r}")
    total = sum(split.values())
    if total != 100:
        st.warning(f"The split adds up to {total}. Make it 100.")

    row = teams[teams["team"] == team].iloc[0]
    st.caption(f"{team} last season: position {int(row['last_position'])}, "
               f"{int(row['last_wins'])} wins, {int(row['last_losses'])} losses (sample data).")

    problems = []
    if total != 100:
        problems.append("Split must be 100.")
    if squad_min > squad_max:
        problems.append("Squad min cannot be more than squad max.")
    if budget <= 0:
        problems.append("Retained players cost more than the purse.")
    if len(retained) > squad_max:
        problems.append("Too many retained players.")
    for p in problems:
        st.error(p)

    if st.button("Save plan and start", type="primary", disabled=bool(problems)):
        db.save_setup({
            "team": team, "auction_type": atype, "purse": float(purse), "budget": float(budget),
            "squad_min": int(squad_min), "squad_max": int(squad_max), "overseas_max": int(overseas_max),
            "min_base": float(min_base), "retained": retained, "target": target, "split": split,
        })
        st.rerun()


# =====================================================================
# SCREENS
# =====================================================================
def top_bar(ctx):
    s, m = ctx["setup"], ctx["mine"]
    st.markdown(
        f'<div class="top"><div class="nm">{esc(s["team"])} <i>· {esc(s["auction_type"])}</i></div>'
        f'<div class="pills">'
        f'<div class="pill m"><small>Money left</small><b>{fmt(m["purse"])} cr</b></div>'
        f'<div class="pill"><small>Spots left</small><b>{m["slots"]}</b></div>'
        f'<div class="pill"><small>Overseas left</small><b>{m["overseas_slots"]}</b></div></div></div>',
        unsafe_allow_html=True)


def tab_bid(ctx, recs):
    pool = ctx["pool"]
    if pool.empty:
        st.info("No players left.")
        return
    order = list(recs["Player"])
    info = pool.set_index("player")

    def label(n):
        r = info.loc[n]
        return f"{n}  ·  {r['role']}  ·  {r['nationality']}"

    name = st.selectbox("Player on the block", order, format_func=label, key="block")
    p = info.loc[name].copy()
    p["player"] = name
    a = E.advise(p, ctx)

    cls = "bid" if a["signal"] == "bid" else "skip"
    if a["signal"] == "bid":
        big = f'{fmt(a["max_bid"])}<small>cr</small>'
        lab = "Do not bid above"
    else:
        big = "Skip"
        lab = "Do not bid"
    st.markdown(
        f'<div class="hero {cls}"><div class="hr"><span class="on">On the block · {esc(name)}</span>'
        f'<span class="badge">{"BID" if a["signal"] == "bid" else "SKIP"}</span></div>'
        f'<div class="lab">{lab}</div><div class="big">{big}</div>'
        f'<div class="why">{esc(a["reason"])}</div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        nat_cls = "ov" if p["nationality"] == "Overseas" else "in"
        chips = (f'<span class="chip in">{esc(p["role"])}</span><span class="chip {nat_cls}">{esc(p["nationality"])}</span>'
                 f'<span class="chip in">Age {int(p["age"])}</span>')
        stats = [("Score (0 to 100)", p["score"]), ("Starting price", f'{fmt(p["base_price_cr"])} cr'),
                 ("Fair price", f'{fmt(a["fair"])} cr'), ("Last year price", f'{fmt(p["last_year_price_cr"])} cr')]
        if p["role"] in ("Batter", "Wicketkeeper", "All-rounder"):
            stats += [("Runs", int(p["runs"])), ("Strike rate", p["strike_rate"])]
        if p["role"] in ("Fast bowler", "Spin bowler", "All-rounder"):
            stats += [("Wickets", int(p["wickets"])), ("Economy", p["economy"])]
        card("Player", chips + kv(stats))
        card("Fit with your plan", f'<div style="font-size:14px">{esc(a["fit"])}</div>')
    with c2:
        chips = ""
        for r in a["rivals"]:
            if r["likely"]:
                cl = "hot"
            elif r["can_afford"]:
                cl = "ok"
            else:
                cl = "no"
            chips += f'<span class="chip {cl}">{esc(r["team"])}</span>'
        extra = ""
        if a["likely"]:
            extra = f'<div class="small">Richest likely rival can pay up to {fmt(a["likely"][0]["can_pay"])} cr.</div>'
        card("Rival watch",
             f'<div><b>{a["can_n"]} of {len(a["rivals"])}</b> rivals can afford him. '
             f'<b>{len(a["likely"])}</b> likely to bid.</div>{chips}'
             f'<div class="small">Red: can afford and needs this role. Green: can afford. Grey: cannot.</div>{extra}')
        rcls = {"High": "hot", "Medium": "mid", "Low": "ok"}[a["risk_level"]]
        risk_html = f'<span class="chip {rcls}">{a["risk_level"]} risk</span>'
        risk_html += "".join(f"<div class='kv'><span>{esc(x)}</span></div>" for x in a["risks"]) or \
            "<div class='small'>No red flags.</div>"
        card("Risk", risk_html)
        if a["alternatives"]:
            alt = "".join(kv([(x["player"], f'score {x["score"]} · fair {fmt(x["fair"])} cr')])
                          for x in a["alternatives"])
            card("Cheaper similar players", alt)
        else:
            card("Cheaper similar players", "<div class='small'>None found.</div>")


def tab_sale(ctx):
    s = ctx["setup"]
    pool = ctx["pool"]
    st.markdown("#### Record a sale")
    if pool.empty:
        st.info("No players left to sell.")
    else:
        c1, c2, c3 = st.columns([2, 1.2, 1])
        player = c1.selectbox("Player", list(pool["player"]), key="sale_player")
        teams_list = list(ctx["teams"]["team"])
        buyer = c2.selectbox("Bought by", teams_list, index=teams_list.index(s["team"]), key="sale_buyer")
        base = float(pool.set_index("player").loc[player]["base_price_cr"])
        price = c3.number_input("Final price (cr)", 0.0, 100.0, base, 0.05, key=f"sale_price_{player}")
        errors, warns = E.check_sale(player, buyer, price, ctx)
        for e in errors:
            alert("bad", e)
        for w in warns:
            alert("warn", w)
        if st.button("Save sale", type="primary", disabled=bool(errors)):
            try:
                db.add_sale(player, buyer, price)
                st.rerun()
            except Exception as ex:
                st.error(f"Could not save: {ex}")
    sales = st.session_state.sales
    st.markdown(f"**Sales so far: {len(sales)}**")
    if sales:
        df = pd.DataFrame(sales)[["player", "buyer", "price"]]
        df.columns = ["Player", "Bought by", "Price (cr)"]
        st.dataframe(df.iloc[::-1], width="stretch", hide_index=True)
        b1, b2, b3 = st.columns([1, 1, 2])
        if b1.button("Undo last sale"):
            db.undo_sale()
            st.rerun()
        b2.download_button("Download CSV", df.to_csv(index=False), "sales.csv", "text/csv")
        with b3.expander("Start over (delete all sales)"):
            if st.checkbox("I am sure"):
                if st.button("Delete all sales"):
                    db.clear_sales()
                    st.rerun()
    st.caption("After every sale, all advice and numbers update.")


def tab_team(ctx):
    s, m = ctx["setup"], ctx["mine"]
    c1, c2 = st.columns(2)
    with c1:
        body = ""
        for r in ROLES:
            have, want = m["have"][r], s["target"][r]
            pct = min(have / want * 100, 100) if want else 100
            body += (f"<div class='kv'><span>{r}</span><b>{have} of {want}</b></div>"
                     f"<div class='bar'><div style='width:{pct}%'></div></div>")
        card("Role gaps (have vs want)", body)
        body = kv([("Squad", f"{m['count']} of {s['squad_max']} (min {s['squad_min']})"),
                   ("Overseas", f"{s['overseas_max'] - m['overseas_slots']} of {s['overseas_max']}"),
                   ("Last season", f"Position {ctx['position']} · {ctx['wins']}W {ctx['losses']}L")])
        card("Squad status", body)
        if m["count"] > s["squad_max"]:
            alert("bad", "Squad is over the maximum.")
        if m["overseas_slots"] < 0:
            alert("bad", "Too many overseas players.")
        if m["count"] < s["squad_min"]:
            alert("warn", f"You still need {s['squad_min'] - m['count']} players to reach the minimum.")
    with c2:
        body = ""
        for r in ROLES:
            pl = ctx["plan"][r]
            pct = min(max(pl["spent"] / pl["planned"] * 100, 0), 100) if pl["planned"] else 0
            over = " over" if pl["left"] < 0 else ""
            body += (f"<div class='kv'><span>{r}</span><b>{fmt(pl['spent'])} of {fmt(pl['planned'])} cr</b></div>"
                     f"<div class='bar{over}'><div style='width:{pct}%'></div></div>")
        card("Plan progress (spent vs planned)", body)
    st.markdown("**My squad**")
    if m["squad"]:
        df = pd.DataFrame(m["squad"])
        df.columns = ["Player", "Role", "Nationality", "Price (cr)", "How"]
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.caption("No players yet.")


def tab_recs(ctx, recs):
    st.markdown("#### Best players for you right now")
    roles_needed = [f"{r} ({s})" for r, s in
                    [(r, ctx["setup"]["target"][r] - ctx["mine"]["have"][r]) for r in ROLES] if s > 0]
    st.caption("Roles you still need: " + (", ".join(roles_needed) if roles_needed else "none"))
    show_skip = st.toggle("Show 'Skip' players too", value=False)
    df = recs if show_skip else recs[recs["Advice"] == "Bid"]
    st.dataframe(df, width="stretch", hide_index=True, height=520,
                 column_config={"Why": st.column_config.TextColumn(width="large")})


def tab_rivals(ctx):
    s = ctx["setup"]
    rows = []
    for t in ctx["teams"]["team"]:
        stt = ctx["mine"] if t == s["team"] else ctx["rivals"][t]
        gaps = sorted(((s["target"][r] - stt["have"][r], r) for r in ROLES), reverse=True)
        likely = ", ".join(r for g, r in gaps[:2] if g > 0) or "none"
        trow = ctx["teams"][ctx["teams"]["team"] == t].iloc[0]
        rows.append({"Team": t + (" (you)" if t == s["team"] else ""), "Money left (cr)": stt["purse"],
                     "Spots left": stt["slots"], "Overseas left": stt["overseas_slots"],
                     "Last season": f"#{int(trow['last_position'])} · {int(trow['last_wins'])}W {int(trow['last_losses'])}L",
                     "Likely to chase": likely})
    df = pd.DataFrame(rows)
    st.markdown("#### All teams")
    st.dataframe(df, width="stretch", hide_index=True)
    st.bar_chart(df.set_index("Team")["Money left (cr)"], color="#4F2FE0")
    st.caption("'Likely to chase' is a guess from each team's biggest role gaps.")
    st.markdown("**Players bought so far, by team**")
    sales = ctx["sales"]
    if not sales:
        st.caption("No sales yet.")
    for t in ctx["teams"]["team"]:
        mine = [x for x in sales if x["buyer"] == t]
        if mine:
            with st.expander(f"{t} ({len(mine)})"):
                for x in mine:
                    st.write(f"{x['player']}: {fmt(x['price'])} cr")


def tab_players(ctx):
    players, sales = ctx["players"], ctx["sales"]
    sold = {x["player"]: x["buyer"] for x in sales}
    df = players.copy()
    df["Status"] = df["player"].map(lambda n: f"Sold to {sold[n]}" if n in sold else "Unsold")
    df["Fair price (cr)"] = (ctx["slope"] * df["score"] + ctx["intercept"]).clip(lower=df["base_price_cr"]).round(2)
    df["Last year vs fair"] = (df["last_year_price_cr"] - df["Fair price (cr)"]).map(
        lambda d: "Was overpaid" if d > 0.5 else ("Was a bargain" if d < -0.5 else "About right"))
    c1, c2, c3 = st.columns(3)
    role = c1.multiselect("Role", ROLES)
    nat = c2.multiselect("Nationality", ["Indian", "Overseas"])
    status = c3.selectbox("Status", ["All", "Unsold", "Sold"])
    if role:
        df = df[df["role"].isin(role)]
    if nat:
        df = df[df["nationality"].isin(nat)]
    if status == "Unsold":
        df = df[df["Status"] == "Unsold"]
    elif status == "Sold":
        df = df[df["Status"] != "Unsold"]
    show = df[["player", "role", "nationality", "age", "score", "base_price_cr", "Fair price (cr)",
               "last_year_price_cr", "Last year vs fair", "Status"]]
    show.columns = ["Player", "Role", "Nationality", "Age", "Score", "Starting (cr)", "Fair (cr)",
                    "Last year (cr)", "Last year vs fair", "Status"]
    st.dataframe(show, width="stretch", hide_index=True, height=360)
    st.markdown("**Compare two players**")
    names = list(players["player"])
    a, b = st.columns(2)
    n1 = a.selectbox("Player 1", names, index=0, key="cmp1")
    n2 = b.selectbox("Player 2", names, index=min(1, len(names) - 1), key="cmp2")
    cmp = players.set_index("player").loc[[n1, n2]].T
    cmp = cmp.loc[["role", "nationality", "age", "score", "base_price_cr", "last_year_price_cr",
                   "runs", "strike_rate", "wickets", "economy"]]
    cmp.index = ["Role", "Nationality", "Age", "Score", "Starting price (cr)", "Last year price (cr)",
                 "Runs", "Strike rate", "Wickets", "Economy"]
    st.dataframe(cmp.astype(str), width="stretch")


def tab_chat(ctx):
    st.markdown("#### Ask about unsold players")
    st.caption("Answers come only from the player table. Example: best Indian fast bowlers under 2 crore")
    hist = st.session_state.setdefault("chat", [])
    for role_, text in hist:
        with st.chat_message(role_):
            st.text(text)
    q = st.chat_input("Ask a question")
    if q:
        hist.append(("user", q))
        hist.append(("assistant", E.answer_question(q, ctx["pool"])))
        st.rerun()


# =====================================================================
# MAIN
# =====================================================================
def main():
    if "user_id" not in st.session_state:
        login_screen()
        return
    if "setup" not in st.session_state:
        try:
            db.load_all()
        except Exception as ex:
            st.error(f"Could not load your data: {ex}")
            if st.button("Log out"):
                db.sign_out()
                st.rerun()
            return
    players, teams = load_data()

    with st.sidebar:
        st.markdown("**IPL Auction Assistant**")
        st.caption(st.session_state.get("email", ""))
        if st.button("Log out", width="stretch"):
            db.sign_out()
            st.rerun()

    banner()
    setup = st.session_state.setup
    if not setup:
        setup_screen(players, teams, None)
        return

    ctx = E.make_context(setup, players, teams, st.session_state.sales)
    recs = E.recommendations(ctx)
    top_bar(ctx)

    tabs = st.tabs(["Bid check", "Record sale", "My team", "Recommendations", "All teams",
                    "Players", "Chat", "Plan"])
    with tabs[0]:
        tab_bid(ctx, recs)
    with tabs[1]:
        tab_sale(ctx)
    with tabs[2]:
        tab_team(ctx)
    with tabs[3]:
        tab_recs(ctx, recs)
    with tabs[4]:
        tab_rivals(ctx)
    with tabs[5]:
        tab_players(ctx)
    with tabs[6]:
        tab_chat(ctx)
    with tabs[7]:
        setup_screen(players, teams, setup)


main()
