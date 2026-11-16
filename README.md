# CricketIQ - IPL Auction Assistant

## What is inside
- `index.html` - the app (your design, real data inside)
- `data/data.json` - player and team data the app uses
- `data/players_pool.csv`, `data/teams_2026.csv` - same data, easy to read
- `netlify/functions/hootie.js` - Hootie's brain (Gemini). Keeps the key secret
- `netlify.toml` - Netlify settings
- `CricketIQ_Colab.ipynb` - the ML analysis (run once in Google Colab)

## Put it online (free)
1. Get a Gemini key: aistudio.google.com/app/apikey > Create API key. Copy it.
2. On GitHub, make a new repo. Upload everything in this folder (keep the folders).
3. On netlify.com, sign up free > Add new site > Import from Git > pick the repo > Deploy.
4. In Netlify: Site configuration > Environment variables > Add `GEMINI_API_KEY` = your key.
5. Deploys > Trigger deploy > Deploy site. Done. Open the link.

Without the key the app still works. Hootie then answers with built-in rules.

## Refresh for a new auction
1. Open `CricketIQ_Colab.ipynb` in Google Colab. Upload the new data files. Run all.
2. Download `players_pool.csv` and `teams_2026.csv`.
3. Ask Claude to rebuild `data.json` from them.

## Known limits (say these in class)
- Fair price comes from a model. Test on 2025: average miss 2.1 cr. A simple guess missed 3.1 cr.
- Recent form counts a lot. Example: Bumrah had a bad 2026, so his price is low.
- Age is known for about 1 in 3 players. Nationality unknown means shown as Indian.
- Base price is the 2025 one. For others it is an estimate (marked in the app).
- Rival squads are not known before an auction. Type their money and spots in Setup.
